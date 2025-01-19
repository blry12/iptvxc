############################################################################
#						\ Fire TV Guru /								   #
############################################################################

#############################=IMPORTS=######################################
	#Kodi Specific
import xbmc,xbmcvfs,xbmcaddon,xbmcgui,xbmcplugin, time, calendar
	#Python Specific
import base64,os,re,time,sys,urllib.request
import urllib.parse,urllib.error,json,shutil
from urllib.parse import urlparse, parse_qs
import sqlite3
import threading
import xml.etree.ElementTree as ET

from datetime import datetime, timezone, timedelta

from concurrent.futures import ThreadPoolExecutor
	#Addon Specific
from resources.modules import control,tools, variables

XMLTV_URL = variables.XMLTV_URL
DB_PATH = variables.DB_PATH
ADDONDATA = variables.ADDONDATA

class EPGUpdater:
	def __init__(self):
		self.db_path = DB_PATH
		self.xmltv_url = XMLTV_URL

	def setup_database(self):
		""" Setup the database with the epg table """
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()
		cursor.execute('''CREATE TABLE IF NOT EXISTS epg (
							channel_id TEXT,
							title TEXT,
							start_time DATETIME,
							end_time DATETIME,
							description TEXT)''')
		conn.commit()
		conn.close()

	def is_db_empty(self):
		""" Check if the database is empty. """
		try:
			conn = sqlite3.connect(self.db_path)
			cursor = conn.cursor()
			cursor.execute("SELECT COUNT(*) FROM epg")
			count = cursor.fetchone()[0]
			conn.close()
			return count == 0
		except Exception as e:
			tools.log(f"Error checking DB: {e}")
			return True

	def download_and_parse_xmltv(self):
		self.setup_database()
		""" Download and parse XMLTV data """
		try:
			tools.log("Fetching XMLTV data...")
			response = tools.OPEN_URL(self.xmltv_url)
			if response is None:
				raise Exception("Failed to fetch XMLTV data.")
			
			with open(os.path.join(ADDONDATA, "xmltv.xml"), "w", encoding="utf-8") as f:
				f.write(response)
			
			tools.log("Parsing and saving XMLTV data...")
			self.parse_and_save_xmltv(os.path.join(ADDONDATA, "xmltv.xml"))
		except Exception as e:
			tools.log(f"Failed to fetch XMLTV: {e}")

	def parse_and_save_xmltv(self, xmltv_file):
		""" Parse and save XMLTV data to the database """
		conn = sqlite3.connect(self.db_path)
		cursor = conn.cursor()

		tree = ET.parse(xmltv_file)
		root = tree.getroot()

		cursor.execute("DELETE FROM epg")

		for programme in root.findall("programme"):
			channel_id = programme.get("channel")
			start_time = self.parse_xmltv_time(programme.get("start"))
			end_time = self.parse_xmltv_time(programme.get("stop"))
			title = programme.find("title").text if programme.find("title") is not None else "No Title"
			description = programme.find("desc").text if programme.find("desc") is not None else "No Description"

			cursor.execute(""" 
				INSERT INTO epg (channel_id, start_time, end_time, title, description) 
				VALUES (?, ?, ?, ?, ?) 
			""", (channel_id, start_time, end_time, title, description))
		
		conn.commit()
		conn.close()

	def parse_xmltv_time1(self, time_str):
		""" Convert the XMLTV time format to Unix timestamp """
		try:
			return int(datetime.strptime(time_str, "%Y%m%d%H%M%S %z").timestamp())
		except ValueError:
			tools.log(f"Invalid time format: {time_str}")
			return None



	def parse_xmltv_time(self, time_str):
		"""Convert the XMLTV time format to a Unix timestamp, handling timezones."""
		try:
			time_str_parts = time_str.split(" ")
			if len(time_str_parts) != 2:
				raise ValueError(f"Invalid time format (missing timezone): {time_str}")
			
			time_without_tz = time_str_parts[0]
			timezone_str = time_str_parts[1]

			if len(timezone_str) != 5 or (timezone_str[0] not in ['+', '-']):
				raise ValueError(f"Invalid timezone format: {timezone_str}")

			tz_sign = 1 if timezone_str[0] == '+' else -1
			tz_hours = int(timezone_str[1:3])
			tz_minutes = int(timezone_str[3:5])
			tz_offset = tz_sign * (tz_hours * 60 + tz_minutes)

			tz_info = timezone(timedelta(minutes=tz_offset))
			dt = datetime.strptime(time_without_tz, "%Y%m%d%H%M%S")
			dt_with_tz = dt.replace(tzinfo=tz_info)
			dt_utc = dt_with_tz.astimezone(timezone.utc)
			return int(dt_utc.timestamp())
		
		except ValueError as e:
			print(f"Error parsing time: {time_str}, exception: {str(e)}")
			return None



	def fetch_and_cache_xmltv(self):
		""" Check if the XMLTV file is outdated or if the DB is empty, then fetch data """
		xmltv_file = os.path.join(ADDONDATA, "xmltv.xml")
		db_file = self.db_path
		
		if os.path.exists(xmltv_file):
			if self.is_db_empty():
				tools.log("XMLTV file is outdated or DB is empty. Fetching new data.")
				self.download_and_parse_xmltv()
			else:
				tools.log("Using cached XMLTV data.")
				self.parse_and_save_xmltv(xmltv_file)
		else:
			tools.log("XMLTV file does not exist. Fetching new data.")
			self.download_and_parse_xmltv()

	def update_xmltv_in_background(self):
		if os.path.exists(xmltv_file):
			if file_age > (1 * 24 * 60 * 60):
				tools.log("XMLTV file is outdated. Fetching new data.")
				self.download_and_parse_xmltv()
		else:
			tools.log("XMLTV file does not exist. Fetching new data.")
			self.download_and_parse_xmltv()


	def manual_update(self):
		self.setup_database()
		""" Manually update the EPG data with progress dialog """
		dialog = xbmcgui.DialogProgress()
		dialog.create("EPG Update", "Initializing update...")

		try:
			tools.log("Starting manual EPG update...")

			dialog.update(0, "Downloading EPG data...")
			url = self.xmltv_url
			req = urllib.request.Request(url)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0')

			with urllib.request.urlopen(req) as response:
				content_length = response.getheader('Content-Length')
				if content_length:
					total_size = int(content_length)
				else:
					total_size = 50000000  # 50mb guess just for progress movement

				downloaded = 0
				chunk_size = 1024  
				xmltv_file = os.path.join(ADDONDATA, "xmltv.xml")

				with open(xmltv_file, "wb") as f:
					while True:
						chunk = response.read(chunk_size)
						if not chunk:
							break
						f.write(chunk)
						downloaded += len(chunk)
						percent = int((downloaded / total_size) * 100)
						dialog.update(percent, f"Downloading EPG data...\nThis can take a while for large channel lists\nDownloading... {percent}")
						if dialog.iscanceled():
							raise Exception("Download canceled by user.")

			tools.log("EPG data downloaded successfully.")
			dialog.update(50, "Parsing EPG data...")

			self.parse_and_save_xmltv(xmltv_file)

			tools.log("EPG data parsed and saved successfully.")
			dialog.update(100, "EPG Update Complete!")
			xbmcgui.Dialog().notification("EPG Update", "Update completed successfully!", xbmcgui.NOTIFICATION_INFO, 5000)

		except Exception as e:
			tools.log(f"Manual EPG update failed: {e}")
			xbmcgui.Dialog().notification("EPG Update Failed", str(e), xbmcgui.NOTIFICATION_ERROR, 5000)
		finally:
			dialog.close()




	def silent_update(self):
		self.setup_database()
		xmltv_file = os.path.join(variables.ADDONDATA, "xmltv.xml")
		file_modified_time = os.path.getmtime(xmltv_file)
		file_age = time.time() - file_modified_time
		def update_in_background():
			try:
				tools.log("Starting silent EPG update in the background...")
				if os.path.exists(xmltv_file):
					if file_age > (1 * 24 * 60 * 60):
						tools.log("XMLTV file is outdated. Fetching new data.")
						self.download_and_parse_xmltv()
						tools.log("Silent EPG update completed.")
				else:
					tools.log("XMLTV file does not exist. Fetching new data.")
					self.download_and_parse_xmltv()
			except Exception as e:
				tools.log(f"Silent EPG update failed: {e}")
		threading.Thread(target=update_in_background, daemon=True).start()
EPGUpdater().setup_database()