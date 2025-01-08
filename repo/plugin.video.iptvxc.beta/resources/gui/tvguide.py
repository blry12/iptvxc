############################################################################
#						\ Fire TV Guru /								   #
############################################################################

#############################=IMPORTS=######################################
	#Kodi Specific
import xbmc,xbmcvfs,xbmcaddon,xbmcgui,xbmcplugin
	#Python Specific
import base64,os,re,time,sys,urllib.request
import urllib.parse,urllib.error,json,shutil
from datetime import datetime,timedelta
from urllib.parse import urlparse, parse_qs
import sqlite3
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
	#Addon Specific
from resources.pyxbmct import addonwindow as pyxbmct
from resources.modules import control,tools, variables
from resources.caching import ini_cache
from concurrent.futures import ThreadPoolExecutor
##########################=VARIABLES=#######################################
ADDON = xbmcaddon.Addon()
ADDONPATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ID = ADDON.getAddonInfo('id')

DIALOG			  = xbmcgui.Dialog()
DP				  = xbmcgui.DialogProgress()
HOME			  = xbmcvfs.translatePath('special://home/')
ADDONS			  = os.path.join(HOME,	   'addons')
USERDATA		  = os.path.join(HOME,	   'userdata')
PLUGIN			  = os.path.join(ADDONS,   ADDON_ID)
PACKAGES		  = os.path.join(ADDONS,   'packages')
ADDONDATA		  = os.path.join(USERDATA, 'addon_data', ADDON_ID)
ADVANCED		  = os.path.join(USERDATA,	'advancedsettings.xml')
advanced_settings = os.path.join(PLUGIN,'resources', 'advanced_settings')
MEDIA			  = os.path.join(ADDONS,  PLUGIN , 'resources', 'media')
KODIV			  = float(xbmc.getInfoLabel("System.BuildVersion")[:4])
M3U_PATH		  = os.path.join(ADDONDATA,	 'm3u.m3u')
##########################=ART PATHS=#######################################
icon			  = os.path.join(PLUGIN,  'icon.png')
fanart			  = os.path.join(PLUGIN,  'fanart.jpg')
background		  = os.path.join(MEDIA,	  'background.jpg')
live			  = os.path.join(MEDIA,	  'live.jpg')
catch			  = os.path.join(MEDIA,	  'cu.jpg')
Moviesod		  = os.path.join(MEDIA,	  'movie.jpg')
Tvseries		  = os.path.join(MEDIA,	  'tv.jpg')
logo			  = os.path.join(MEDIA,	  'logo.png')
iconextras		  = os.path.join(MEDIA,	  'iconextras.png')
iconsettings	  = os.path.join(MEDIA,	  'iconsettings.png')
iconlive		  = os.path.join(MEDIA,	  'iconlive.png')
iconcatchup		  = os.path.join(MEDIA,	  'iconcatchup.png')
iconMoviesod	  = os.path.join(MEDIA,	  'iconmovies.png')
iconTvseries	  = os.path.join(MEDIA,	  'icontvseries.png')
iconsearch		  = os.path.join(MEDIA,	  'iconsearch.png')
iconaccount		  = os.path.join(MEDIA,	  'iconaccount.png')
icontvguide		  = os.path.join(MEDIA,	  'iconguide.png')
tvguidebg		  = os.path.join(MEDIA,	  'g_bg.png')

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

XMLTV_URL		  = variables.XMLTV_URL
#############################################################################
adult_tags = ['xxx','xXx','XXX','adult','Adult','ADULT','adults','Adults','ADULTS','porn','Porn','PORN', '18+']
DB_PATH = os.path.join(ADDONDATA, "epg_cache.db")

def entry():
	try:
		db_data = ini_cache.CacheManager().load_cat_data_from_db("live_tv_categories")

		categories = []
		if db_data:
			tools.log("Loaded categories from the database.")
			for row in db_data:
				category_id, category_name = row
				if xbmcaddon.Addon().getSetting('hidexxx') == 'false' or not any(tag in category_name for tag in adult_tags):
					categories.append({
						'id': category_id,
						'name': category_name
					})
		else:
			raise ValueError("No categories found in the database.")

	except Exception as e:
		tools.log(f"Failed to load categories from DB: {e}. Falling back to URL.")
		data = tools.OPEN_URL(live_cat)
		parsed_data = json.loads(data)
		categories = []
		for item in parsed_data:
			category_id = item['category_id']
			category_name = item['category_name']
			if xbmcaddon.Addon().getSetting('hidexxx') == 'false' or not any(tag in category_name for tag in adult_tags):
				categories.append({
					'id': category_id,
					'name': category_name
				})

	if categories:
		window = CategoryEPGWindow("", categories=categories)
		window.doModal()
		del window

class CategoryEPGWindow(pyxbmct.AddonFullWindow):
	xbmc.executebuiltin("Dialog.Close(busydialog)")

	def __init__(self, title="Categories & EPG Grid", categories=None):
		super().__init__(title)
		self.setGeometry(1280, 720, 20, 10)

		Background = pyxbmct.Image(tvguidebg)
		self.placeControl(Background, -3, -1, 25, 12)



		self.categories = categories or []
		self.epg_data = []

		self._create_controls()

		self._populate_categories()

		self.set_navigation()

	def _create_controls(self):

		title_name = pyxbmct.Label(ADDON_NAME)
		self.placeControl(title_name, -1, 4, 1,5)
		
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

		self.full_scrn__button = pyxbmct.Button('Back to stream')
		self.placeControl(self.full_scrn__button, -1, 8, 1, 2)
		self.connect(self.full_scrn__button, self._go_back_to_stream)

		self.category_list = pyxbmct.List('font13', _itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.category_list, 0, 0, 14, 3)
		self.connect(self.category_list, self._on_category_selected)

		self.epg_section = pyxbmct.List(_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=60, _space=10, _alignmentY=4,  _imageWidth=120, _imageHeight=90)
		self.placeControl(self.epg_section, 0, 3, 14, 7)
		self.connect(self.epg_section, self._on_channel_selected)

		self.connectEventList(
			[pyxbmct.ACTION_MOVE_DOWN, pyxbmct.ACTION_MOVE_UP, pyxbmct.ACTION_MOUSE_MOVE],
			self._on_channel_highlighted
		)

		self.chn = pyxbmct.TextBox()
		self.placeControl(self.chn, 13, 0, 2, 2)
		self.chn.setText('')
		
		self.channel_icon_label = pyxbmct.Image('')
		self.placeControl(self.channel_icon_label, 15, 0, 5, 2)
		
		self.channel_description_label = pyxbmct.TextBox()
		self.placeControl(self.channel_description_label, 13, 2, 3, 8)
		self.channel_description_label.setText('')
		self.channel_description_label.autoScroll(1000, 1000, 1000)


		self.channel_description_label2 = pyxbmct.TextBox()
		self.placeControl(self.channel_description_label2, 16, 2, 3, 8)
		self.channel_description_label2.setText('')
		self.channel_description_label2.autoScroll(1000, 1000, 1000)


	def set_navigation(self):
		self.category_list.controlRight(self.epg_section)

		self.epg_section.controlLeft(self.category_list)

		self.epg_section.controlRight(self.full_scrn__button)
		self.full_scrn__button.controlDown(self.epg_section)
		self.full_scrn__button.controlLeft(self.category_list)


	def _populate_categories(self):
		for category in self.categories:
			self.category_list.addItem(category['name'])
		self.setFocus(self.category_list)

	def _on_category_selected(self):
		tools.LogNotify('Loading', 'Loading category data...')

		selected_index = self.category_list.getSelectedPosition()
		if selected_index < 0:
			xbmcgui.Dialog().notification('Error', 'No category selected.', xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		selected_category = self.categories[selected_index]
		tools.log(f"Selected Category: {selected_category}")

		category_id = selected_category.get('id')
		if not category_id:
			xbmcgui.Dialog().notification('Error', f"Missing ID for {selected_category.get('name')}", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		tools.LogNotify('Loading', "Please wait.....")
		self._load_epg_data(category_id)


	def load_epg_for_channel_and_update(self, epg_channel_id, stream_id, name, stream_icon):
		epg_data_from_db = load_epg_for_channel(epg_channel_id)
		now_program, next_program = "No data", "No data"
		now_description, next_description = "No Description Available", "No Description Available"

		if epg_data_from_db:
			epg_data_from_db.sort(key=lambda x: x[2])
			current_time = int(time.time())
			for i, entry in enumerate(epg_data_from_db):
				start_time, end_time = entry[2], entry[3]

				if start_time <= current_time <= end_time:
					now_program = entry[1]
					now_description = entry[4]

					if i + 1 < len(epg_data_from_db):
						next_program = epg_data_from_db[i + 1][1]
						next_description = epg_data_from_db[i + 1][4]
					else:
						next_program, next_description = self.fetch_next_program(epg_channel_id, end_time)
					break
			else:
				tools.log("No program found matching the current time.")
		else:
			pass
		
		self.epg_data.append({
			'name': name,
			'icon': stream_icon,
			'now': now_program,
			'next': next_program,
			'now_description': now_description,
			'next_description': next_description,
			'stream_url': f"{play_live}{stream_id}"
		})

	def fetch_next_program(self, epg_channel_id, end_time):
		conn = sqlite3.connect(DB_PATH)
		cursor = conn.cursor()
		cursor.execute("""
			SELECT * FROM epg 
			WHERE channel_id = ? AND start_time > ? 
			ORDER BY start_time ASC LIMIT 1
		""", (epg_channel_id, end_time))
		next_program = cursor.fetchone()
		conn.close()

		if next_program:
			return next_program[1], next_program[4]
		else:
			return "No data", "No Description Available"

	def _load_epg_data(self, category_id): 
		self.epg_section.reset()

		db_data = ini_cache.CacheManager().load_data_from_db("live_tv", category_id)

		dialog = xbmcgui.DialogProgress()
		dialog.create("Loading EPG Data", "Fetching live TV channels...")

		if db_data:
			total_channels = len(db_data)
			tools.log(f"Using cached data for {total_channels} channels.")
			self.epg_data = []

			with ThreadPoolExecutor(max_workers=5) as executor:
				futures = []
				for i, item in enumerate(db_data):
					stream_id = item[0]
					epg_channel_id = item[1]
					name = item[2]
					stream_icon = item[3]

					futures.append(executor.submit(self.load_epg_for_channel_and_update, epg_channel_id, stream_id, name, stream_icon))

					percent = int((i + 1) / total_channels * 100)
					dialog.update(percent, f"Loading channel {i + 1}/{total_channels}...")

					if dialog.iscanceled():
						tools.log("Cache update canceled by user.")
						dialog.close()
						return

				for future in futures:
					future.result()

		else:
			dialog.update(0, "Fetching channels from URL...")
			data = tools.OPEN_URL(f"{live_streams}{category_id}")
			parsed_data = json.loads(data)

			self.epg_data = []
			total_channels = len(parsed_data)

			for i, item in enumerate(parsed_data):
				stream_id = item['stream_id']
				epg_channel_id = item['epg_channel_id']
				name = item['name']
				stream_icon = item.get('stream_icon', 'DefaultIcon.png')

				epg_data_from_db = load_epg_for_channel(epg_channel_id)

				epg_response = tools.OPEN_URL(f"{live_short_epg}{stream_id}")
				epg_listings = json.loads(epg_response).get("epg_listings", [])
				now_program = self._format_program(epg_listings[0]) if epg_listings else "No data"
				now_description = tools.b64(epg_listings[0]['description']) if epg_listings and 'description' in epg_listings[0] else "No Description Available"
				next_program = self._format_program(epg_listings[1]) if len(epg_listings) > 1 else "No data"
				next_description = tools.b64(epg_listings[1]['description']) if len(epg_listings) > 1 and 'description' in epg_listings[1] else "No Description Available"

				self.epg_data.append({
					'name': name,
					'icon': stream_icon,
					'now': now_program,
					'next': next_program,
					'now_description': now_description,
					'next_description': next_description,
					'stream_url': f"{play_live}{stream_id}"
				})

				percent = int((i + 1) / total_channels * 100)
				dialog.update(percent, f"Fetching data from URL... ({i + 1}/{total_channels})")
				if dialog.iscanceled():
					tools.log("Cache update canceled by user.")
					dialog.close()
					return

		dialog.update(100, "Cache update complete!")
		dialog.close()
		del dialog
		self._create_epg_list()
		xbmc.executebuiltin("Dialog.Close(busydialog)")

	def _create_epg_list(self):
		for channel in self.epg_data:
			channel_name = channel['name']
			now_program = channel['now']
			next_program = channel['next']
			channel_name2 = f"[COLOR 00FFFFFF]{channel['name']}[/COLOR]"
			epg_item = f"{channel_name} | Now: {now_program}\n"
			epg_item += f"{channel_name2} | Next: {next_program}"
			#self.epg_section.addItem(epg_item)
			
			# test
			list_item_text = (
				#f"[COLOR white][B]{channel_name}[/B][/COLOR]\n"
				f"[COLOR yellow]Now:[/COLOR] {now_program}\n"
				f"[COLOR lightblue]Next:[/COLOR] {next_program}"
			)
			list_item = xbmcgui.ListItem(label=list_item_text)
			list_item.setArt({"icon": channel['icon']})
			self.epg_section.addItem(list_item)
			
		self.setFocus(self.epg_section)

	def clean_description(self, description):
		if '¤' in description:
			return description.split('¤')[0].strip()
		return description.strip()

	def _update_channel_info(self, channel):
		_now = self.clean_description(channel['now_description'])
		_next = self.clean_description(channel['next_description'])
		self.channel_description_label.setText(f"[COLOR yellow]Now:[/COLOR] {_now}")
		self.channel_description_label2.setText(f"[COLOR lightblue]Next:[/COLOR] {_next}")
		self.channel_icon_label.setImage(channel['icon'])
		self.chn.setText(f"  [COLOR white][B]{channel['name']}[/B][/COLOR]")

	def _on_channel_highlighted(self):
		selected_index = self.epg_section.getSelectedPosition()
		if selected_index < 0:
			return

		selected_channel = self.epg_data[selected_index]
		self._update_channel_info(selected_channel)

	def _on_channel_selected(self):
		selected_index = self.epg_section.getSelectedPosition()
		if selected_index < 0:
			return
		selected_channel = self.epg_data[selected_index]
		self._update_channel_info(selected_channel)
		self._play_stream(selected_channel['stream_url'],selected_channel['now'], selected_channel['icon'], selected_channel['now_description'])

	def _format_program(self, program):
		try:
			start_time = datetime.fromtimestamp(int(program['start_timestamp'])).strftime('%H:%M')
			end_time = datetime.fromtimestamp(int(program['stop_timestamp'])).strftime('%H:%M')
			title = base64.b64decode(program['title']).decode('utf-8')
			return f"{start_time}-{end_time}: {title}"
		except (KeyError, ValueError, TypeError) as e:
			tools.log(f"Error formatting program: {e}")
			return "Invalid Program Data"


	def _go_back_to_stream(self):
		player = xbmc.Player()

		if player.isPlaying():
			xbmc.executebuiltin("ActivateWindow(12005)")
		else:
			xbmcgui.Dialog().notification("No Stream", "No stream is currently playing.", xbmcgui.NOTIFICATION_INFO, 5000) 
	
	def _close(self):
		xbmcgui.Dialog().notification('', 'closing')
		self.close()
		home()

	def _play_stream(self, url, name, thumb, plot):
		liz = xbmcgui.ListItem(name)
		liz.setPath(url)
		liz.setArt({"thumb": thumb})
		liz.setProperty('IsPlayable', 'true')
		liz.setInfo('video', {'Plot': plot})
		liz.setMimeType('application/x-mpegURL')
		liz.setProperty('inputstream', 'inputstream.ffmpegdirect')
		liz.setProperty('inputstream.ffmpegdirect.manifest_type', 'hls')
		liz.setProperty('inputstream.ffmpegdirect.is_realtime_stream', 'true')
		liz.setProperty('inputstream.ffmpegdirect.stream_mode', "timeshift")
		xbmc.Player().play(url, liz)

def load_epg_for_channel(channel_id, offset=0):
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.cursor()
	current_time = datetime.now() + timedelta(hours=offset)
	current_time = current_time.replace(microsecond=0)
	timestamp = int(current_time.timestamp())
	cursor.execute("SELECT * FROM epg WHERE channel_id=? AND start_time<=? AND end_time>=?", 
				   (channel_id, timestamp, timestamp))
	epg_data = cursor.fetchall()
	conn.close()
	return epg_data
