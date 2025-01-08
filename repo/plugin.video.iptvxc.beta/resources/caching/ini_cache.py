import sqlite3
import time
import json
import os, xbmcaddon, xbmcvfs, xbmcgui
from datetime import datetime, timedelta
from resources.modules import control,tools, variables
ADDON = xbmcaddon.Addon()
ADDONPATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ID = ADDON.getAddonInfo('id')
HOME			  = xbmcvfs.translatePath('special://home/')
ADDONS			  = os.path.join(HOME,	   'addons')
USERDATA		  = os.path.join(HOME,	   'userdata')
PLUGIN			  = os.path.join(ADDONS,   ADDON_ID)
PACKAGES		  = os.path.join(ADDONS,   'packages')
ADDONDATA		  = os.path.join(USERDATA, 'addon_data', ADDON_ID)
#########################=XC VARIABLES=#####################################
dns				  = variables.dns			
username		  = variables.username		
password		  = variables.password		

panel_api		  = variables.panel_api		
player_api		  = variables.player_api	

play_url		  = variables.play_url		
play_live		  = variables.play_live		
play_movies		  = variables.play_movies	
play_series		  = variables.play_series	

live_all		  = variables.live_all		
live_cat		  = variables.live_cat		
live_streams	  = variables.live_streams	
live_short_epg	  = variables.live_short_epg

vod_all			  = variables.vod_all		
vod_cat			  = variables.vod_cat		
vod_streams		  = variables.vod_streams	
vod_info		  = variables.vod_info		

series_all		  = variables.series_all	
series_cat		  = variables.series_cat	
series_list		  = variables.series_list	
series_season	  = variables.series_season	

#############################################################################
DB_PATH1 = os.path.join(ADDONDATA, "media_cache.db")
UPDATE_INTERVAL = 48 * 60 * 60	# 48 hours
if not os.path.exists(ADDONDATA):
	os.makedirs(ADDONDATA)
class CacheManager:
	def __init__(self):
		self.setup_database()

	def setup_database(self):
		"""Setup the database for caching Live TV, VOD, and TV Series."""
		conn = sqlite3.connect(DB_PATH1)
		cursor = conn.cursor()

		cursor.execute('''CREATE TABLE IF NOT EXISTS live_tv_categories (
							category_id TEXT PRIMARY KEY,
							category_name TEXT,
							last_updated DATETIME)''')
		cursor.execute('''CREATE TABLE IF NOT EXISTS vod_categories (
							category_id TEXT PRIMARY KEY,
							category_name TEXT,
							last_updated DATETIME)''')
		cursor.execute('''CREATE TABLE IF NOT EXISTS tv_series_categories (
							category_id TEXT PRIMARY KEY,
							category_name TEXT,
							last_updated DATETIME)''')

		cursor.execute('''CREATE TABLE IF NOT EXISTS live_tv (
							stream_id TEXT PRIMARY KEY,
							epg_channel_id TEXT,
							name TEXT,
							stream_icon TEXT,
							category_id TEXT,
							last_updated DATETIME)''')

		cursor.execute('''CREATE TABLE IF NOT EXISTS vod (
							stream_id TEXT PRIMARY KEY,
							name TEXT,
							stream_icon TEXT,
							category_id TEXT,
							container_extension TEXT,
							last_updated DATETIME)''')

		cursor.execute('''CREATE TABLE IF NOT EXISTS tv_series (
							series_id TEXT PRIMARY KEY,
							name TEXT,
							cover TEXT,
							category_id TEXT,
							last_updated DATETIME)''')

		conn.commit()
		conn.close()

	def fetch_and_cache_data(self, url, table_name, columns, category_id=None):
		"""
		Generalized method to fetch and cache data for a given category.
		:param url: The API URL to fetch data from.
		:param table_name: The table to store the data.
		:param columns: The columns to insert data into.
		:param category_id: The category ID to filter data (if applicable).
		"""
		conn = sqlite3.connect(DB_PATH1)
		cursor = conn.cursor()
	
		# Check if the data exists and if it needs to be updated
		cursor.execute(f"SELECT last_updated FROM {table_name} WHERE category_id=?", (category_id,))
		result = cursor.fetchone()
	
		if result:
			try:
				last_updated = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
			except ValueError:
				last_updated = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
		else:
			last_updated = None

		if not result or (time.time() - time.mktime(last_updated.timetuple())) > UPDATE_INTERVAL:
			tools.log(f"Fetching new data for category_id {category_id} in {table_name}...")
			data = tools.OPEN_URL(url)
			parsed_data = json.loads(data)

			for item in parsed_data:
				values = [item.get(col, "Unknown") for col in columns]
				values.append(datetime.now())
				placeholders = ", ".join(["?"] * len(values))
	
				cursor.execute(f"""
					INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}, last_updated)
					VALUES ({placeholders})
				""", values)
			conn.commit()

		cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE category_id=?", (category_id,))
		total_items = cursor.fetchone()[0]
	
		conn.close()
		return total_items

	def fetch_all_and_cache(self):
		"""Fetch and cache all data for Live TV, VOD, and TV Series."""
		conn = sqlite3.connect(DB_PATH1)
		cursor = conn.cursor()

		live_categories = tools.OPEN_URL(live_cat)
		live_parsed = json.loads(live_categories)
		for item in live_parsed:
			category_id = item['category_id']
			category_name = item['category_name']

			cursor.execute("""
				INSERT OR REPLACE INTO live_tv_categories (category_id, category_name, last_updated)
				VALUES (?, ?, ?)
			""", (category_id, category_name, datetime.now()))

			self.fetch_and_cache_data(
				f"{live_streams}{category_id}",
				"live_tv",
				["stream_id", "epg_channel_id", "name", "stream_icon", "category_id"],
				category_id
			)

		vod_categories = tools.OPEN_URL(vod_cat)
		vod_parsed = json.loads(vod_categories)
		for item in vod_parsed:
			category_id = item['category_id']
			category_name = item['category_name']

			cursor.execute("""
				INSERT OR REPLACE INTO vod_categories (category_id, category_name, last_updated)
				VALUES (?, ?, ?)
			""", (category_id, category_name, datetime.now()))

			self.fetch_and_cache_data(
				f"{vod_streams}{category_id}",
				"vod",
				["stream_id", "name", "stream_icon", "category_id", "container_extension"],
				category_id
			)

		series_categories = tools.OPEN_URL(series_cat)
		series_parsed = json.loads(series_categories)
		for item in series_parsed:
			category_id = item['category_id']
			category_name = item['category_name']

			cursor.execute("""
				INSERT OR REPLACE INTO tv_series_categories (category_id, category_name, last_updated)
				VALUES (?, ?, ?)
			""", (category_id, category_name, datetime.now()))

			self.fetch_and_cache_data(
				f"{series_list}{category_id}",
				"tv_series",
				["series_id", "name", "cover", "category_id"],
				category_id
			)

		conn.commit()
		conn.close()

	def load_cat_data_from_db(self, table_name):
		conn = sqlite3.connect(DB_PATH1)
		cursor = conn.cursor()
		cursor.execute(f"SELECT category_id, category_name FROM {table_name}")
		data = cursor.fetchall()
		conn.close()
		return data

	def load_data_from_db(self, table_name, category_id):
		conn = sqlite3.connect(DB_PATH1)
		cursor = conn.cursor()
		cursor.execute(f"SELECT * FROM {table_name} WHERE category_id=?", (category_id,))
		data = cursor.fetchall()
		conn.close()
		return data

import threading


def silent_cache_update():
	"""
	Triggers the cache update silently in the background.
	"""
	def update_cache():
		try:
			tools.log("Starting silent cache update.")
			cache_manager = CacheManager()
			with sqlite3.connect(DB_PATH1) as conn:
				cursor = conn.cursor()

				cursor.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
				cursor.execute("SELECT value FROM metadata WHERE key='last_update'")
				result = cursor.fetchone()

				if result:
					last_update = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
					if (datetime.now() - last_update).total_seconds() <= 48 * 3600:
						tools.log("Cache is up-to-date; no update required.")
						return
				else:
					tools.log("No previous update timestamp found. Updating cache.")

			live_categories = tools.OPEN_URL(live_cat)
			live_parsed = json.loads(live_categories)
			for item in live_parsed:
				category_id = item['category_id']
				category_name = item['category_name']

				with sqlite3.connect(DB_PATH1) as conn:
					cursor = conn.cursor()
					cursor.execute("""
						INSERT OR REPLACE INTO live_tv_categories (category_id, category_name, last_updated)
						VALUES (?, ?, ?)
					""", (category_id, category_name, datetime.now()))

				cache_manager.fetch_and_cache_data(
					f"{live_streams}{category_id}",
					"live_tv",
					["stream_id", "epg_channel_id", "name", "stream_icon", "category_id"],
					category_id
				)

			vod_categories = tools.OPEN_URL(vod_cat)
			vod_parsed = json.loads(vod_categories)
			for item in vod_parsed:
				category_id = item['category_id']
				category_name = item['category_name']

				with sqlite3.connect(DB_PATH1) as conn:
					cursor = conn.cursor()
					cursor.execute("""
						INSERT OR REPLACE INTO vod_categories (category_id, category_name, last_updated)
						VALUES (?, ?, ?)
					""", (category_id, category_name, datetime.now()))

				cache_manager.fetch_and_cache_data(
					f"{vod_streams}{category_id}",
					"vod",
					["stream_id", "name", "stream_icon", "category_id", "container_extension"],
					category_id
				)

			series_categories = tools.OPEN_URL(series_cat)
			series_parsed = json.loads(series_categories)
			for item in series_parsed:
				category_id = item['category_id']
				category_name = item['category_name']

				with sqlite3.connect(DB_PATH1) as conn:
					cursor = conn.cursor()
					cursor.execute("""
						INSERT OR REPLACE INTO tv_series_categories (category_id, category_name, last_updated)
						VALUES (?, ?, ?)
					""", (category_id, category_name, datetime.now()))

				cache_manager.fetch_and_cache_data(
					f"{series_list}{category_id}",
					"tv_series",
					["series_id", "name", "cover", "category_id"],
					category_id
				)
				with sqlite3.connect(DB_PATH1) as conn:
					cursor = conn.cursor()
					cursor.execute("""
						INSERT OR REPLACE INTO metadata (key, value)
						VALUES ('last_update', ?)
					""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
			tools.log("Silent cache update completed successfully.")
		except Exception as e:
			tools.log(f"Cache update failed: {e}")

	threading.Thread(target=update_cache, daemon=True).start()


def start_silent_cache_update_in_background():
	""" Starts the silent cache update in a background thread """
	threading.Thread(target=silent_cache_update, daemon=True).start()



def manual_cache_update():
	"""
	Manually triggers the caching process with a Kodi progress dialog.
	Displays progress for Live TV, VOD, and TV Series caching with detailed debugging logs.
	"""
	dialog = xbmcgui.DialogProgress()
	dialog.create("Updating Cache", "Starting cache update...")

	try:
		tools.log("Starting manual cache update.")
		cache_manager = CacheManager()
		with sqlite3.connect(DB_PATH1) as conn:
			cursor = conn.cursor()

			cursor.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
			cursor.execute("SELECT value FROM metadata WHERE key='last_update'")
			result = cursor.fetchone()

			if result:
				last_update = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
				if (datetime.now() - last_update).total_seconds() <= 48 * 3600:
					tools.log("Cache is up-to-date; no update required.")
					return
			else:
				tools.log("No previous update timestamp found. Updating cache.")
		live_categories = tools.OPEN_URL(live_cat)
		live_parsed = json.loads(live_categories)
		tools.log(f"Parsed {len(live_parsed)} Live TV categories.")

		total_live, total_channels = 0, 0
		for i, item in enumerate(live_parsed):
			category_id = item['category_id']
			category_name = item['category_name']

			with sqlite3.connect(DB_PATH1) as conn:
				cursor = conn.cursor()
				cursor.execute("""
					INSERT OR REPLACE INTO live_tv_categories (category_id, category_name, last_updated)
					VALUES (?, ?, ?)
				""", (category_id, category_name, datetime.now()))

			cache_manager.fetch_and_cache_data(
				f"{live_streams}{category_id}",
				"live_tv",
				["stream_id", "epg_channel_id", "name", "stream_icon", "category_id"],
				category_id
			)

			total_live += 1
			total_channels += get_total_channels_in_category(category_id)
			percent = int((i + 1) / len(live_parsed) * 33)
			dialog.update(percent, f"Caching Live TV Categories... ({i + 1}/{len(live_parsed)})")
			if dialog.iscanceled():
				raise Exception("Cache update canceled by user.")

		vod_categories = tools.OPEN_URL(vod_cat)
		vod_parsed = json.loads(vod_categories)
		tools.log(f"Parsed {len(vod_parsed)} VOD categories.")

		total_vod, total_movies = 0, 0
		for i, item in enumerate(vod_parsed):
			category_id = item['category_id']
			category_name = item['category_name']

			with sqlite3.connect(DB_PATH1) as conn:
				cursor = conn.cursor()
				cursor.execute("""
					INSERT OR REPLACE INTO vod_categories (category_id, category_name, last_updated)
					VALUES (?, ?, ?)
				""", (category_id, category_name, datetime.now()))

			cache_manager.fetch_and_cache_data(
				f"{vod_streams}{category_id}",
				"vod",
				["stream_id", "name", "stream_icon", "category_id", "container_extension"],
				category_id
			)

			total_vod += 1
			total_movies += get_total_movies_in_category(category_id)
			percent = int(33 + (i + 1) / len(vod_parsed) * 33)
			dialog.update(percent, f"Caching VOD Categories... ({i + 1}/{len(vod_parsed)})")
			if dialog.iscanceled():
				raise Exception("Cache update canceled by user.")

		series_categories = tools.OPEN_URL(series_cat)
		series_parsed = json.loads(series_categories)
		tools.log(f"Parsed {len(series_parsed)} TV Series categories.")

		total_series, total_shows = 0, 0
		for i, item in enumerate(series_parsed):
			category_id = item['category_id']
			category_name = item['category_name']

			with sqlite3.connect(DB_PATH1) as conn:
				cursor = conn.cursor()
				cursor.execute("""
					INSERT OR REPLACE INTO tv_series_categories (category_id, category_name, last_updated)
					VALUES (?, ?, ?)
				""", (category_id, category_name, datetime.now()))

			# Cache TV Series data
			cache_manager.fetch_and_cache_data(
				f"{series_list}{category_id}",
				"tv_series",
				["series_id", "name", "cover", "category_id"],
				category_id
			)

			total_series += 1
			total_shows += get_total_shows_in_category(category_id)
			percent = int(66 + (i + 1) / len(series_parsed) * 34)
			dialog.update(percent, f"Caching TV Series Categories... ({i + 1}/{len(series_parsed)})")
			if dialog.iscanceled():
				raise Exception("Cache update canceled by user.")
		with sqlite3.connect(DB_PATH1) as conn:
			cursor = conn.cursor()

			cursor.execute("""
				INSERT OR REPLACE INTO metadata (key, value)
				VALUES ('last_update', ?)
			""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
		dialog.update(100, "Cache Update Complete!")
		tools.log(f"Cache update completed successfully. "
				  f"Live TV: {total_live} categories, {total_channels} total channels\n"
				  f"VOD: {total_vod} categories, {total_movies} total movies\n"
				  f"TV Series: {total_series} categories, {total_shows} total TV shows.")

		xbmcgui.Dialog().ok(
			"Cache Update Complete",
			f"Live TV items: {total_live} categories - {total_channels} total channels\n"
			f"VOD items: {total_vod} categories - {total_movies} total movies\n"
			f"TV Series items: {total_series} categories - {total_shows} total TV shows"
		)

	except Exception as e:
		tools.log(f"Cache update failed: {e}")
		xbmcgui.Dialog().notification("Cache Update Failed", str(e), xbmcgui.NOTIFICATION_ERROR, 5000)
	finally:
		dialog.close()


def get_total_channels_in_category(category_id):
	"""Get the total number of channels in the specified category from the database."""
	conn = sqlite3.connect(DB_PATH1)
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM live_tv WHERE category_id=?", (category_id,))
	total_channels = cursor.fetchone()[0]
	conn.close()
	return total_channels


def get_total_movies_in_category(category_id):
	"""Get the total number of movies in the specified category from the database."""
	conn = sqlite3.connect(DB_PATH1)
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM vod WHERE category_id=?", (category_id,))
	total_movies = cursor.fetchone()[0]
	conn.close()
	return total_movies


def get_total_shows_in_category(category_id):
	"""Get the total number of shows in the specified category from the database."""
	conn = sqlite3.connect(DB_PATH1)
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM tv_series WHERE category_id=?", (category_id,))
	total_shows = cursor.fetchone()[0]
	conn.close()
	return total_shows
