############################################################################
#						\ Fire TV Guru /								   #
############################################################################

#############################=IMPORTS=######################################
	#Kodi Specific
import xbmc,xbmcvfs,xbmcaddon,xbmcgui,xbmcplugin
	#Python Specific
import base64,os,re,time,sys,urllib.request
import urllib.parse,urllib.error,json,datetime,shutil
import xml.dom.minidom
from xml.dom.minidom import Node
from datetime import datetime,timedelta
from urllib.parse import urlparse, parse_qs
#parsed_url = urlparse(url)
	#Addon Specific
from resources.pyxbmct import addonwindow
from resources.modules import control,tools,popup,speedtest, variables
from resources.gui import tvguide, vod, series, login, homescrn
import shutil, sqlite3
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


'''
todos
convert all to use variables module
make json for user pass and not settings xml(kodi cant refresh fast enough)
implement multi dns - db already made


finish settings menu
make search menu


'''

def search_menu():
	tools.addDir('Search in Live TV','live','search',iconlive,background,'')
	tools.addDir('Search in TV Series','series','search',iconTvseries,background,'')
	tools.addDir('Search in Video On Demand','vod','search',iconMoviesod,background,'')

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

def adult_set1():
	dialog = DIALOG.yesno(ADDON_NAME,'Would you like to hide the Adult Menu? \nYou can always change this in settings later on.')
	if dialog:
		control.setSetting('xxx_pwset','true')
		pass
	else:
		control.setSetting('xxx_pwset','false')
		pass
	dialog = DIALOG.yesno(ADDON_NAME,'Would you like to Password Protect Adult Content? \nYou can always change this in settings later on.')
	if dialog:
		control.setSetting('xxx_pwset','true')
		adultpw = tools.keypopup('Enter Password')
		control.setSetting('xxx_pw',adultpw)
	else:
		control.setSetting('xxx_pwset','false')
		pass

if __name__ == '__main__': 
	if variables.username == "":
		login.entry()
	else:
		homescrn.entry()

xbmcplugin.endOfDirectory(int(sys.argv[1]))




