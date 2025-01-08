############################################################################
#						\ Fire TV Guru /								   #
############################################################################

#############################=IMPORTS=######################################
	#Kodi Specific
import xbmc,xbmcvfs,xbmcaddon,xbmcgui,xbmcplugin
	#Python Specific
import base64,os,re,time,sys,urllib.request
import urllib.parse,urllib.error,json
from urllib.parse import urlparse, parse_qs
#parsed_url = urlparse(url)
	#Addon Specific
from resources.pyxbmct import addonwindow as pyxbmct
from resources.modules import control,tools, variables
from resources.caching import ini_cache
import threading
from threading import Thread
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

#############################################################################
adult_tags = ['xxx','xXx','XXX','adult','Adult','ADULT','adults','Adults','ADULTS','porn','Porn','PORN', '18+']

def entry():
	try:
		db_data = ini_cache.CacheManager().load_cat_data_from_db("vod_categories")

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
		data = tools.OPEN_URL(vod_cat)
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
		window = CategoryVODWindow("", categories=categories)
		window.doModal()
		del window


class CategoryVODWindow(pyxbmct.AddonFullWindow):
	xbmc.executebuiltin("Dialog.Close(busydialog)")

	def __init__(self, title="Categories & VOD Grid", categories=None):
		super().__init__(title)
		self.setGeometry(1280, 720, 20, 10)

		Background = pyxbmct.Image(tvguidebg)
		self.placeControl(Background, -3, -1, 25, 12)

		self.categories = categories or []
		self.vod_data = []

		self._create_controls()

		self._populate_categories()

		self.set_navigation()
		self.plot = None

	def _create_controls(self):
		title_name = pyxbmct.Label(ADDON_NAME)
		self.placeControl(title_name, -1, 4, 1, 5)
		
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

		self.full_scrn__button = pyxbmct.Button('Back to stream')
		self.placeControl(self.full_scrn__button, -1, 8, 1, 2)
		self.connect(self.full_scrn__button, self._go_back_to_stream)

		self.category_list = pyxbmct.List('font13', _itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.category_list, 0, 0, 14, 3)
		self.connect(self.category_list, self._on_category_selected)

		self.vod_section = pyxbmct.List(_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.vod_section, 0, 3, 14, 8)
		self.connect(self.vod_section, self._on_vod_selected)

		self.connectEventList(
			[pyxbmct.ACTION_MOVE_DOWN, pyxbmct.ACTION_MOVE_UP, pyxbmct.ACTION_MOUSE_MOVE],
			self._on_vod_highlighted
		)

		self.channel_icon_label = pyxbmct.Image('')
		self.placeControl(self.channel_icon_label, 12, 0, 8, 2)

		self.channel_description_label = pyxbmct.TextBox()
		self.placeControl(self.channel_description_label, 13, 2, 8, 8)
		self.channel_description_label.setText('')
		self.channel_description_label.autoScroll(1000, 1000, 1000)


		self.setFocus(self.category_list)

	def set_navigation(self):
		self.category_list.controlRight(self.vod_section)
		self.vod_section.controlLeft(self.category_list)
		self.vod_section.controlRight(self.full_scrn__button)
		self.full_scrn__button.controlDown(self.vod_section)
		self.full_scrn__button.controlLeft(self.category_list)

	def _populate_categories(self):
		self.category_list.reset()
		for category in self.categories:
			self.category_list.addItem(category['name'])
		self.setFocus(self.category_list)

	def _on_category_selected(self):
		selected_index = self.category_list.getSelectedPosition()
		if selected_index < 0:
			tools.log("No category selected.")
			xbmcgui.Dialog().notification('Error', 'No category selected.', xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		selected_category = self.categories[selected_index]
		category_id = selected_category.get('id')

		if not category_id:
			tools.log(f"Selected category is missing an ID: {selected_category}")
			xbmcgui.Dialog().notification('Error', f"Missing ID for {selected_category.get('name', 'Unknown')}", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		tools.log(f"Loading VOD data for category ID: {category_id}")
		self._load_vod_data(category_id)

	def _load_vod_data(self, category_id):
		self.vod_section.reset()
		self.vod_data = []

		def fetch_data(category_id):
			try:
				db_data = ini_cache.CacheManager().load_data_from_db("vod", category_id)

				if db_data:
					tools.log(f"Loaded VOD items from cache for category {category_id}.")
					for row in db_data:
						stream_id, name, stream_icon, category_id, container_extension, last_updated = row
						self.vod_data.append({
							'name': name,
							'poster': stream_icon or logo,
							'movie_url': f"{play_movies}{stream_id}.{container_extension or ''}"
						})
				else:
					tools.log("Cache is empty. Fetching VOD data from URL...")
					data = tools.OPEN_URL(f"{vod_streams}{category_id}")
					parsed_data = json.loads(data)
					for item in parsed_data:
						self.vod_data.append({
							'name': item['name'],
							'poster': item.get('stream_icon', logo),
							'movie_url': f"{play_movies}{item['stream_id']}.{item.get('container_extension', '')}"
						})
			except Exception as e:
				tools.log(f"Error loading VOD data: {e}")
			finally:
				self._create_vod_list()
				xbmc.executebuiltin("Dialog.Close(busydialog)")

		threading.Thread(target=fetch_data(category_id)).start()

	def _create_vod_list(self):
		self.vod_section.reset()
		for movie in self.vod_data:
			self.vod_section.addItem(movie['name'])
		xbmc.executebuiltin("Dialog.Close(busydialog)")
		self.setFocus(self.vod_section)

	def _on_vod_selected(self):
		selected_index = self.vod_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		selected_movie = self.vod_data[selected_index]
		self._update_movie_info(selected_movie)
		self._play_vod(selected_movie['movie_url'], selected_movie['name'], selected_movie['poster'])

	def _on_vod_highlighted(self):
		selected_index = self.vod_section.getSelectedPosition()
		if selected_index < 0:
			return

		selected_movie = self.vod_data[selected_index]
		self.channel_icon_label.setImage(selected_movie['poster'])
		self.channel_description_label.setText('Loading movie details...')

		def fetch_details():
			tmdb_movie = self._get_movie_details(selected_movie['name'])
			description = tmdb_movie.get('overview', 'No Description Available')
			self.plot = description
			length = tmdb_movie.get('runtime', 'N/A')
			rating = tmdb_movie.get('vote_average', 'N/A')
			date = tmdb_movie.get('release_date', 'N/A')

			movie_info = f"Plot: {description}\n\nLength: {length} mins\nRating: {rating}/10\nRelease Date: {date}"
			self.channel_description_label.setText(movie_info)

		Thread(target=fetch_details).start()

	def _update_movie_info(self, movie):
		tools.log(f"Fetching info for movie: {movie['name']}")

		tmdb_movie = self._get_movie_details(movie['name'])

		description = tmdb_movie.get('overview', 'No Description Available')
		plot = description 
		length = tmdb_movie.get('runtime', 'N/A')
		rating = tmdb_movie.get('vote_average', 'N/A')
		date = tmdb_movie.get('release_date', 'N/A')
		self.plot=plot

		movie_info = f"Plot: {plot}\n\nLength: {length} mins\nRating: {rating}/10\nRelease Date: {date}"

		self.channel_description_label.setText(movie_info)
		self.channel_icon_label.setImage(movie['poster'])

	def _get_movie_details(self, movie_name):
		api_key = '6ca3392e2903d0ddafc2dae3044ee31f'
		base_url = 'https://api.themoviedb.org/3'
		cleaned_movie_name = re.sub(r"[\s\-]\(?\d{4}\)?$", "", movie_name).strip()

		if not hasattr(self, 'movie_cache'):
			self.movie_cache = {}

		if cleaned_movie_name in self.movie_cache:
			return self.movie_cache[cleaned_movie_name]

		try:
			search_url = f"{base_url}/search/movie?api_key={api_key}&query={cleaned_movie_name.replace(' ', '+')}&language=en-US"
			response = tools.OPEN_URL(search_url)
			search_results = json.loads(response)

			if search_results['results']:
				movie_id = search_results['results'][0]['id']
				details_url = f"{base_url}/movie/{movie_id}?api_key={api_key}&language=en-US"

				details_response = tools.OPEN_URL(details_url)
				movie_details = json.loads(details_response)
				self.movie_cache[cleaned_movie_name] = movie_details
				return movie_details

		except Exception as e:
			tools.log(f"Error fetching TMDB details for {movie_name}: {e}")
		return {}

	def _play_vod(self, url, name, thumb, plot=''):
		liz = xbmcgui.ListItem(name)
		liz.setArt({"thumb": thumb})
		liz.setProperty('IsPlayable', 'true')
		liz.setInfo('video', {'Plot': self.plot})
		liz.setPath(url)
		xbmc.Player().play(url, liz, False)

	def _go_back_to_stream(self):
		player = xbmc.Player()
		if player.isPlaying():
			xbmc.executebuiltin("ActivateWindow(12005)")
		else:
			xbmcgui.Dialog().notification("No VOD", "No VOD is currently playing.", xbmcgui.NOTIFICATION_INFO, 5000)
