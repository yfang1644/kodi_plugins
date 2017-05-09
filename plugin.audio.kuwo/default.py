#!/usr/bin/python
# -*- coding: utf-8 -*-

# v1.0.0 2009/11/08 by robinttt, initial release
# v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urllib
import urllib2
import re
import sys
import gzip
import StringIO
import hashlib
import time
from bs4 import BeautifulSoup

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'
URL_BASE = 'http://yinyue.kuwo.cn'
INDENT_STR = '    '
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'


#
# Web process engine
#
def getUrlTree(url):
    req = urllib2.Request(url.replace(' ', '%20'))  # some names have ' '
    req.add_header('User-Agent', UserAgent)
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


def PlayMusic(params):
    mids = params.get('url')
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    mids = mids.split('/')
    mids = [x for x in mids if x != '']   # remove empty items
    for mid in mids:
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


def PlayMV(params):
    name = params.get('name')
    url = params.get('url')
    thumb = params.get('thumb')

    html = getUrlTree(url)
    mp4 = re.compile('var mp4url.+(http:.+?mp4)').findall(html)
    mp4 = mp4[0]
    playlist = xbmc.PlayList(1)
    playlist.clear()
    listitem = xbmcgui.ListItem(name, iconImage=thumb, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    playlist.add(mp4, listitem)
    xbmc.Player().play(playlist)


def musiclist(params):
    name = params.get('name')
    url = params.get('url')

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


def albumlist(params, tree=None):
    name = params.get('name')
    url = params.get('url')

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


def category():
    html = getUrlTree(URL_BASE + '/category.htm')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'hotlist'})

    for hotlist in soup:
        item = xbmcgui.ListItem(BANNER_FMT % hotlist.h1.text.encode('utf-8'))
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        x = hotlist.find_all('ul', {'class': 'clearfix'})
        li = x[0].find_all('li')

        for item in li:
            url = item.a['href'].encode('utf-8')
            name = item.text.encode('utf-8')
            url = URL_BASE + url
            u = sys.argv[0] + '?url=' + url + '&mode=album&name=' + name
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    pdict = {'name': 'Main Menu', 'url': url}
    albumlist(pdict, tree)


def singeralbum(params):
    name = params.get('name')
    url = params.get('url')
    page = int(params.get('page', 0))
    artistid = params.get('artistId')

    item = xbmcgui.ListItem(BANNER_FMT % '专辑')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

    html = getUrlTree(url)
    tree = BeautifulSoup(html, "html.parser")

    # ALBUM #######################################
    soup = tree.find_all('div', {'id': 'album'})
    li = soup[0].find_all('li')
    for album in li:
        image = album.find('div', {'class': 'cover'})
        image = image.img['src']
        name = album.find('span', {'class': 'name'})
        aurl = name.a['href'].encode('utf-8')
        name = name.text.strip('\n').encode('utf-8')
        u = sys.argv[0] + '?url=' + aurl + '&mode=album1&name=' + name
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    # MV ###############################################
    soup = tree.find_all('div', {'id': 'mv'})
    li = soup[0].find_all('li')
    item = xbmcgui.ListItem(BANNER_FMT % 'MV')
    u = sys.argv[0] + '?mode=title'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)
    for mv in li:
        image = mv.find('div', {'class': 'cover'})
        image = image.img['src']
        name = mv.find('span', {'class': 'name'})
        aurl = name.a['href'].encode('utf-8')
        name = name.text.strip('\n').encode('utf-8')
        u = sys.argv[0] + '?url=' + aurl + '&mode=playmv&name=' + name
        u += "&thumb=%s" % image.encode('utf-8')
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    # SONGS ###############################################
    aurl = 'http://www.kuwo.cn/artist/contentMusicsAjax'
    aurl += '?artistId=%s&pn=%d&rn=15' % (artistid, page)
    html = getUrlTree(aurl)
    l = re.compile('"id":"MUSIC_(\d+)').findall(html)
    maxpage = re.compile('data-page="(\d+)"').findall(html)
    maxpage = int(maxpage[0])

    if l:
        tree = BeautifulSoup(html, 'html.parser')
        soup = tree.find_all('li', {'class': 'onLine'})
        item = xbmcgui.ListItem(BANNER_FMT % '单曲(全部播放)')
        mids = '/'.join(l)
        u = sys.argv[0] + '?mode=play&url=' + mids
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        if page > 0:
            name = BANNER_FMT % '上一页'
            aurl = url
            aurl += "&artistId=%s&page=%d" % (artistid, page-1)
            u = sys.argv[0] + '?url=' + aurl + '&mode=singeralbum'
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

        for song in soup:
            mid = re.compile('\d+').findall(song.a['href'])
            mid = mid[0].encode('utf-8')
            name = song.a.text.encode('utf-8')
            u = sys.argv[0] + '?url=' + mid + '&mode=play&name=' + name
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False)

        if page < maxpage:
            name = BANNER_FMT % '下一页'
            aurl = url
            aurl += "&artistId=%s&page=%d" % (artistid, page+1)
            u = sys.argv[0] + '?url=' + aurl + '&mode=singeralbum'
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def singergroup(params):
    name = params.get('name')
    url = params.get('url')
    prefix = params.get('prefix', '')
    page = int(params.get('page', 0))

    html = getUrlTree(url + '&prefix=%s&pn=%d' % (prefix, page))
    # pn=page number, prefix=alphabet, initial singer name
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'artistTop'})

    if page > 0:
        name = BANNER_FMT % '上一页'
        aurl = url + '&prefix=%s&page=%d' % (prefix, page-1)
        u = sys.argv[0] + '?url=' + aurl + '&mode=singers'
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    for artist in soup:
        aurl = artist.a['href'].encode('utf-8')
        name = re.compile('name=(.+)').findall(aurl)
        name = name[0]
        aurl = 'http://www.kuwo.cn' + aurl
        artistid = artist.find('div', {'class': 'artistnav'})['data-id']
        u = sys.argv[0] + '?url=' + aurl + '&mode=singeralbum&name=' + name
        u += "&page=0&artistId=%s" % artistid.encode('utf-8')
        image = artist.img['src']
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    soup = tree.find('div', {'class': 'page'})
    maxpage = int(soup['data-page'])
    if page < maxpage:
        name = BANNER_FMT % '下一页'
        aurl = url + '&prefix=%s&page=%d' % (prefix, page+1)
        u = sys.argv[0] + '?url=' + aurl + '&mode=singers'
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    for abc in range(0x41, 0x5B):   # A--Z
        ch = chr(abc)
        aurl = url + '&prefix=%s&page=%d' % (ch, page)
        u = sys.argv[0] + '?url=' + aurl + '&mode=singers'
        liz = xbmcgui.ListItem(ch)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def singerlist():
    html = getUrlTree('http://www.kuwo.cn/artist/index')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('dl', {'class': 'area'})

    for singer in soup:
        item = xbmcgui.ListItem(BANNER_FMT % singer.span.text.encode('utf-8'))
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        li = singer.find_all('dd')

        for item in li:
            url = item.a['href'].encode('utf-8')
            url = 'http://www.kuwo.cn' + url
            name = item.text.strip('\n').encode('utf-8')
            u = sys.argv[0] + '?url=' + url + '&mode=singers&name=' + name
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def single_album(params):
    name = params.get('name')
    url = params.get('url')

    html = getUrlTree(url)
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('li', {'class': 'clearfix'})

    l = re.findall('class="[Mm]usicID.+mid="(.+)"', html)
    if not l:
        return
    mids = "/".join(l)
    item = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0] + '?mode=play&url=' + mids
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

    for item in soup:
        mid = item.p.input['mid'].encode('utf-8')
        name = item.a.text.encode('utf-8')
        u = sys.argv[0] + '?url=' + mid + '&mode=play&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def sortitem(params):
    name = params.get('name')
    url = params.get('url')

    html = getUrlTree(url)
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'music clearfix'})

    for item in soup:
        url = item.a['href'].encode('utf-8')
        name = item.a['title'].encode('utf-8')
        u = sys.argv[0] + '?url=' + url + '&mode=album1&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    soup = tree.find_all('div', {'class': 'page'})
    li = soup[0].find_all('a')

    for item in li:
        url = item['href'].encode('utf-8')
        name = item.text.encode('utf-8')
        u = sys.argv[0] + '?url=' + url + '&mode=sortitem&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def sortlist():
    html = getUrlTree('http://www.kuwo.cn/album/')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'sdlist clearfix'})

    for sdlist in soup:
        item = xbmcgui.ListItem(BANNER_FMT % sdlist.h1.text.encode('utf-8'))
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        li = sdlist.find_all('li')

        for item in li:
            url = item.a['href'].encode('utf-8')
            name = item.text.encode('utf-8')
            u = sys.argv[0] + '?url=' + url + '&mode=sortitem&name=' + name
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listRoot():
    li = xbmcgui.ListItem('分类')
    u = sys.argv[0] + '?url=url&mode=category'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    li = xbmcgui.ListItem('歌手')
    u = sys.argv[0] + '?url=url&mode=singer'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    li = xbmcgui.ListItem('专辑')
    u = sys.argv[0] + '?url=url&mode=sort'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'listRoot()',
    'category': 'category()',
    'singer': 'singerlist()',
    'sort': 'sortlist()',
    'singerarea': 'singerarea()',
    'singers': 'singergroup(params)',
    'singeralbum': 'singeralbum(params)',
    'sortitem': 'sortitem(params)',
    'album1': 'single_album(params)',
    'album': 'albumlist(params)',
    'list': 'musiclist(params)',
    'play': 'PlayMusic(params)',
    'playmv': 'PlayMV(params)'
}

eval(runlist[mode])
