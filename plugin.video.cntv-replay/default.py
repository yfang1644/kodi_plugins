# -*- coding: utf-8 -*-

import sys
import time
import urllib 
import urlparse
import xbmc
import xbmcgui 
import xbmcplugins
import xbmcaddon

def cn_time_s():  # return CST (China Standard Time) in seconds
    lc_time = time.localtime()
    gm_time_s = time.mktime(time.gmtime())
    return gm_time_s + (8-lc_time.tm_isdst)*60*60 # CST = GMT + 8h, tm_isdst = {1,0,-1}

addon = xbmcaddon.Addon()
title = addon.getAddonInfo('name')
thumbnail = addon.getAddonInfo('icon')
pwd_path = addon.getAddonInfo('path')
mediaType = 'Video'

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

media_ended = False
media_stopped = False

# channel urls have the form of 'http://8.37.234.13/v.cctv.com/live_back/nettv_cctv1/cctv1'...
# BASE_URL = 'http://8.37.234.13'
# BASE_URL = 'http://220.243.235.9'
BASE_URL = 'http:/'
chnurl = BASE_URL + '/v.cctv.com/live_back/nettv_'

# list of channels
tv_listing = [['cctv1', '1-综合'],
              ['cctv2', '2-财经'],
              ['cctv3', '3-综艺'],
              ['cctv4', '4-国际'],
              ['cctv5', '5-体育'],
              ['cctv5plus', '5+体育'],
              ['cctv6', '6-电影'],
              ['cctv7', '7-体育农业'],
              ['cctv8', '8-电视剧'],
              ['cctv9', '9-纪录'],
              ['cctv10', '10-科教'],
              ['cctv11', '11-戏曲'],
              ['cctv12', '12-社会与法制'],
              ['cctv13', '13-新闻'],
              ['cctv15', '15-音乐']]

class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass
        xbmc.log('#=#=#=# '+ channel + ' XBMCPlayer Initialized #=#=#=#')

    def __del__(self):
        xbmc.log('#=#=#=# '+ channel + ' XBMCPlayer Destructed #=#=#=#')

    def nPlayBackPaused(self):
        xbmc.log('#=#=#=# Status: ' + channel + ' Playback Paused #=#=#=#')

    def onPlayBackResumed(self):
        xbmc.log('#=#=#=# Status: ' + channel + ' Playback Resumed #=#=#=#')

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        xbmc.log('#=#=#=# Status: ' + channel + ' Playback Started #=#=#=#')
        global media_ended
        global media_stopped
        media_ended = False
        media_stopped = False

    def onPlayBackEnded(self):
        # Will be called when xbmc ended playing a file
        xbmc.log('#=#=#=# Status: ' + channel + ' Playback Ended, #=#=#=#')
        global media_ended
        media_ended = True
        global media_stopped  # let treated media_ended the same as media_stopped for now
        media_stopped = True

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        xbmc.log('#=#=#=# Status: ' + channel + ' Playback Stopped #=#=#=#')
        global media_stopped
        media_stopped = True
        # self.stop()


class XBMCMonitor(xbmc.Monitor):
    def __init__(self, *args):
        pass
        xbmc.log("#=#=#=# Monitor initialized  #=#=#=#")

    def __del__(self):
        xbmc.log("#=#=#=# Monitor destructed #=#=#=#")

    def abortRequested(self):
        # Returns True if abort has been requested.
        xbmc.log("#=#=#=# Status: ** abort *** has been requestd #=#=#=#")


def cntvplay(ch):
    b_url = chnurl + ch +'/' + ch +'-'
    player = XBMCPlayer()
    monitor = XBMCMonitor()
    global media_stopped

    while(not media_stopped):
        cur = cn_time_s()
        hr = (time.strftime("%Y-%m-%d-%H", time.localtime(cur-600)))
        seg = '%03d' % (int((time.strftime("%M", time.localtime(cur-600))))/5+1)
        url = b_url + hr + "-" + seg + '.mp4?wsiphost=local'
        li = xbmcgui.ListItem(label=title, iconImage=thumbnail, thumbnailImage=thumbnail, path=url)
        li.setInfo(type=mediaType, infoLabels={"Title": title})
        player.play(item=url, listitem=li)
        for x in range(1, 300):
            if monitor.waitForAbort(1) or media_stopped: # Sleep/wait for abort for 1 second
                xbmc.log('#=#=#=# ' + ch + ' aborted or media_stopped #=#=#=#')
                media_stopped = True
                break   # Abort was requested while waiting. Exit the while loop.
    player.stop()
    xbmc.log('#=#=#=# left ' + ch + ' #=#=#=#')


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

#  main program ##################
xbmcplugin.setContent(addon_handle, 'movies')
channel = 'cctv00'

mode = args.get('mode', None)

if mode is None:   # first time call, fill up the tv_listing
    for i in tv_listing:
        url = build_url({'mode': 'folder', 'foldername': i[0]})
        li = xbmcgui.ListItem(i[1], iconImage=pwd_path + '/resources/media/' + i[0]+'.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
    channel = args['foldername'][0]
    cntvplay(channel)   # should get cctv1, cctv2 etc
