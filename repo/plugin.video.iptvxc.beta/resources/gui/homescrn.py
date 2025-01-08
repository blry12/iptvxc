import json, xbmcgui, xbmc, time
from resources.pyxbmct import addonwindow as pyxbmct
from resources.modules import control,tools, variables
from resources.caching import ini_cache, eqp_cache
from resources.gui import tvguide, vod, series, settings, catchup, search
from datetime import datetime


def entry():
	h = HomePage()
	h.doModal()
	del h

#add to settings xml and make it check a few day before expiry with notify
def userx():
	xbmc.executebuiltin('Container.Refresh')
	response = tools.OPEN_URL(variables.player_api)
	parsed_data = json.loads(response)
	expiry_timestamp = parsed_data['user_info'].get('exp_date', None)
	username = parsed_data['user_info'].get('username', 'Unknown User')
	if expiry_timestamp:
		expiry = datetime.utcfromtimestamp(int(expiry_timestamp)).strftime('%B %d - %Y')
	else:
		expiry = 'Unlimited'
	return {'expiry': expiry, 'username': username}

#wont work in class
def _close(self):
	xbmc.executebuiltin("Container.Update(path,replace)") #reset path
	xbmc.executebuiltin("ActivateWindow(Home)")# fix why it want to open when choosing video addons
	self.close()

def setting():
	s = settings.SettingWindow()
	s.doModal()
	del s

def account_info():
	class AccountInfo(pyxbmct.AddonDialogWindow):
		def __init__(self):
			super(AccountInfo, self).__init__("Account Information")
			self.setGeometry(525, 400, 10, 5)
			self.account_data = self.fetch_account_data(variables.player_api)
			self.place_controls()
			self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

		def fetch_account_data(self, player_api):
			response = tools.OPEN_URL(player_api)
			parse = json.loads(response)
			expiry = parse['user_info']['exp_date']
			if expiry:
				expiry_date = datetime.utcfromtimestamp(int(expiry)).strftime('%B %d - %Y')
			else:
				expiry = "Unlimited"
			return {
				"username": parse['user_info']['username'],
				"password": parse['user_info']['password'],
				"expiry": expiry,
				"status": parse['user_info']['status'],
				"active_connections": parse['user_info']['active_cons'],
				"max_connections": parse['user_info']['max_connections'],
				"local_ip": tools.getlocalip(),
				"external_ip": tools.getexternalip(),
			}

		def place_controls(self):
			data = self.account_data
			labels = [
				f"[B][COLOR white]Username:[/COLOR][/B] {data['username']}",
				f"[B][COLOR white]Password:[/COLOR][/B] {data['password']}",
				f"[B][COLOR white]Expiry Date:[/COLOR][/B] {data['expiry']}",
				f"[B][COLOR white]Account Status:[/COLOR][/B] {data['status']}",
				f"[B][COLOR white]Current Connections:[/COLOR][/B] {data['active_connections']}",
				f"[B][COLOR white]Allowed Connections:[/COLOR][/B] {data['max_connections']}",
				f"[B][COLOR white]Local IP Address:[/COLOR][/B] {data['local_ip']}",
				f"[B][COLOR white]External IP Address:[/COLOR][/B] {data['external_ip']}",
			]

			start_row = 1
			for i, label_text in enumerate(labels):
				label = pyxbmct.Label(label_text)
				self.placeControl(label, start_row + i, 1, columnspan=4)

	a = AccountInfo()
	a.doModal()
	del a

class HomePage(pyxbmct.AddonFullWindow):
	def __init__(self):
		super(HomePage, self).__init__("Home Page")
		self.setGeometry(1280, 720, 100, 50)
		Background = pyxbmct.Image(variables.tvguidebg)
		self.placeControl(Background, -8, -1, 122, 58)
		self.set_info_controls()
		self.set_navigation()
		if control.setting('first_run')=='true':
			ini_cache.manual_cache_update()
			eqp_cache.EPGUpdater().manual_update()
			control.setSetting('first_run','false')


	def set_info_controls(self):
		focus_texture = variables.focus_texture
		no_focus_texture = variables.no_focus_texture
		self.connect(pyxbmct.ACTION_NAV_BACK, lambda:_close(self))

		_time = pyxbmct.Label("[B][COLOR white]$INFO[System.Date][/COLOR][/B]	  [B][COLOR white]$INFO[System.Time][/COLOR][/B]")
		self.placeControl(_time, -1, 17, 2,20)

		self.search_button = pyxbmct.Button(
			"Search", focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.placeControl(self.search_button, -1, 1, rowspan=10, columnspan=10)
		self.connect(self.search_button, lambda:search.entry())
		self.account_info_button = pyxbmct.Button(
			"Account Info", focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.placeControl(self.account_info_button, -1, 40, rowspan=10, columnspan=10)
		self.connect(self.account_info_button, lambda:account_info())

		self.live_tv_button = pyxbmct.Button(
			"Live TV", font='font40', focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.placeControl(self.live_tv_button, 40, 3, rowspan=55, columnspan=15)
		self.connect(self.live_tv_button, lambda:tvguide.entry())
		self.vod_button = pyxbmct.Button(
			"VOD",font='font14', focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.placeControl(self.vod_button, 40, 18, rowspan=40, columnspan=15)
		self.connect(self.vod_button, lambda:vod.entry())
		self.tv_series_button = pyxbmct.Button(
			"TV Series",font='font14', focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.placeControl(self.tv_series_button, 40, 33, rowspan=40, columnspan=15)
		self.connect(self.tv_series_button, lambda:series.entry())

		self.catchup_button = pyxbmct.Button(
			"Catch Up", focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.connect(self.catchup_button, lambda:catchup.entry())
		self.placeControl(self.catchup_button, 81, 20, rowspan=10, columnspan=11)
		self.settings_button = pyxbmct.Button(
			"Settings", focusTexture=focus_texture, noFocusTexture=no_focus_texture
		)
		self.connect(self.settings_button, lambda:setting())
		self.placeControl(self.settings_button, 81, 35, rowspan=10, columnspan=11)

		_userx = userx()
		_expiry = pyxbmct.Label(f"[B][COLOR white]Expiration :[/COLOR][/B]  {_userx['expiry']}")
		self.placeControl(_expiry, 100, 1, rowspan=10, columnspan=15)

		_user = pyxbmct.Label(f"[B][COLOR white]Logged In :[/COLOR][/B] {_userx['username']}")
		self.placeControl(_user, 100, 39, rowspan=10, columnspan=11)


	def on_button_press(self):
		xbmcgui.Dialog().notification("Short Press", "You clicked the button!", xbmcgui.NOTIFICATION_INFO, 2000)
	
	def on_action(self):
		self.start_time = time.time()
		if self.start_time:
			duration = time.time() - self.start_time
			self.start_time = None
			if duration >= 1:  # 1-second threshold for long press
				self.on_long_press()
			else:
				xbmcgui.Dialog().notification("Short Press", "Button released too quickly.", xbmcgui.NOTIFICATION_INFO, 2000)

	def on_long_press(self):
			xbmcgui.Dialog().notification("Long Press", "You held the button long enough!", xbmcgui.NOTIFICATION_INFO, 3000)


	def set_navigation(self):
		self.account_info_button.controlDown(self.tv_series_button)

		self.search_button.controlUp(self.live_tv_button)
		self.search_button.controlRight(self.settings_button)

		self.live_tv_button.controlRight(self.vod_button)
		self.live_tv_button.controlUp(self.search_button)

		self.vod_button.controlLeft(self.live_tv_button)
		self.vod_button.controlRight(self.tv_series_button)
		self.vod_button.controlDown(self.catchup_button)
		self.vod_button.controlUp(self.search_button)

		self.tv_series_button.controlUp(self.account_info_button)
		self.tv_series_button.controlLeft(self.vod_button)
		self.tv_series_button.controlDown(self.settings_button)

		self.catchup_button.controlUp(self.tv_series_button)
		self.catchup_button.controlRight(self.settings_button)

		self.settings_button.controlUp(self.tv_series_button)
		self.settings_button.controlLeft(self.catchup_button)

		self.setFocus(self.live_tv_button)
