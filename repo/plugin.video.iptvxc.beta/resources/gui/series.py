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
		db_data = ini_cache.CacheManager().load_cat_data_from_db("tv_series_categories")

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
		data = tools.OPEN_URL(series_cat)
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
		window = CategoryTVWindow("", categories=categories)
		window.doModal()
		del window

class CategoryTVWindow(pyxbmct.AddonFullWindow):
	xbmc.executebuiltin("Dialog.Close(busydialog)")

	def __init__(self, title="Categories & TV Shows", categories=None):
		super().__init__(title)
		self.setGeometry(1280, 720, 20, 10)

		Background = pyxbmct.Image(tvguidebg)
		self.placeControl(Background, -3, -1, 25, 12)

		self.categories = categories or []
		self.tv_data = []
		self.selected_show = None
		self.selected_season = None
		self.focused_section = "categories"
		self._create_controls()
		self._populate_categories()
		self.set_navigation()
		self.tmdb_id = None
		self.thumb = None
		self.title = None
		self.plot = None

	def _create_controls(self):
		title_name = pyxbmct.Label(ADDON_NAME)
		self.placeControl(title_name, -1, 4, 1, 5)
		
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

		self.full_scrn__button = pyxbmct.Button('Back to stream')
		self.placeControl(self.full_scrn__button, -1, 8, 1, 2)
		self.connect(self.full_scrn__button, self._go_back_to_stream)

		self.category_list = pyxbmct.List('font13', _itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.category_list, 0, 0, 14, 2)
		self.connect(self.category_list, self._on_category_selected)

		self.tv_section = pyxbmct.List(_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.tv_section, 0, 2, 14, 3)
		self.connect(self.tv_section, self._on_show_selected)

		self.season_section = pyxbmct.List(_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.season_section, 0, 5, 14, 2)
		self.connect(self.season_section, self._on_season_selected)

		self.episode_section = pyxbmct.List(_itemTextXOffset=10, _itemTextYOffset=-3, _itemHeight=40, _space=10, _alignmentY=4)
		self.placeControl(self.episode_section, 0, 7, 14, 3)
		self.connect(self.episode_section, self._on_episode_selected)

		self.channel_icon_label = pyxbmct.Image('')
		self.placeControl(self.channel_icon_label, 12, 0, 8, 2)

		self.channel_description_label = pyxbmct.TextBox()
		self.placeControl(self.channel_description_label, 13, 2, 8, 8)
		self.channel_description_label.setText('')
		self.channel_description_label.autoScroll(1000, 1000, 1000)

		self.connectEventList(
			[pyxbmct.ACTION_MOVE_LEFT, pyxbmct.ACTION_MOVE_RIGHT, pyxbmct.ACTION_MOVE_UP, pyxbmct.ACTION_MOVE_DOWN],
			self._on_navigation
		)
		self.setFocus(self.category_list)

	def set_navigation(self):
		self.category_list.controlRight(self.tv_section)

		self.tv_section.controlLeft(self.category_list)
		self.tv_section.controlRight(self.season_section)

		self.season_section.controlRight(self.episode_section)
		self.season_section.controlLeft(self.tv_section)

		self.episode_section.controlRight(self.full_scrn__button)
		self.episode_section.controlLeft(self.season_section)

		self.full_scrn__button.controlDown(self.episode_section)
		self.full_scrn__button.controlLeft(self.category_list)


	def _on_navigation(self):
		focused_control = self.getFocus()

		if focused_control == self.tv_section:
			self.focused_section = "shows"
			self._on_show_highlighted()
		elif focused_control == self.season_section:
			self.focused_section = "seasons"
			self._on_season_highlighted()
		elif focused_control == self.episode_section:
			self.focused_section = "episodes"
			self._on_episode_highlighted()
		elif focused_control == self.category_list:
			self.focused_section = "categories"

	def _populate_categories(self):
		for category in self.categories:
			self.category_list.addItem(category['name'])
		self.setFocus(self.category_list)

	def _on_category_selected(self):
		self.season_section.reset()
		self.episode_section.reset()
		tools.LogNotify('Loading', 'Loading TV data...')

		selected_index = self.category_list.getSelectedPosition()
		if selected_index < 0:
			xbmcgui.Dialog().notification('Error', 'No category selected.', xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		selected_category = self.categories[selected_index]
		category_id = selected_category.get('id')
		if not category_id:
			xbmcgui.Dialog().notification('Error', f"Missing ID for {selected_category.get('name')}", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		tools.LogNotify('Loading', "Please wait.....")
		self._load_tv_data(category_id)

	def _load_tv_data(self, category_id):
		self.tv_section.reset()
		db_data = ini_cache.CacheManager().load_data_from_db("tv_series", category_id)

		self.tv_data = []

		if db_data:
			tools.log(f"Loaded TV Shows items from the cache.")
			for row in db_data:
				series_id, name, cover, category_id, last_updated = row
				poster = cover if cover else logo
				description = "No Description Available"
				
				self.tv_data.append({
					'name': name,
					'poster': poster,
					'description': description,
					'id': series_id,
				})
		else:
			tools.log("Cache is empty. Fetching VOD data from the URL...")
			data = tools.OPEN_URL(f"{series_list}{category_id}")
			parsed_data = json.loads(data)
		
			for item in parsed_data:
				show_id = item['series_id']
				name = item['name']
				poster = item.get('cover', logo)
				description = item.get('description', "No Description Available")
		
				self.tv_data.append({
					'name': name,
					'poster': poster,
					'description': description,
					'id': show_id,
				})
		
		self._create_tv_list()
		xbmc.executebuiltin("Dialog.Close(busydialog)")

	def _create_tv_list(self):
		for show in self.tv_data:
			show_name = show['name']
			self.tv_section.addItem(show_name)
		self.setFocus(self.tv_section)
		self._on_show_highlighted()

	def _on_show_selected(self):
		selected_index = self.tv_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		self.selected_show = self.tv_data[selected_index]
		self._update_show_info(self.selected_show)
		self._load_seasons(self.selected_show)
	
	def _load_seasons(self, show):
		self.episode_section.reset()
		self.season_section.reset()
		seasons_data = tools.OPEN_URL(f"{series_season}{show['id']}")
		tools.log(f"seasons url:  {series_season}{show['id']}")
		seasons_parsed = json.loads(seasons_data)
	
		self.seasons = seasons_parsed.get('seasons', [])
		for season in self.seasons:
			self.season_section.addItem(f"Season {season['season_number']}")
		self.setFocus(self.season_section)
		self._on_season_highlighted()
	
	def _on_season_selected(self):
		selected_index = self.season_section.getSelectedPosition()
		if selected_index < 0:
			return
		self.selected_season = self.seasons[selected_index]
		self._load_episodes(self.selected_show['id'], self.selected_season['season_number'])
	
	def _load_episodes(self, show_id, season_number):
		self.episode_section.reset()
		episodes_data = tools.OPEN_URL(f"{series_season}{show_id}&season_number={season_number}")
		episodes_parsed = json.loads(episodes_data)
		episodes_for_season = episodes_parsed.get('episodes', {}).get(str(season_number), [])
	
		self.episodes = []
		if isinstance(episodes_for_season, list):
			for episode in episodes_for_season:
				if isinstance(episode, dict):
					title = episode.get('title', f"Episode {episode.get('episode_num', 'Unknown')}")
					if not title.startswith(f"Season {season_number} | Episode"):
						title = f"Season {season_number} | Episode {episode.get('episode_num', 'Unknown')}"


					self.episode_section.addItem(title)
					self.episodes.append(episode)
			self.setFocus(self.episode_section)
			self._on_episode_highlighted()
		else:
			tools.log(f"Invalid episodes format for season {season_number}.")

	def _on_episode_selected(self):
		selected_index = self.episode_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		selected_episode = self.episodes[selected_index]
		self._play_episode(selected_episode, self.title, self.thumb, self.plot)

	def _update_show_info(self, show):
		tmdb_show = self._get_tv_show_details(show['name'])
		description = tmdb_show.get('overview', 'No Description Available')
		self.plot = description
		rating = tmdb_show.get('vote_average', 'N/A')
		date = tmdb_show.get('first_air_date', 'N/A')
		show_info = f"Plot: {description}\n\nRating: {rating}/10\nFirst Air Date: {date}"
		self.channel_description_label.setText(show_info)
		self.channel_icon_label.setImage(show['poster'])

	def _on_show_highlighted(self):
		selected_index = self.tv_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		self.selected_show = self.tv_data[selected_index]
		self.focused_section = "shows"
		self._update_show_info(self.selected_show)

	def _get_tv_show_details(self, show_name):
		show_data = self._get_tmdb_info(show_name)

		if show_data:
			return show_data
		else:
			tools.log(f"No TMDb results found for show: {show_name}")
			return {}

	def _update_season_info(self, selected_season):
		show_id = selected_season.get("show_id")
		season_number = selected_season.get("season_number", "Unknown")

		season_data = self._get_tmdb_info(show_id, season_number)

		if season_data:
			season_name = season_data.get("name", f"Season {season_number}")
			air_date = season_data.get("air_date", "N/A")
			episode_count = season_data.get("episodes", [])
			overview = season_data.get("overview", "No overview available.")
			cover = season_data.get("poster_path", "")
			background = season_data.get("backdrop_path", "")

			season_info = (
				f"Season: {season_name}\n"
				f"Episodes: {len(episode_count)}\n"
				f"Air Date: {air_date}\n\n"
				f"Plot: {overview}"
			)
			self.channel_description_label.setText(season_info)
			image_url = f"https://image.tmdb.org/t/p/w500{cover or background}"
			self.thumb = image_url
			self.channel_icon_label.setImage(image_url)
		else:
			self.channel_description_label.setText(f"Season {season_number} not found.")

	def _update_episode_info(self, selected_episode):
		episode_number = selected_episode.get('episode_num', 'Unknown')
		title = selected_episode.get('title', f"Episode {episode_number}")
		plot = selected_episode.get('info', {}).get('plot', 'No plot available.')
		release_date = selected_episode.get('info', {}).get('releaseDate', 'N/A')
		image = selected_episode.get('info', {}).get('movie_image', '')

		show_id = selected_episode.get('show_id')
		season_number = selected_episode.get('season_number')
		if show_id and season_number and episode_number:
			tools.log(f"Fetching episode data: Show ID={show_id}, Season={season_number}, Episode={episode_number}")
			episode_data = self._get_tmdb_info(show_id, season_number, episode_number)
			
			if episode_data:
				title = episode_data.get('name', title)
				plot = episode_data.get('overview', plot)
				self.plot= plot
				release_date = episode_data.get('air_date', release_date)
				image = f"https://image.tmdb.org/t/p/w500{episode_data.get('still_path', '')}" or image

		episode_info = (
			f"Episode: {title}\n"
			f"Air Date: {release_date}\n\n"
			f"Plot: {plot}"
		)
		self.channel_description_label.setText(episode_info)

		if image:
			self.channel_icon_label.setImage(image)
		else:
			self.channel_icon_label.clear()

	def _get_tmdb_info(self, show_name=None, season_number=None, episode_number=None):
		api_key = '6ca3392e2903d0ddafc2dae3044ee31f'
		base_url = 'https://api.themoviedb.org/3'

		if show_name:
			cleaned_show_name = re.sub(r"[\s\-]\(?\d{4}\)?$", "", str(show_name)).strip()
			_show_name = cleaned_show_name.replace(' ', '+')
			search_url = f"{base_url}/search/tv?api_key={api_key}&query={_show_name}&language=en-US"

			response = tools.OPEN_URL(search_url)
			search_results = json.loads(response)

			if search_results['results']:
				self.tmdb_id = search_results['results'][0]['id']
				tools.log(f"TMDb ID for {show_name}: {self.tmdb_id}")
			else:
				tools.log(f"No TMDb results found for show: {show_name}")
				return {}

		if self.tmdb_id and season_number and episode_number is None:
			season_url = f"{base_url}/tv/{self.tmdb_id}/season/{season_number}?api_key={api_key}&language=en-US"
			season_response = tools.OPEN_URL(season_url)
			season_data = json.loads(season_response)
			return season_data

		if self.tmdb_id and season_number and episode_number:
			episode_url = f"{base_url}/tv/{self.tmdb_id}/season/{season_number}/episode/{episode_number}?api_key={api_key}&language=en-US"
			episode_response = tools.OPEN_URL(episode_url)
			episode_data = json.loads(episode_response)
			tools.log(f"Episode data fetched for season {season_number}, episode {episode_number}")
			return episode_data

		if self.tmdb_id and not season_number and not episode_number:
			details_url = f"{base_url}/tv/{self.tmdb_id}?api_key={api_key}&language=en-US"
			details_response = tools.OPEN_URL(details_url)
			show_details = json.loads(details_response)
			tools.log(f"Show details fetched for TMDb ID {self.tmdb_id}")
			return show_details

		return {}

	def _on_season_highlighted(self):
		selected_index = self.season_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		self.selected_season = self.seasons[selected_index]
		self.focused_section = "seasons"
		self._update_season_info(self.selected_season)

	def _on_episode_highlighted(self):
		selected_index = self.episode_section.getSelectedPosition()
		if selected_index < 0:
			return
	
		selected_episode = self.episodes[selected_index]
		self.focused_section = "episodes"
		self._update_episode_info(selected_episode)

	def _play_episode(self, episode, name, thumb, plot):
		url = f"{dns}/series/{username}/{password}/{episode['id']}.{episode['container_extension']}"
		liz = xbmcgui.ListItem(episode['title'])
		liz.setPath(url)
		liz.setArt({"thumb": thumb})
		liz.setProperty('IsPlayable', 'true')
		liz.setInfo('video', {'Plot': plot})
		xbmc.Player().play(url, liz, False)

	def _go_back_to_stream(self):
		player = xbmc.Player()
		if player.isPlaying():
			xbmc.executebuiltin("ActivateWindow(12005)")
		else:
			xbmcgui.Dialog().notification("No VOD", "No VOD is currently playing.", xbmcgui.NOTIFICATION_INFO, 5000)