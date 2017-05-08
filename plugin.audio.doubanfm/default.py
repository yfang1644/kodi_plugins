#!/usr/bin/python
# -*- coding: utf-8 -*-

import DoubanFM
import xbmcplugin
import xbmcgui
import xbmc
import urllib
import urllib2


def addLink(name, url, totalItems):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url) + \
            "&mode=play" + \
            "&name="+urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name)
    liz.setInfo(type="Music", infoLabels={"Title": name})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False, totalItems)


params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

url = params.get('url')
name = params.get('name')
mode = params.get('mode')

if mode is None:
    channels = DoubanFM.GetChannels()
    n = len(channels)
    for name, url in channels:
        addLink(name.encode('utf-8'), str(url), n)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

else:
    playlist = xbmc.PlayList(0)
    playlist.clear()

    # add song to playlist
    songs = DoubanFM.GetSongs(url)
    for song in songs:
        pic = song.pop('pic')
        url = song.pop('url')
        listitem = xbmcgui.ListItem(song['title'])
        listitem.setInfo('Music', song)
        listitem.setThumbnailImage(pic)
        playlist.add(url, listitem)

    print 'Added '+str(playlist.size()) + ' songs'
    xbmc.Player().play(playlist)
