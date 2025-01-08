import json, xbmcgui, xbmc
from resources.pyxbmct import addonwindow
from resources.modules import control,tools, variables
from resources.gui import homescrn

def entry():
	l = LoginWindow()
	l.doModal()
	del l

class LoginWindow(addonwindow.AddonDialogWindow):
	def __init__(self, title=f"Login to Service        {variables.ADDON_NAME}"):
		super().__init__(title)
		self.setGeometry(600, 350, 6, 3)
		self._setup_ui()
		self._set_navigation()

	def _setup_ui(self):
		self.connect(addonwindow.ACTION_NAV_BACK, self.close)

		self.placeControl(addonwindow.Label('DNS:'), 1, 0)
		self.placeControl(addonwindow.Label('Username:'), 2, 0)
		self.placeControl(addonwindow.Label('Password:'), 3, 0)

		self.name_input = addonwindow.Edit('', 'font16')
		self.placeControl(self.name_input, 1, 1, columnspan=2)

		self.username_input = addonwindow.Edit('')
		self.placeControl(self.username_input, 2, 1, columnspan=2)

		self.password_input = addonwindow.Edit('')
		self.placeControl(self.password_input, 3, 1, columnspan=2)

		self.login_button = addonwindow.Button('Login')
		self.placeControl(self.login_button, 5, 1)
		self.connect(self.login_button, self._login_action)

		self.cancel_button = addonwindow.Button('Cancel')
		self.placeControl(self.cancel_button, 5, 2)
		self.connect(self.cancel_button, self.close)

		self.setFocus(self.name_input)

	def _set_navigation(self):
		self.name_input.controlDown(self.username_input)
		self.username_input.controlUp(self.name_input)
		self.username_input.controlDown(self.password_input)
		self.password_input.controlUp(self.username_input)
		self.password_input.controlDown(self.login_button)

		self.login_button.controlUp(self.password_input)
		self.login_button.controlRight(self.cancel_button)
		self.cancel_button.controlLeft(self.login_button)

	def _login_action(self):
		dns = self.name_input.getText()
		username = self.username_input.getText()
		password = self.password_input.getText()

		auth_url = f"{dns}/player_api.php?username={username}&password={password}"
		response = tools.OPEN_URL(auth_url)
		parse = json.loads(response)
		login_data = parse['user_info']['auth']

		if login_data == 0:
			xbmcgui.Dialog().notification('Login Failed', 'Please fill all fields!')
		else:
			tools.s_to_json({"dns": dns, "username": username, "password": password})

			xbmcgui.Dialog().notification('Login Success', f"Welcome {username}!")
			self.close()
			xbmc.sleep(200)
			homescrn.entry()