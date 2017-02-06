# -*- coding: utf-8 -*-
import sys
import urllib2
import urllib
import time
import re
import xbmc
import xbmcplugin
import xbmcgui
from bs4 import BeautifulSoup

URL_BASE = 'http://www.kuwo.cn/www/category/index'
UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'


def getUrlTree(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)

    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()

    response.close()
    match = re.compile('encoding=(.+?)"').findall(httpdata)
    if not match:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if match:
        charset = match[0].lower()
    if (charset != 'utf-8') and (charset != 'utf8'):
        httpdata = unicode(httpdata, charset).encode('utf8')

    # BeautifulSoup handles encoding, thus skip transcoding here.

    tree = BeautifulSoup(httpdata, "html.parser")
    return tree


def rootList():
    tree = getUrlTree(URL_BASE)

    h2 = tree.find_all('h2')

    xbmcplugin.setContent(handle, 'albums')
    n = len(h2)
    for i in range(0, n):
        li = xbmcgui.ListItem(h2[i].string)
        print  h2[i]['data-catid']
        url = plugin_url+"?&act=sublist&title="+"&hash="
        xbmcplugin.addDirectoryItem(handle, url, li, False, n)
    xbmcplugin.endOfDirectory(handle)


def subList():


#获得相应电台的歌曲的列表
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


#播放音乐
def play(hashId, title):
    playlist = xbmc.PlayList(0)
    playlist.clear() #中止播放列表
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
    page = params.get('page', 1)
    rootList()
elif act = 'sublist'
    subList()
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
