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
		open_data = tools.OPEN_URL(player_api + '&action=get_live_streams')
		if not open_data:
			xbmcgui.Dialog().notification("Error", "No response from the server", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		try:
			data = json.loads(open_data)
		except json.JSONDecodeError:
			xbmcgui.Dialog().notification("Error", "Invalid JSON format from server", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		archive_streams = [stream for stream in data if stream.get('tv_archive', 0)]

		total_archives = len(archive_streams)
		tools.log(f"Total archive streams: {total_archives}")

		if total_archives == 0:
			xbmcgui.Dialog().notification("No Channels", "No channels with archives found.", xbmcgui.NOTIFICATION_INFO, 3000)
			return

		channels = []

		progress = xbmcgui.DialogProgress()
		progress.create("Loading Channels", "Processing channels with archives...")

		for index, stream in enumerate(archive_streams):
			percent_complete = int((index + 1) / total_archives * 100)
			progress.update(percent_complete, f"Processing {index + 1} of {total_archives} archived streams...")
			if progress.iscanceled():
				progress.close()
				xbmcgui.Dialog().notification("Cancelled", "Operation cancelled by user", xbmcgui.NOTIFICATION_INFO, 3000)
				return

			name = stream.get('name', "Unknown Channel")
			thumb = stream.get('stream_icon', iconcatchup)
			stream_id = stream.get('stream_id')
			duration = stream.get('tv_archive_duration', 0)
			#tools.log(f"Processing stream: {name}, id: {stream_id}, duration: {duration}")
			if not name or not stream_id or not duration:
				continue

			channels.append({
				"id": stream_id,
				"name": name,
				"thumb": thumb,
				"duration": duration,
			})

		progress.close()
		window = CatchupWindow(channels=channels)
		window.doModal()
		del window

	except Exception as e:
		xbmcgui.Dialog().notification("Error", f"An unexpected error occurred: {str(e)}", xbmcgui.NOTIFICATION_ERROR, 3000)



class CatchupWindow(pyxbmct.AddonFullWindow):
	def __init__(self, channels=None):
		super().__init__("Channel & Archive Viewer")
		self.setGeometry(1280, 720, 50, 30)

		self.channels = channels or []
		self.archives = []
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

		self.background = pyxbmct.Image(tvguidebg)
		self.placeControl(self.background, -5, -1, 58, 40)

		title_name = pyxbmct.Label(ADDON_NAME)
		self.placeControl(title_name, -3, 12, 1, 5)

		self.full_scrn__button = pyxbmct.Button('Back to stream')
		self.placeControl(self.full_scrn__button, -3, 25, 3, 5)
		self.connect(self.full_scrn__button, self._go_back_to_stream)

		self.channel_list = pyxbmct.List("font13", _itemHeight=50, _space=10, _imageWidth=120, _imageHeight=90)
		self.placeControl(self.channel_list, 0, 0, 35, 11)
		self.connect(self.channel_list, self._on_channel_selected)

		self.archive_list = pyxbmct.List("font13", _itemHeight=50, _space=10, _imageWidth=90, _imageHeight=70)
		self.placeControl(self.archive_list, 0, 11, 35, 18)
		self.connect(self.archive_list, self._on_archive_selected)

		self.channel_icon = pyxbmct.Image("")
		self.placeControl(self.channel_icon, 32, 0, 15, 8)

		self.channel_description = pyxbmct.TextBox("font14")
		self.placeControl(self.channel_description, 32, 8, 25, 22)
		self.channel_description.setText("")

		self._populate_channels()
		self.set_navigation()

		self.connectEventList(
			[pyxbmct.ACTION_MOVE_DOWN, pyxbmct.ACTION_MOVE_UP, pyxbmct.ACTION_MOUSE_MOVE],
			self._on_archive_highlighted
		)

	def set_navigation(self):
		self.channel_list.controlRight(self.archive_list)
		self.archive_list.controlLeft(self.channel_list)

		self.full_scrn__button.controlDown(self.archive_list)
		self.full_scrn__button.controlLeft(self.channel_list)
		self.archive_list.controlRight(self.full_scrn__button)

	def _populate_channels(self):
		for channel in self.channels:
			#self.channel_list.addItem(channel["name"])

			list_item = xbmcgui.ListItem(label=f"{channel['name']} Days {channel['duration']}")
			list_item.setArt({"icon": channel['thumb']} )
			self.channel_list.addItem(list_item)
		self.setFocus(self.channel_list)

	def _on_channel_selected(self):
		selected_index = self.channel_list.getSelectedPosition()
		if selected_index < 0:
			return

		selected_channel = self.channels[selected_index]
		self._load_archives(selected_channel)

	def _load_archives(self, channel):
		self.archives.clear()
		self.archive_list.reset()

		api_url = f"{player_api}&action=get_simple_data_table&stream_id={channel['id']}"
		response = tools.OPEN_URL(api_url)
		try:
			data = json.loads(response)
		except json.JSONDecodeError:
			xbmcgui.Dialog().notification("Error", "Invalid JSON format for archives", xbmcgui.NOTIFICATION_ERROR, 3000)
			return

		for archive in data.get("epg_listings", []):
			if not archive.get("has_archive"):
				continue

			title = base64.b64decode(archive.get("title", "")).decode("utf-8")
			plot = base64.b64decode(archive.get("description", "")).decode("utf-8")
			start_time = archive.get("start", "")
			end_time = archive.get("end", "")

			self.archives.append({
				"title": title,
				"plot": plot,
				"start_time": start_time,
				"end_time": end_time,
				"channel_icon": channel["thumb"],
			})

		self._populate_archives()

	def _populate_archives(self):
		for archive in self.archives:
			#self.archive_list.addItem(f"{archive['start_time']} - {archive['title']}")
			list_item = xbmcgui.ListItem(label=f"{archive['start_time']} - {archive['title']}")
			list_item.setArt({"icon": archive['channel_icon']} )
			self.archive_list.addItem(list_item)
		self.setFocus(self.archive_list)

	def _on_archive_selected(self):
		selected_index = self.archive_list.getSelectedPosition()
		if selected_index < 0:
			return

		selected_archive = self.archives[selected_index]
		self._update_archive_details(selected_archive)

	def _on_archive_highlighted(self):
		selected_index = self.archive_list.getSelectedPosition()
		if selected_index < 0:
			return

		selected_archive = self.archives[selected_index]
		self._update_archive_details(selected_archive)

	def _update_archive_details(self, archive):
		description = f"Title: {archive['title']}\n\nDescription: {archive['plot']}\nStart: {archive['start_time']}\nEnd: {archive['end_time']}"
		self.channel_description.setText(description)
		self.channel_icon.setImage(archive["channel_icon"])

	def _go_back_to_stream(self):
		player = xbmc.Player()

		if player.isPlaying():
			xbmc.executebuiltin("ActivateWindow(12005)")
		else:
			xbmcgui.Dialog().notification("No Stream", "No stream is currently playing.", xbmcgui.NOTIFICATION_INFO, 5000) 

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



