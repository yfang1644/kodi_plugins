#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcplugin
import xbmcgui
import kugou
import sys
import urllib2
import urllib
import time


# 显示 酷狗FM 的相应的专辑
def index(page):
    currpage = int(page)
    pagesize = 30
    lists = kugou.getFmList(page, pagesize)
    totalPages = (lists['recordcount']-1)//pagesize + 1
    for i in lists['data']:
        li = xbmcgui.ListItem(i['fmname'])
        li.setInfo(type="Music", infoLabels={"Title": i['fmname']})
        icon = 'http://imge.kugou.com/fmlogo/145/%s' % i['imgurl']
        li.setIconImage(icon)
        query = {'act': 'list', 'fmid': i['fmid'], 'icon': icon}
        url = "%s?%s" % (plugin_url, urllib.urlencode(query))
        xbmcplugin.addDirectoryItem(handle, url, li, True)
    # 设置分页
    if currpage > 1:
        linkpage = currpage - 1
        prevLi = xbmcgui.ListItem('上一页 【[COLOR FF00FF00]%s[/COLOR]/[COLOR FFFF0000]%s[/COLOR]】'%(linkpage,totalPages))
        u = "%s?act=index&page=%s" % (plugin_url, linkpage)
        xbmcplugin.addDirectoryItem(handle, u, prevLi, True)
    if currpage < totalPages:
        linkpage = currpage + 1
        nextLi = xbmcgui.ListItem('下一页 【[COLOR FF00FF00]%s[/COLOR]/[COLOR FFFF0000]%s[/COLOR]】'%(linkpage,totalPages))
        u = "%s?act=index&page=%s" % (plugin_url, linkpage)
        xbmcplugin.addDirectoryItem(handle, u, nextLi, True)
    xbmcplugin.endOfDirectory(handle)


# 获得相应电台的歌曲的列表
def getPlayList(fmid, icon):
    title = '播放当前专辑所有歌曲'
    listitemAll = xbmcgui.ListItem(title, iconImage=icon)
    listitemAll.setInfo(type="Music", infoLabels={"Title": title})
    t = int(time.time())
    query = {'act': 'playList', 'fmid': fmid, 'time': t}
    listUrl = '%s?%s' % (plugin_url, urllib.urlencode(query))
    xbmcplugin.addDirectoryItem(handle, listUrl, listitemAll, False)
    songs = kugou.getSongs(fmid, t)
    # 判断songs是否存在
    if songs:
        for song in songs:
            listitem = xbmcgui.ListItem(song['name'])
            listitem.setInfo(type="Music", infoLabels={"Title": song['name'], })
            url = plugin_url+"?act=play&title="+song['name'].encode('utf-8')+"&hash="+urllib.quote_plus(song['hash'].encode('utf-8'))
            xbmcplugin.addDirectoryItem(handle, url, listitem, False)
        xbmcplugin.endOfDirectory(handle)


#播放当前Fm列表里的歌曲
def playList(fmid, t):
    playlist = xbmc.PlayList(0)
    playlist.clear()
    for song in kugou.getSongs(fmid, t):
        listitem = xbmcgui.ListItem(song['name'])
        listitem.setInfo(type="Music", infoLabels={"Title": song['name']})
        playlist.add(kugou.getSongInfo(song['hash']), listitem)
    xbmc.Player().play(playlist)


# 播放音乐
def play(hashId, title):
    playlist = xbmc.PlayList(0)
    playlist.clear()          # 中止播放列表
    xbmc.Player().stop()
    mp3path = kugou.getSongInfo(hashId)
    icon = kugou.getSingerPic(title, 100)
    thumbnail = kugou.getSingerPic(title, 200)
    listitem=xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumbnail)
    listitem.setInfo(type="Music", infoLabels={"Title": title})
    xbmc.Player().play(mp3path, listitem)

plugin_url = sys.argv[0]
handle = int(sys.argv[1])
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

act = params.get('act', 'index')
fmid = params.get("fmid", '')

if act == 'index':
    page = params.get("page", 1)
    index(page)
elif act == 'list':
    icon = params.get('icon', '')
    getPlayList(fmid, icon)
elif act == 'playList':
    t = params.get('time', 0)
    playList(fmid, t)
elif act == 'play':
    hashId = urllib.unquote_plus(params['hash'])
    title = params.get('title', '')
    play(hashId, title)
