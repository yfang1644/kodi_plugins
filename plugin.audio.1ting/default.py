#!/usr/bin/python
# -*- coding: utf-8 -*-

import music
import xbmc
import xbmcgui
import xbmcplugin
from urllib import urlencode
from urlparse import parse_qsl
import sys


def addList(lists):
    # name, mode, url, icon, info
    n = len(lists)
    plugin = sys.argv[0]
    handle = int(sys.argv[1])
    for i in lists:
        name = i[0]
        mode = i[1] if len(i) > 1 else music.MODE_NONE
        isFolder = music.isFolder(mode)
        query = {"mode": mode}
        if len(i) > 2:
            query["url"] = i[2]
        li = xbmcgui.ListItem(name)
        if len(i) > 3:
            icon = i[3]
            query['icon'] = icon
            li.setIconImage(icon)
        if len(i) > 4:
            info = i[4]
            query.update(info)
            li.setInfo(type="Music", infoLabels=info)
            isFolder = False
        u = "%s?%s" % (plugin, urlencode(query))
        xbmcplugin.addDirectoryItem(handle, u, li, isFolder, n)
    xbmcplugin.endOfDirectory(handle)


def play(name, mode, url, icon, info):
    li = xbmcgui.ListItem(name)
    li.setInfo(type='Music', infoLabels=info)
    li.setThumbnailImage(icon)
    url = music.getSongUrl(url)
    xbmc.Player().play(url, li)


def playSong(params):
    name = params['title']
    icon = params['icon']
    mode = params['mode']
    url = params['url']
    info = {'title': name,
            'artist': params['artist'],
            'album': params['album']}
    play(name, mode, url, icon, info)


def playList(url):
    song = music.getPlayList(url)[0]
    if len(song) == 5:
        play(*song)
    else:
        xbmcgui.Dialog().notification(url, song[0], xbmcgui.NOTIFICATION_ERROR)


def get_keyword():
    keyboard = xbmc.Keyboard('', '请输入歌名,专辑或歌手进行搜索,支持简拼.')
    xbmc.sleep(1500)
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        return keyword


def search():
    q = get_keyword()
    print 'q', q
    if q:
        url = music.getSearchUrl(q)
        return music.getSearchList(url)
    else:
        return []


params = sys.argv[2][1:]
paramlist = dict(parse_qsl(params))
mode = paramlist.get("mode", music.MODE_MENU)
url = paramlist.get("url", "")

l = []

if mode == music.MODE_SONG:
    playSong(paramlist)
elif mode == music.MODE_PLAYLIST:
    playList(url)
elif mode == music.MODE_SEARCH:
    l = search()
else:
    l = music.getList(mode, url)
if l:
    addList(l)
