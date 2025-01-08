import json, xbmcgui, xbmc
from resources.pyxbmct import addonwindow as pyxbmct
from resources.modules import control,tools, variables, speedtest, defs
from datetime import datetime

class SettingWindow(pyxbmct.AddonDialogWindow):
	def __init__(self, title="Settings Menu"):
		super(SettingWindow, self).__init__(title)
		self.setGeometry(900, 450, 50, 30)
		self.buttons = []
		self.set_active_controls()
		self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

	def set_active_controls(self):
		self.list = pyxbmct.List(_itemTextXOffset=-10)
		self.placeControl(self.list, 1, 1, rowspan=48, columnspan=10)
		items = ["Speed Test", "Edit Advanced Settings", "Cache Settings", "Adult Settings", "Logout"]
		self.list.addItems(items)
		self.details_label = pyxbmct.Label("[B][COLOR white]Details:[/COLOR][/B]")
		self.placeControl(self.details_label, 1, 11, columnspan=20)
		self.details_area = pyxbmct.TextBox()
		self.placeControl(self.details_area, 5, 11, rowspan=45, columnspan=20)
		self.create_buttons()
		self.hide_all_buttons()
		self.set_navigation(0)

		self.setFocus(self.list)
		self.connectEventList([pyxbmct.ACTION_MOVE_DOWN, pyxbmct.ACTION_MOVE_UP, pyxbmct.ACTION_MOUSE_MOVE], self.on_list_item_selected)

	def create_buttons(self):
		self.speed_test_button = pyxbmct.Button("Run Speed Test")
		self.placeControl(self.speed_test_button, 45, 15, columnspan=8, rowspan=8)
		self.connect(self.speed_test_button, lambda: self.run_speed_test())

		self.edit_settings_button = pyxbmct.Button("Edit Advanced Settings")
		self.placeControl(self.edit_settings_button, 45, 15, columnspan=8, rowspan=8)
		self.connect(self.edit_settings_button, lambda: self.edit_advanced_settings())

		self.cat_cache_label = pyxbmct.Label("[B][COLOR white]IPTV CACHE: [/COLOR][/B]Manually update the cach.")
		self.placeControl(self.cat_cache_label, 14, 13, columnspan=14)
		self.cat_cache_button = pyxbmct.Button("Start")
		self.placeControl(self.cat_cache_button, 19, 15, columnspan=8, rowspan=6)
		self.connect(self.cat_cache_button, lambda: self.cat_cache())

		self.epg_cache_label = pyxbmct.Label("[B][COLOR white]EPG Cache: [/COLOR][/B]Manually update the cach.")
		self.placeControl(self.epg_cache_label, 26, 13, columnspan=14)
		self.epg_cache_button = pyxbmct.Button("Start")
		self.placeControl(self.epg_cache_button, 31, 15, columnspan=8, rowspan=6)
		self.connect(self.epg_cache_button, lambda: self.epg_cache())

		self.reset_cache_label = pyxbmct.Label("[B][COLOR white]Clear Cache: [/COLOR][/B]Clears all cache!")
		self.placeControl(self.reset_cache_label, 38, 13, columnspan=14)
		self.reset_cache_button = pyxbmct.Button("Delete")
		self.placeControl(self.reset_cache_button, 43, 15, columnspan=8, rowspan=6)
		self.connect(self.reset_cache_button, lambda: self.reset_cache())

		self.adult_settings_button = pyxbmct.Button("Edit Adult Settings")
		self.placeControl(self.adult_settings_button, 45, 15, columnspan=8, rowspan=8)
		self.connect(self.adult_settings_button, lambda: self.edit_adult_settings())

		self.logout_button = pyxbmct.Button("Logout")
		self.placeControl(self.logout_button, 45, 15, columnspan=8, rowspan=8)
		self.connect(self.logout_button, lambda: self.logout())

		self.buttons = [
			{"item": 0, "buttons": [self.speed_test_button]},
			{"item": 1, "buttons": [self.edit_settings_button]},
			{
				"item": 2,
				"buttons": [
					self.cat_cache_button,
					self.epg_cache_button,
					self.reset_cache_button,
					self.cat_cache_label,
					self.epg_cache_label,
					self.reset_cache_label,
				],
			},
			{"item": 3, "buttons": [self.adult_settings_button]},
			{"item": 4, "buttons": [self.logout_button]},
		]

	def on_list_item_selected(self):
		selected_index = self.list.getSelectedPosition()
		details_text = {
			0: "Run a network speed test to check your connection.",
			1: "Edit advanced settings like buffering or quality options.",
			2: "Manage cache settings. Manually update IPTV, EPG, or reset cache.",
			3: "Configure adult content settings and restrictions.",
			4: "Logout from your current session.",
		}.get(selected_index, "Select an option to view details.")
		self.details_area.setText(details_text)

		self.hide_all_buttons()
		for button_group in self.buttons:
			if button_group["item"] == selected_index:
				for button in button_group["buttons"]:
					button.setVisible(True)

		self.set_navigation(selected_index)

	def set_navigation(self, selected_index):
		self.list.controlRight(self.speed_test_button)
		self.speed_test_button.controlLeft(self.list)
		self.edit_settings_button.controlLeft(self.list)
		self.cat_cache_button.controlLeft(self.list)
		self.epg_cache_button.controlLeft(self.list)
		self.reset_cache_button.controlLeft(self.list)
		self.adult_settings_button.controlLeft(self.list)
		self.logout_button.controlLeft(self.list)

		if selected_index == 0:
			self.list.controlRight(self.speed_test_button)
			self.speed_test_button.controlLeft(self.list)
			self.speed_test_button.controlDown(self.edit_settings_button)

		elif selected_index == 1:
			self.list.controlRight(self.edit_settings_button)
			self.edit_settings_button.controlLeft(self.list)
			self.edit_settings_button.controlDown(self.cat_cache_button)

		elif selected_index == 2:
			self.list.controlRight(self.cat_cache_button)
			self.cat_cache_button.controlLeft(self.list)
			self.cat_cache_button.controlDown(self.epg_cache_button)

			self.epg_cache_button.controlLeft(self.list)
			self.epg_cache_button.controlDown(self.reset_cache_button)
			self.epg_cache_button.controlUp(self.cat_cache_button)

			self.reset_cache_button.controlLeft(self.list)
			self.reset_cache_button.controlUp(self.epg_cache_button)

		elif selected_index == 3:
			self.list.controlRight(self.adult_settings_button)
			self.adult_settings_button.controlLeft(self.list)
			self.adult_settings_button.controlDown(self.logout_button)

		elif selected_index == 4:
			self.list.controlRight(self.logout_button)
			self.logout_button.controlLeft(self.list)


	def hide_all_buttons(self):
		for button_group in self.buttons:
			for button in button_group["buttons"]:
				button.setVisible(False)

	def run_speed_test(self):
		speedtest.speedtest()

	def edit_advanced_settings(self):
		defs.addonsettings('ADS')

	def cat_cache(self):
		defs.cache('cat_cache')

	def epg_cache(self):
		defs.cache('epg_cache')

	def reset_cache(self):
		defs.delete_cache()

	def edit_adult_settings(self):
		defs.addonsettings('XXX')

	def logout(self):
		defs.addonsettings('LO')
