# -*- coding: utf-8 -*-

#v1.0.0 2009/11/08 by robinttt, initial release
#v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import urllib
import urllib2
import re
import sys
import gzip
import StringIO #playvideo
import hashlib, time
from bs4 import BeautifulSoup
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'
URL_BASE = 'http://yinyue.kuwo.cn'
INDENT_STR = '    '
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'

#
# Web process engine
#
def getUrlTree(url, data=None):
    if data and not isinstance(data, str):
        # 2-item tuple or param dict, assume utf-8
        data = urllib.urlencode(data)
    req = urllib2.Request(url, data, {'User-Agent': UserAgent})
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        # BeautifulSoup handles encoding, thus skip transcoding here.

    return httpdata


#
# Media player
#
def get_content_by_tag(tree, tag):
    f = tree.find(tag)
    if f and f.contents:
        return f.contents[0].encode('utf-8')
    else:
        return ''


def PlayMusic(url):
    mids = url

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    mids = mids.split('/')
    for mid in mids:
        if mid == '':
            continue
        html = getUrlTree('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_'+mid)
        tree = BeautifulSoup(html, 'html.parser')
        title = get_content_by_tag(tree, 'name')
        # kuwo has names like "song name(抢听版)", causing lyrics look up failure
        true_title = title.split('(')[0].rstrip()
        artist = get_content_by_tag(tree, 'artist')
        iconimage = get_content_by_tag(tree, 'artist_pic240')

        # prefer AAC or WMA, somehow it starts or loads faster than the mp3 link,
        # change AAC to the first download.  edit by runner6502@gamil.com
        path = get_content_by_tag(tree, 'aacpath')
        dl = get_content_by_tag(tree, 'aacdl')
        if not (path and dl):
            path = get_content_by_tag(tree, 'path')
            dl = get_content_by_tag(tree, 'wmadl')
            if not (path and dl):
                path = get_content_by_tag(tree, 'mp3path')
                dl = get_content_by_tag(tree, 'mp3dl')

        if path and dl:
            timestamp = ("%x" % int(time.time()))[:8]
            hashstr = hashlib.md5("kuwo_web@1906/resource/%s%s" % (path, timestamp)).hexdigest()
            url = 'http://%s/%s/%s/resource/%s' % (dl, hashstr, timestamp, path)

            listitem = xbmcgui.ListItem(title, iconImage=iconimage, thumbnailImage=iconimage)
            listitem.setInfo(type="Music", infoLabels={"Title": true_title, "Artist": artist})
            playlist.add(url, listitem)

        xbmc.Player().play(playlist)


def musiclist(name, url):
    html = getUrlTree(url)
    l = re.findall('"musiclist":(\[.+\]),"rids"', html)
    if not l:
        return
    l = eval(l[0])
    mids = "/".join([d['musicrid'] for d in l])
    item = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0] + '?mode=play&url=' + mids
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)
    for d in l:
        title = d['name']
        artist = d['artist']
        mid = d['musicrid']
        displayname = artist + ' - ' + title if artist else title
        item = xbmcgui.ListItem(displayname)
        u = sys.argv[0] + '?mode=play&url=' + mid
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, listitem=item, isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumlist(name, url, tree=None):
    if tree is None:
        html = getUrlTree(url)
        tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('ul', {'class': 'singer_list clearfix'})
    li = soup[0].find_all('li')

    for item in li:
        url = item.a['href'].encode('utf-8')
        url = URL_BASE + url
        itemp = item.p.text
        attr = 'album' if u'列表' in itemp else 'list'
        name = item.a['title'].encode('utf-8')
        name = name + '(' + itemp.encode('utf-8') + ')'
        image = item.img['lazy_src']
        u = sys.argv[0] + '?url=' + url + '&mode=%s&name='%attr + name
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listRoot():
    html = getUrlTree(URL_BASE + '/category.htm')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'hotlist'})

    item = xbmcgui.ListItem(BANNER_FMT % soup[0].h1.text.encode('utf-8'))
    u = sys.argv[0] + '?mode=title'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

    x = soup[0].find_all('ul', {'class': 'clearfix'})
    li = x[0].find_all('li')

    for item in li:
        url = item.a['href'].encode('utf-8')
        name = item.text.encode('utf-8')
        url = URL_BASE + url
        u = sys.argv[0] + '?url=' + url + '&mode=album&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    item = xbmcgui.ListItem(BANNER_FMT % soup[1].h1.text.encode('utf-8'))
    u = sys.argv[0] + '?mode=title'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

    x = soup[1].find_all('ul', {'class': 'clearfix'})
    li = x[0].find_all('li')

    for item in li:
        url = item.a['href'].encode('utf-8')
        name = item.text.encode('utf-8')
        url = URL_BASE + url
        u = sys.argv[0] + '?url=' + url + '&mode=album&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    albumlist('Main Menu', url, tree)


params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')
name = params.get('name')
url = params.get('url')

if mode is None:
    listRoot()
elif mode == 'album':
    albumlist(name, url)
elif mode == 'list':
    musiclist(name, url)
elif mode == 'play':
    PlayMusic(url)
