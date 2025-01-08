#!/usr/bin/python														   #
# -*- coding: utf-8 -*-													   #
############################################################################
#							  /T /I										   #
#							   / |/ | .-~/								   #
#						   T\ Y	 I	|/	/  _							   #
#		  /T			   | \I	 |	I  Y.-~/							   #
#		 I l   /I		T\ |  |	 l	|  T  /								   #
#	  T\ |	\ Y l  /T	| \I  l	  \ `  l Y								   #
# __  | \l	 \l	 \I l __l  l   \   `  _. |								   #
# \ ~-l	 `\	  `\  \	 \ ~\  \   `. .-~	|								   #
#  \   ~-. "-.	`  \  ^._ ^. "-.  /	 \	 |								   #
#.--~-._  ~-  `	 _	~-_.-"-." ._ /._ ." ./								   #
# >--.	~-.	  ._  ~>-"	  "\   7   7   ]								   #
#^.___~"--._	~-{	 .-~ .	`\ Y . /	|								   #
# <__ ~"-.	~		/_/	  \	  \I  Y	  : |								   #
#	^-.__			~(_/   \   >._:	  | l______							   #
#		^--.,___.-~"  /_/	!  `-.~"--l_ /	   ~"-.						   #
#			   (_/ .  ~(   /'	  "~"--,Y	-=b-. _)					   #
#				(_/ .  \  Fire TV Guru/ l	   c"~o \					   #
#				 \ /	`.	  .		.^	 \_.-~"~--.	 )					   #
#				  (_/ .	  `	 /	   /	   !	   )/					   #
#				   / / _.	'.	 .':	  /		   '					   #
#				   ~(_/ .	/	 _	`  .-<_								   #
#					 /_/ . ' .-~" `.  / \  \		  ,z=.				   #
#					 ~( /	'  :   | K	 "-.~-.______//					   #
#					   "-,.	   l   I/ \_	__{--->._(==.				   #
#						//(		\  <	~"~"	 //						   #
#					   /' /\	 \	\	  ,v=.	((						   #
#					 .^. / /\	  "	 }__ //===-	 `						   #
#					/ / ' '	 "-.,__ {---(==-							   #
#				  .^ '		 :	T  ~"	ll								   #
#				 / .  .	 . : | :!		 \								   #
#				(_/	 /	 | | j-"		  ~^							   #
#				  ~-<_(_.^-~"											   #
#																		   #
############################################################################

#############################=IMPORTS=######################################
	#Kodi Specific
import xbmc,xbmcvfs,xbmcplugin,xbmcgui, xbmcaddon
	#Python Specific
import os,re,sys,json,base64,shutil,socket
import urllib.request,urllib.parse,urllib.error,urllib.parse
from urllib.parse import urlparse
from urllib.request import Request, urlopen
	#Addon Specific
from . import control, variables

##########################=VARIABLES=#######################################
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
GET_SET = xbmcaddon.Addon(ADDON_ID)
ADDON_NAME = ADDON.getAddonInfo("name")
PROFILE_PATH = xbmcaddon.Addon().getAddonInfo('profile')
ICON   = xbmcvfs.translatePath(os.path.join('special://home/addons/' + ADDON_ID,  'icon.png'))
DIALOG = xbmcgui.Dialog()
DP	= xbmcgui.DialogProgress()
COLOR1='white'
COLOR2='blue'
dns_text = GET_SET.getSetting(id='DNS')
USER_DATA = variables.USER_DATA

def check_protocol(url):
	parsed = urlparse(dns_text)
	protocol = parsed.scheme
	if protocol=='https':
		return url.replace('http','https')
	else:
		return url

def log(msg):
	msg = str(msg)
	xbmc.log('%s-%s'%(ADDON_ID,msg),2)

def b64(obj):
	return base64.b64decode(obj).decode('utf-8')

def percentage(part, whole):
	return 100 * float(part)/float(whole)
	
def getInfo(label):
	try: return xbmc.getInfoLabel(label)
	except: return False
	
def LogNotify(title, message, times=3000, icon=ICON,sound=False):
	DIALOG.notification(title, message, icon, int(times), sound)
	
def ASln():
	return LogNotify("[COLOR {0}]{1}[/COLOR]".format(COLOR1, ADDON_ID), '[COLOR {0}]AdvancedSettings.xml have been written[/COLOR]'.format(COLOR2))

def regex_from_to(text, from_string, to_string, excluding=True):
	if excluding:
		try: r = re.search("(?i)" + from_string + "([\S\s]+?)" + to_string, text).group(1)
		except: r = ''
	else:
		try: r = re.search("(?i)(" + from_string + "[\S\s]+?" + to_string + ")", text).group(1)
		except: r = ''
	return r

def regex_get_all(text, start_with, end_with):
	r = re.findall("(?i)(" + start_with + "[\S\s]+?" + end_with + ")", text)
	return r
	
def regex_get_us(text, start_with, end_with):
	r = re.findall("(?i)(" + start_with + ".+?[UK: Sky Sports].+?" + end_with + ")", text)
	return r
	
def addDir(name, url, mode, iconimage, fanart, description):
	default_icon = "DefaultIcon.png"
	default_fanart = "DefaultFanart.jpg"
	
	name = str(name) if name else "Unknown"
	url = str(url) if url else ""
	iconimage = str(iconimage) if iconimage else default_icon
	fanart = str(fanart) if fanart else default_fanart
	description = str(description) if description else "No description available"
	
	params = {
		"url": urllib.parse.quote_plus(url),
		"mode": str(mode),
		"name": urllib.parse.quote_plus(name),
		"iconimage": urllib.parse.quote_plus(iconimage),
		"description": urllib.parse.quote_plus(description),
	}
	u = sys.argv[0] + "?" + "&".join(f"{key}={value}" for key, value in params.items())
#files songs artists albums movies tvshows episodes musicvideos videos images games
	#if mode in ['live_category', 'live_list']:
	#	xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	#elif mode in ['vod_category', 'vod_list']:
	#	xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	#elif mode in ['series_lists', 'series_seasons', 'episode_list']:
	#	xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
	#elif mode in ['search', 'search_menu']:
	#	xbmcplugin.setContent(int(sys.argv[1]), 'search')
	#else:
	#	xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	
	# Create the ListItem
	liz = xbmcgui.ListItem(name)
	liz.setArt({"icon": iconimage, "thumb": iconimage})
	liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description})
	liz.setProperty("fanart_image", fanart)

	# Determine if the item is playable
	is_playable_modes = {'play_live_stream', 'play_stream_video'}
	isFolder = mode not in is_playable_modes
	if not isFolder:
		liz.setProperty("IsPlayable", "true")

	# Add the directory item
	if mode == 'addonsettings' or mode == 'gui':
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
	else:
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)
	
	return ok

def OPEN_URL(url, binary=False):
    try:
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0')
        with urlopen(req) as response:
            if binary:
                return response.read()
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        log(f"Error fetching URL {url} : {e}")
        return None

def s_to_json(creds):
    try:
        data = [creds]
        with open(USER_DATA, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        xbmc.log(f"Error saving credentials: {e}", xbmc.LOGERROR)

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



def clear_cache():
	xbmc.log('CLEAR CACHE ACTIVATED')
	xbmc_cache_path = os.path.join(xbmcvfs.translatePath('special://home'), 'cache')
	confirm=xbmcgui.Dialog().yesno("Please Confirm","Please Confirm You Wish To Delete Your Kodi Application Cache")
	if confirm:
		if os.path.exists(xbmc_cache_path)==True:
			for root, dirs, files in os.walk(xbmc_cache_path):
				file_count = 0
				file_count += len(files)
				if file_count > 0:
						for f in files:
							try:
								os.unlink(os.path.join(root, f))
							except:
								pass
						for d in dirs:
							try:
								shutil.rmtree(os.path.join(root, d))
							except:
								pass
		LogNotify("[COLOR {0}]{1}[/COLOR]".format(COLOR1, ADDON_NAME), '[COLOR {0}]Cache Cleared Successfully![/COLOR]'.format(COLOR2))
		xbmc.executebuiltin("Container.Refresh()")

def get_params():
	params = {}
	if len(sys.argv) > 2:
		paramstring = sys.argv[2]
		if len(paramstring) >= 2:
			cleanedparams = paramstring.lstrip('?').rstrip('/')
			pairsofparams = cleanedparams.split('&')
			for pair in pairsofparams:
				if '=' in pair:
					key, value = pair.split('=', 1)	 # Split on first '='
					params[key] = value
	return params

def getlocalip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8', 0))
	s = s.getsockname()[0]
	return s

def getexternalip():
	import json 
	url = urllib.request.urlopen("https://api.ipify.org/?format=json")
	data = json.loads(url.read().decode())
	return str(data["ip"])

def MonthNumToName(num):
	if '01' in num:
		month = 'January'
	elif '02' in num:
		month = 'Febuary'
	elif '03' in num:
		month = 'March'
	elif '04' in num:
		month = 'April'
	elif '05' in num:
		month = 'May'
	elif '06' in num:
		month = 'June'
	elif '07' in num:
		month = 'July'
	elif '08' in num:
		month = 'Augast'
	elif '09' in num:
		month = 'September'
	elif '10' in num:
		month = 'October'
	elif '11' in num:
		month = 'November'
	elif '12' in num:
		month = 'December'
	return month

def num2day(num):
	if num =="0":
		day = 'monday'
	elif num=="1":
		day = 'tuesday'
	elif num=="2":
		day = 'wednesday'
	elif num=="3":
		day = 'thursday'
	elif num=="4":
		day = 'friday'
	elif num=="5":
		day = 'saturday'
	elif num=="6":
		day = 'sunday'
	return day

def killxbmc():
	killdialog = xbmcgui.Dialog().yesno('Force Close Kodi', '[COLOR white]You are about to close Kodi', 'Would you like to continue?[/COLOR]', nolabel='[B][COLOR red] No Cancel[/COLOR][/B]',yeslabel='[B][COLOR green]Force Close Kodi[/COLOR][/B]')
	if killdialog:
		os._exit(1)
	else:
		home()

def gen_m3u(url, path):
	parse = json.loads(OPEN_URL(url))
	i=1
	DP.create(ADDON_NAME, "Please Wait")
	with open (path, 'w+', encoding="utf-8") as ftg:
		ftg.write('#EXTM3U\n')
		for items in parse['available_channels']:
			a = parse['available_channels'][items]
			
			if a['stream_type'] == 'live':
				
				b = '#EXTINF:-1 channel-id="{0}" tvg-id="{1}" tvg-name="{2}" tvg-logo="{3}" channel-id="{4}" group-title="{5}",{6}'.format(i, a['epg_channel_id'], a['epg_channel_id'], a['stream_icon'], a['name'], a['category_name'], a['name'])
				
				if parse['server_info']['server_protocol'] == 'https':
					port = parse['server_info']['https_port']
				else:
					port = parse['server_info']['port']
				
				dns = '{0}://{1}:{2}'.format(parse['server_info']['server_protocol'], parse['server_info']['url'], port)
				c = '{0}/{1}/{2}/{3}'.format(dns, parse['user_info']['username'], parse['user_info']['password'],a['stream_id'])
				ftg.write(b+'\n'+c+'\n')
				i +=1
				DP.update(int(100), 'Found Channel \n' + a['name'] + '\n')
				if DP.iscanceled(): break
		DP.close
		DIALOG.ok(ADDON_NAME, 'Found ' + str(i) + ' Channels')

def keypopup(heading):
	kb =xbmc.Keyboard ('', 'heading', True)
	kb.setHeading(heading)
	kb.setHiddenInput(False)
	kb.doModal()
	if (kb.isConfirmed()):
		text = kb.getText()
		return text
	else:
		return False