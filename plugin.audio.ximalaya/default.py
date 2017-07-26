#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urlparse
import urllib
import re
import sys
import simplejson
from bs4 import BeautifulSoup
from common import get_html

########################################################################
# www.ximalaya.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')

stream_types = [
    {'itag': '1', 'container': 'm4a', 'bitrate': 'default'},
    {'itag': '2', 'container': 'm4a', 'bitrate': '32'},
    {'itag': '3', 'container': 'm4a', 'bitrate': '64'}
]

HOST_URL = 'http://www.ximalaya.com'

BANNER_FMT = '[COLOR gold][%s][/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'


def url_from_id(id, stream_id=2):
    api = HOST_URL + '/tracks/%s.json' % id
    json_data = simplejson.loads(get_html(api))
    if 'res' in json_data:
        if json_data['res'] is False:
            raise ValueError('Server reported id %s is invalid' % id)
    if 'is_paid' in json_data and json_data['is_paid']:
        if 'is_free' in json_data and not json_data['is_free']:
            raise ValueError('%s is paid item' % id)
    title = json_data.get('title')

    quality = ['play_path', 'play_path_32', 'play_path_64']
    url = json_data[quality[stream_id]]

    return url


def audio_from_url(url, stream_id=2):
    match = re.search(r'http://www\.ximalaya\.com/\d+/sound/(\d+)', url)
    if match:
        id = match.group(1)
        return url_from_id(id, stream_id=stream_id)


def audios_from_url(playlist_url, stream_id=2):
    if re.match(r'http://www\.ximalaya\.com/(\d+)/album/(\d+)', playlist_url):
        page_content = get_html(playlist_url)
        ids = re.compile(r'<li sound_id="(\d+)"').findall(page_content)
        urls = []
        for id in ids:
            try:
                url = url_from_id(id, stream_id=stream_id)
                urls += [url]
            except(ValueError):
                return None
        return urls


def ximalaya_download_playlist(url, stream_id=2):
    match_result = re.match(r'http://www\.ximalaya\.com/(\d+)/album/(\d+)', url)
    if not match_result:
        return None

    pages = []
    page_content = get_html(url)
    if page_content.find('<div class="pagingBar_wrapper"') == -1:
        pages.append(url)
    else:
        base_url = 'http://www.ximalaya.com/' + match_result.group(1) + '/album/' + match_result.group(2)
        html_str = '<a href=(\'|")\/' + match_result.group(1) + '\/album\/' + match_result.group(2) + '\?page='
        count = len(re.findall(html_str, page_content))
        for page_num in range(count):
            pages.append(base_url + '?page=' + str(page_num+1))
            print(pages[-1])
    for page in pages:
        ximalaya_download_page(page, stream_id=stream_id)


############################################################################
def PlayAudio(params):
    title = params['title']

    playlistA = xbmc.PlayList(1)
    playlist = xbmc.PlayList(0)
    playlist.clear()

    v_pos = int(title.split('.')[0])
    psize = playlistA.size()

    for x in range(v_pos, psize):
        p_item = playlistA.__getitem__(x)
        sound_id = p_item.getfilename(x)
        p_list = p_item.getdescription(x)
        li = p_item
        li.setInfo(type='Music', infoLabels={'Title': p_list})
        v_url = url_from_id(sound_id)

        playlist.add(v_url, li)
        if x == v_pos:
            xbmc.Player(0).play(playlist)


def PlayAlbum(params):
    url = params['url']
    order = params.get('order', 'asc')
    page = params.get('page', '1')
    pdata = {'page': page, 'order': order}
    data = urllib.urlencode(pdata)
    html = get_html(url + '?' + data)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'album_soundlist'})
    songs = soup[0].find_all('li')

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    firstId_in_url = songs[0]

    title = params.get('title', '0.0')
    begin_id = int(title.split('.')[0])

    for song in songs[begin_id:]:
        sound_id = song['sound_id']
        info = song.find('a', {'class': 'title'})
        title = info.text.strip()
        p_url = url_from_id(sound_id)
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Music', infoLabels={'Title': title})
        x = playlist.add(p_url, li)

    xbmc.Player().play(playlist, windowed=True)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


def mainMenu():
    html = get_html(HOST_URL + '/dq/all/')
    html = re.sub('\t|\r|\n', '', html)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'sort_list'})

    grp = soup[0].find_all('li')
    listing = []
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            continue
        cid = prog['cid']
        name = prog.text
        href = httphead(href)

        li = xbmcgui.ListItem(name)
        li.setInfo(type='Music', infoLabels={'Title': name})
        u = sys.argv[0] + '?url=' + href
        u += '&mode=sublist&name=' + name + '&cid=' + cid
	listing.append((u, li, True))

    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listing)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    name = params['name']
    url = params['url']
    cid = params['cid']

    name = re.sub('\t|\n|\r', '', name)
    li = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0]
    listing = [(u, li, False)]

    html = get_html(HOST_URL + '/dq/all/')
    tree = BeautifulSoup(html, 'html.parser')

    soup = tree.find_all('div', {'data-cache': cid})
    pages = soup[0].find_all('a')
    for page in pages:
        href = page['href']
        href = httphead(href)
        title = page['tid']
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=albumlist'
        u += '&title=' + title
	listing.append((u, li, True))

    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listing)
    xbmcplugin.setContent(int(sys.argv[1]), 'songs')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumList(params):
    url = params['url']
    title = params['title']
    li = xbmcgui.ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    listing = [(u, li, False)]

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'discoverAlbum_wrapper'})

    albums = soup[0].find_all('div', {'class', 'discoverAlbum_item'})
    for album in albums:
        href = album.a['href']
        p_thumb = album.img['src']
        title = album.img['alt']
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playlist' + '&title=' + title + '&thumb=' + p_thumb
        li = xbmcgui.ListItem(title,
                              iconImage=p_thumb, thumbnailImage=p_thumb)
	listing.append((u, li, True))

    soup = tree.find_all('div', {'class': 'pagingBar_wrapper'})
    try:
        pages = soup[0].find_all('a')
    except:
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), listing)
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    u = sys.argv[0]
    li = xbmcgui.ListItem(BANNER_FMT % '分页')
    listing.append((u, li, False))

    for page in pages:
        href = page['href']
        if href == 'javascript:;':
            continue
        page_num = page['data-page']
        title = page.text
        href = httphead(href)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=albumlist' + '&title=Page. ' + page_num
        li = xbmcgui.ListItem(title)
        listing.append((u, li, True))

    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listing)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playList(params):
    url = params['url']
    page = params.get('page', '1')
    order = params.get('order', 'asc')
    pdata = {'page': page, 'order': order}
    data = urllib.urlencode(pdata)
    html = get_html(url + '?' + data)
    tree = BeautifulSoup(html, 'html.parser')

    title = params['title']
    info = tree.find_all('div', {'class': 'rich_intro'})
    if info:
        info = info[0].article.text
    else:
        info = ''

    u = sys.argv[0] + '?url=' + url + '&mode=playlist&title=' + title
    u += '&page=' + page
    if order == 'asc':
        u += '&order=desc'
    else:
        u += '&order=asc'
    li = xbmcgui.ListItem(BANNER_FMT % (title + '(更改排序)'))
    li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('div', {'class': 'album_soundlist'})
    songs = soup[0].find_all('li')

    playlist = xbmc.PlayList(1)
    playlist.clear()

    number = 0
    for song in songs:
        sound_id = song['sound_id']
        info = song.find('a', {'class': 'title'})
        href = httphead(info['href'])
        p_title = info.text.strip()
        u = sys.argv[0] + '?url=' + url + '&mode=playaudio'
        u += '&order=' + order + '&page=' + page
        u += '&title=%d.%s' % (number, p_title) + '&sound_id=' + sound_id
        li = xbmcgui.ListItem(p_title)
        li.setInfo(type='Music', infoLabels={'Title': p_title})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        playlist.add(sound_id, li)
        number += 1

    # pagelist
    soup = tree.find_all('div', {'class': 'pagingBar_wrapper'})
    try:
        pages = soup[0].find_all('a')
        for page in pages:
            href = page['href']
            if 'javascript' in href:
                continue
            href = href.split('?')[0]
            href = httphead(href.encode('utf-8'))
            p_title = page.text.encode('utf-8')
            u = sys.argv[0] + '?url=' + href + '&mode=playlist&title=' + title
            u += '&order=' + order + '&page=' + p_title
            li = xbmcgui.ListItem(p_title)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    except:
        pass

    xbmcplugin.setContent(int(sys.argv[1]), 'songs')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'sublist': 'listSubMenu(params)',
    'albumlist': 'albumList(params)',
    'playlist': 'playList(params)',
    'playaudio': 'PlayAudio(params)',
    'playalbum': 'PlayAlbum(params)'
}

exec(runlist[mode])
