import os, xbmc, xbmcgui, xbmcaddon, xbmcvfs, json
from . import control
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
USER_DATA = os.path.join(ADDONDATA, "user.json")
##########################=ART PATHS=#######################################
icon			  = os.path.join(PLUGIN,  'icon.png')
fanart			  = os.path.join(PLUGIN,  'fanart.jpg')
background		  = os.path.join(MEDIA,	  'background.jpg')
logo			  = os.path.join(MEDIA,	  'logo.png')
icontvguide		  = os.path.join(MEDIA,	  'iconguide.png')
tvguidebg		  = os.path.join(MEDIA,	  'g_bg.png')
focus_texture		  = os.path.join(MEDIA,	  'button_focus.png')
no_focus_texture		  = os.path.join(MEDIA,	  'button.png')

#########################=XC VARIABLES=#####################################
def r_from_json():
    try:
        if os.path.exists(USER_DATA):
            with open(USER_DATA, 'r') as f:
                data = json.load(f)
                return data
        else:
            return []
    except Exception as e:
        xbmc.log(f"Unexpected error reading {USER_DATA}: {e}", xbmc.LOGERROR)
        return []
credentials = r_from_json()
if credentials:
	for cred in credentials:
		dns = cred['dns']
		username = cred['username']
		password = cred['password']
else:
	#dns				  = control.setting('DNS')
	#username		  = control.setting('Username')
	#password		  = control.setting('Password')
	dns				  = ''
	username		  = ''
	password		  = ''


panel_api		  = f"{dns}/panel_api.php?username={username}&password={password}"
player_api		  = f"{dns}/player_api.php?username={username}&password={password}"

play_url		  = f"{dns}/live/{username}/{password}/"
play_live		  = f"{dns}/{username}/{password}/"
play_movies		  = f"{dns}/movie/{username}/{password}/"
play_series		  = f"{dns}/series/{username}/{password}/"

live_all		  = f"{player_api}&action=get_live_streams"
live_cat		  = f"{player_api}&action=get_live_categories"
live_streams	  = f"{player_api}&action=get_live_streams&category_id="
live_short_epg	  = f"{player_api}&action=get_short_epg&stream_id="

vod_all			  = f"{player_api}&action=get_vod_streams"
vod_cat			  = f"{player_api}&action=get_vod_categories"
vod_streams		  = f"{player_api}&action=get_vod_streams&category_id="
vod_info		  = f"{player_api}&action=get_vod_info&vod_id="

series_all		  = f"{player_api}&action=get_series"
series_cat		  = f"{player_api}&action=get_series_categories"
series_list		  = f"{player_api}&action=get_series&category_id="
series_season	  = f"{player_api}&action=get_series_info&series_id="

XMLTV_URL		  = f"{dns}/xmltv.php?username={username}&password={password}"
#############################################################################
adult_tags = ['xxx','xXx','XXX','adult','Adult','ADULT','adults','Adults','ADULTS','porn','Porn','PORN', '18+']
DB_PATH = os.path.join(ADDONDATA, "epg_cache.db")