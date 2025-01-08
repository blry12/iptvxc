import os, sqlite3, time
import xbmc,xbmcvfs,xbmcaddon,xbmcgui,xbmcplugin
from resources.modules import control,tools, variables, popup
from resources.caching import ini_cache, eqp_cache

def addonsettings(typ):
	if	 typ =="clearcache":
		tools.clear_cache()
	elif typ =="AS":
		xbmc.executebuiltin('Addon.OpenSettings(%s)'% variables.ADDON_ID)
	elif typ =="ADS":
		dialog = xbmcgui.Dialog().select('Edit Advanced Settings', ['Open AutoConfig','Enable Fire TV Stick AS','Enable Fire TV AS','Enable 1GB Ram or Lower AS','Enable 2GB Ram or Higher AS','Enable Nvidia Shield AS','Disable AS'])
		if dialog==0:
			advancedsettings('auto')
		elif dialog==1:
			advancedsettings('stick')
			tools.ASln()
		elif dialog==2:
			advancedsettings('firetv')
			tools.ASln()
		elif dialog==3:
			advancedsettings('lessthan')
			tools.ASln()
		elif dialog==4:
			advancedsettings('morethan')
			tools.ASln()
		elif dialog==5:
			advancedsettings('shield')
			tools.ASln()
		elif dialog==6:
			advancedsettings('remove')
			xbmcgui.Dialog().ok(ADDON_NAME, 'Advanced Settings Removed')
	elif typ =="ADS2":
		dialog = xbmcgui.Dialog().select('Select Your Device Or Closest To', ['Open AutoConfig','Fire TV Stick ','Fire TV','1GB Ram or Lower','2GB Ram or Higher','Nvidia Shield'])
		if dialog==0:
			advancedsettings('auto')
			tools.ASln()
		elif dialog==1:
			advancedsettings('stick')
			tools.ASln()
		elif dialog==2:
			advancedsettings('firetv')
			tools.ASln()
		elif dialog==3:
			advancedsettings('lessthan')
			tools.ASln()
		elif dialog==4:
			advancedsettings('morethan')
			tools.ASln()
		elif dialog==5:
			advancedsettings('shield')
			tools.ASln()
	elif typ =="tv":
		dialog = xbmcgui.Dialog().yesno(variables.ADDON_NAME,'Would You like us to Setup the TV Guide for You?')
		if dialog:
			pvrsetup()
			xbmcgui.Dialog().ok(variables.ADDON_NAME, 'PVR Integration Complete, Restart Kodi For Changes To Take Effect')
	elif typ =="Itv":
			xbmc.executebuiltin('InstallAddon(pvr.iptvsimple)')
	elif typ =="ST":
		speedtest.speedtest()
	elif typ =="XXX":
		if control.setting('hidexxx')=='true':
			pas = tools.keypopup('Enter Adult Password:')
			if pas ==control.setting('xxx_pw'):
				control.setSetting('hidexxx','false')
				xbmc.executebuiltin('Container.Refresh')
		else:
			control.setSetting('hidexxx','true')
			xbmc.executebuiltin('Container.Refresh')
	elif typ =="GUI":
		if xbmcaddon.Addon().getSetting('gui')=='true':
			control.setSetting('gui','false')
			xbmc.executebuiltin('Container.Refresh')
		else:
			control.setSetting('gui','true')
			xbmc.executebuiltin('Container.Refresh')
	elif typ =="LO":
		control.setSetting('DNS','')
		control.setSetting('Username','')
		control.setSetting('Password','')
		xbmc.executebuiltin('XBMC.ActivateWindow(Videos,addons://sources/video/)')
		control.setSetting('first_run','true')

		time.sleep(1)
		DB_PATH = os.path.join(variables.ADDONDATA, "epg_cache.db")
		DB_PATH1 = os.path.join(variables.ADDONDATA, "media_cache.db")
		try:
			conn = sqlite3.connect(variables.DB_PATH)
			conn.close()
			conn = sqlite3.connect(variables.DB_PATH1)
			conn.close()
		except sqlite3.Error as e:
			tools.log(f"Error closing DB connection: {e}")
		userdata_path = os.path.join(xbmcvfs.translatePath(variables.ADDONDATA))
		cache_dirs = ['media_cache.db', 'epg_cache.db', 'xmltv.xml']
		
		for item in cache_dirs:
			item_path = os.path.join(userdata_path, item)
			if os.path.exists(item_path):
				if os.path.isdir(item_path):
					shutil.rmtree(item_path)
				else:
					os.remove(item_path)

		xbmc.executebuiltin('Container.Refresh')
	elif typ == "RefM3U":
		DP.create(ADDON_NAME, "Please Wait")
		tools.gen_m3u(variables.panel_api, variables.M3U_PATH)
	elif typ == "TEST":
		tester()

def advancedsettings(device):
	if device == 'stick':
		file = open(os.path.join(advanced_settings, 'stick.xml'))
	elif device =='auto':
		popup.autoConfigQ()
	elif device == 'firetv':
		file = open(os.path.join(advanced_settings, 'firetv.xml'))
	elif device == 'lessthan':
		file = open(os.path.join(advanced_settings, 'lessthan1GB.xml'))
	elif device == 'morethan':
		file = open(os.path.join(advanced_settings, 'morethan1GB.xml'))
	elif device == 'shield':
		file = open(os.path.join(advanced_settings, 'shield.xml'))
	elif device == 'remove':
		os.remove(ADVANCED)
	try:
		read = file.read()
		f = open(ADVANCED, mode='w+')
		f.write(read)
		f.close()
	except:
		pass

def cache(_type):
	if _type == 'cat_cache':
		ini_cache.manual_cache_update()
	elif _type == 'epg_cache':
		eqp_cache.EPGUpdater().manual_update()
	elif _type == 'wipe_cache':
		delete_cache()
	elif _type == 'users':
		UserManager().manage_users()
	elif _type == 'start_cache':
		dialog = DIALOG.ok(variables.ADDON_NAME,'Press OK to start setting up your cache?\nThis will cache all categoies and EPG data.')
		if dialog:
			ini_cache.manual_cache_update()
			eqp_cache.EPGUpdater().manual_update()
		control.setSetting('first_run','false')
		xbmc.executebuiltin('Container.Refresh')

def delete_cache():
	time.sleep(1)
	DB_PATH = os.path.join(ADDONDATA, "epg_cache.db")
	DB_PATH1 = os.path.join(ADDONDATA, "media_cache.db")
	try:
		conn = sqlite3.connect(DB_PATH)
		conn.close()
		conn = sqlite3.connect(DB_PATH1)
		conn.close()
	except sqlite3.Error as e:
		tools.log(f"Error closing DB connection: {e}")
	userdata_path = os.path.join(xbmcvfs.translatePath(ADDONDATA))
	cache_dirs = ['media_cache.db', 'epg_cache.db', 'xmltv.xml']
	
	for item in cache_dirs:
		item_path = os.path.join(userdata_path, item)
		if os.path.exists(item_path):
			if os.path.isdir(item_path):
				shutil.rmtree(item_path)
			else:
				os.remove(item_path)

	xbmcgui.Dialog().notification("Cache Cleared", "All cache has been deleted.", xbmcgui.NOTIFICATION_INFO, 5000)
	dialog = DIALOG.yesno(ADDON_NAME,'Would you like to rebuild the cache?\nIt will be slower if you dont! \nYou can always do this in Cache menu later on.')
	if dialog:
		dialog = DIALOG.yesno(ADDON_NAME,'Would you like to cache all the categories?\nIt will be slower if you dont! \nYou can always do this in Cache menu later on.')
		if dialog:
			ini_cache.manual_cache_update()
			pass
		dialog = DIALOG.yesno(ADDON_NAME,'Would you like to Download the EPG data?\nIf not it will rely on short EPG data if you dont. \nYou can always do this in Cache menu later on.')
		if dialog:
			tvguide.EPGUpdater().manual_update()
	del dialog