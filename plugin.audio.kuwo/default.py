#!/usr/bin/python
# -*- coding: utf-8 -*-

# v1.0.0 2009/11/08 by robinttt, initial release
# v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import urlparse
import re
import sys
from bs4 import BeautifulSoup
from common import get_html, match1

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

URL_BASE = 'http://yinyue.kuwo.cn'
INDENT_STR = '    '
BANNER_FMT = '[COLOR gold][%s][/COLOR]'

#
# Media player
#

def PlayMusic(params):
    supported_stream_types = ['aac', 'wma', 'mp3']

    mids = params.get('url')
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    mids = mids.split('/')
    mids = [x for x in mids if x != '']   # remove empty items
    for mid in mids:
        api_url = 'http://player.kuwo.cn/webmusic/st/getNewMuiseByRid'
        print '=====================', api_url + '?rid=MUSIC_' + mid
        html = get_html(api_url + '?rid=MUSIC_' + mid)
        title = match1(html, '<name>(.*)</name>')
        # kuwo has names like "song name(抢听版)", causing lyrics look up failure
        true_title = title.split('(')[0].rstrip()
        artist = match1(html, '<artist>(.*)</artist>')
        iconimage = match1(html, '<artist_pic240>(.*)</artist_pic240>')

        # prefer AAC or WMA, somehow it starts or loads faster than the mp3 link,

        api_url = 'http://antiserver.kuwo.cn/anti.s'
        api_url += '?type=convert_url&response=url'
        for t in supported_stream_types:
            url = get_html(api_url + '&format={}&rid=MUSIC_{}'.format(t, mid))
            if url:
                break
        listitem = xbmcgui.ListItem(title,
                                    iconImage=iconimage,
                                    thumbnailImage=iconimage)
        listitem.setInfo(type='Music',
                         infoLabels={'Title': true_title, 'Artist': artist})
        playlist.add(url, listitem)

    xbmc.Player().play(playlist)


def PlayMV(params):
    name = params.get('name')
    url = params.get('url')
    thumb = params.get('thumb')

    html = get_html(url)
    mp4 = match1(html, 'var mp4url.+(http:.+?mp4)')
    listitem = xbmcgui.ListItem(name, iconImage=thumb, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    xbmc.Player().play(mp4, listitem)


def musiclist(params):
    name = params.get('name')
    url = params.get('url')

    html = get_html(url)
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
        html = get_html(url)
        tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('ul', {'class': 'singer_list clearfix'})
    li = soup[0].find_all('li')

    for item in li:
        url = item.a['href']
        url = URL_BASE + url
        itemp = item.p.text
        attr = 'album' if u'列表' in itemp else 'list'
        name = item.a['title']
        name = name + '(' + itemp + ')'
        image = item.img['lazy_src']
        u = sys.argv[0] + '?url=' + url + '&mode=%s&name='%attr + name
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def category():
    html = get_html(URL_BASE + '/category.htm')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'hotlist'})

    for hotlist in soup:
        item = xbmcgui.ListItem(BANNER_FMT % hotlist.h1.text)
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        x = hotlist.find_all('ul', {'class': 'clearfix'})
        li = x[0].find_all('li')

        for item in li:
            url = item.a['href']
            name = item.text
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

    html = get_html(url.replace(' ', '%20'))    # some singer name has ' '
    tree = BeautifulSoup(html, "html.parser")

    # ALBUM #######################################
    soup = tree.find_all('div', {'id': 'album'})
    li = soup[0].find_all('li')
    for album in li:
        image = album.find('div', {'class': 'cover'})
        image = image.img['src']
        name = album.find('span', {'class': 'name'})
        aurl = name.a['href']
        name = name.text.strip('\n')
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
        aurl = name.a['href']
        name = name.text.strip('\n')
        u = sys.argv[0] + '?url=' + aurl + '&mode=playmv&name=' + name
        u += "&thumb=%s" % image
        liz = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    # SONGS ###############################################
    aurl = 'http://www.kuwo.cn/artist/contentMusicsAjax'
    aurl += '?artistId=%s&pn=%d&rn=15' % (artistid, page)
    html = get_html(aurl)
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
            mid = mid[0]
            name = song.a.text
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

    html = get_html(url + '&prefix=%s&pn=%d' % (prefix, page))
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
        aurl = artist.a['href']
        name = re.compile('name=(.+)').findall(aurl)
        name = name[0]
        aurl = 'http://www.kuwo.cn' + aurl
        artistid = artist.find('div', {'class': 'artistnav'})['data-id']
        u = sys.argv[0] + '?url=' + aurl + '&mode=singeralbum&name=' + name
        u += "&page=0&artistId=%s" % artistid
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
    html = get_html('http://www.kuwo.cn/artist/index')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('dl', {'class': 'area'})

    for singer in soup:
        item = xbmcgui.ListItem(BANNER_FMT % singer.span.text)
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        li = singer.find_all('dd')

        for item in li:
            url = item.a['href']
            url = 'http://www.kuwo.cn' + url
            name = item.text.strip('\n')
            u = sys.argv[0] + '?url=' + url + '&mode=singers&name=' + name
            liz = xbmcgui.ListItem(name)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def single_album(params):
    name = params.get('name')
    url = params.get('url')

    html = get_html(url)
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
        mid = item.p.input['mid']
        name = item.a.text
        u = sys.argv[0] + '?url=' + mid + '&mode=play&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def sortitem(params):
    name = params.get('name')
    url = params.get('url')

    html = get_html(url)
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'music clearfix'})

    for item in soup:
        url = item.a['href']
        name = item.a['title']
        u = sys.argv[0] + '?url=' + url + '&mode=album1&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    soup = tree.find_all('div', {'class': 'page'})
    li = soup[0].find_all('a')

    for item in li:
        url = item['href']
        curr = item.get('class', '')
        if 'current' in curr:
            continue
        name = item.text
        u = sys.argv[0] + '?url=' + url + '&mode=sortitem&name=' + name
        liz = xbmcgui.ListItem(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def sortlist():
    html = get_html('http://www.kuwo.cn/album/')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'sdlist clearfix'})

    for sdlist in soup:
        item = xbmcgui.ListItem(BANNER_FMT % sdlist.h1.text)
        u = sys.argv[0]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, item, False)

        li = sdlist.find_all('li')

        for item in li:
            url = item.a['href']
            name = item.text
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
params = dict(urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'listRoot()',
    'category': 'category()',
    'singer': 'singerlist()',
    'sort': 'sortlist()',
    'singers': 'singergroup(params)',
    'singeralbum': 'singeralbum(params)',
    'sortitem': 'sortitem(params)',
    'album1': 'single_album(params)',
    'album': 'albumlist(params)',
    'list': 'musiclist(params)',
    'play': 'PlayMusic(params)',
    'playmv': 'PlayMV(params)'
}

exec(runlist[mode])
