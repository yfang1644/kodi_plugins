#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import urlparse
import re
import sys
import gzip
import StringIO
import simplejson
from bs4 import BeautifulSoup

########################################################################
# www.ximalaya.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')

UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

stream_types = [
    {'itag': '1', 'container': 'm4a', 'bitrate': 'default'},
    {'itag': '2', 'container': 'm4a', 'bitrate': '32'},
    {'itag': '3', 'container': 'm4a', 'bitrate': '64'}
]

LIST_URL = 'http://www.ximalaya.com'

BANNER_FMT = '[COLOR FFDEB887][%s][/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'


def match1(text, *patterns):
    if len(patterns) == 1:
        pattern = patterns[0]
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ret.append(match.group(1))
        return ret


def ximalaya_download_by_id(id, stream_id):
    api = 'http://www.ximalaya.com/tracks/%s.json' % id
    json_data = simplejson.loads(getHttpData(api))
    if 'res' in json_data:
        if json_data['res'] is False:
            raise ValueError('Server reported id %s is invalid' % id)
    if 'is_paid' in json_data and json_data['is_paid']:
        if 'is_free' in json_data and not json_data['is_free']:
            raise ValueError('%s is paid item' % id)
    if 'title' in json_data:
        title = json_data['title']

    size = 0
    url = json_data['play_path_64']
    if stream_id:
        if stream_id == 1:
            url = json_data['play_path_32']
        elif stream_id == 0:
            url = json_data['play_path']

    ext = 'm4a'
    return [url]


def ximalaya_download(url):
    if re.match(r'http://www\.ximalaya\.com/(\d+)/sound/(\d+)', url):
        id = match1(url, r'http://www\.ximalaya\.com/\d+/sound/(\d+)')
    else:
        return []
    return ximalaya_download_by_id(id, stream_id=1)


def ximalaya_download_page(playlist_url, stream_id=1):
    if re.match(r'http://www\.ximalaya\.com/(\d+)/album/(\d+)', playlist_url):
        page_content = get_content(playlist_url)
        pattern = re.compile(r'<li sound_id="(\d+)"')
        ids = pattern.findall(page_content)
        for id in ids:
            try:
                ximalaya_download_by_id(id, stream_id=1)
            except(ValueError):
                return None
    else:
        return None


def ximalaya_download_playlist(url, stream_id=1):
    match_result = re.match(r'http://www\.ximalaya\.com/(\d+)/album/(\d+)', url)
    if not match_result:
        return None

    pages = []
    page_content = getHttpData(url)
    if page_content.find('<div class="pagingBar_wrapper"') == -1:
        pages.append(url)
    else:
        base_url = 'http://www.ximalaya.com/' + match_result.group(1) + '/album/' + match_result.group(2)
        html_str = '<a href=(\'|")\/' + match_result.group(1) + '\/album\/' + match_result.group(2) + '\?page='
        count = len(re.findall(html_str, page_content))
        for page_num in range(count):
            pages.append(base_url + '?page=' +str(page_num+1))
            print(pages[-1])
    for page in pages:
        ximalaya_download_page(page, stream_id=1)


############################################################################
def PlayAudio(params):
    url = params['url']
    title = params['title']

    urls = ximalaya_download(url)

    ulen = len(urls)
    if ulen > 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        playlist.clear()
        for i in range(ulen):
            listitem = xbmcgui.ListItem(title)
            playlist.add(urls[i], listitem)

        xbmc.Player().play(playlist)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def getHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()
        if response.headers.get('content-encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    except:
        print 'GetHttpData Error: %s' % url
        return ''

    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    charset = ''
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')

    return httpdata


def mainMenu():
    html = getHttpData('http://www.ximalaya.com/dq/all/')
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'sort_list'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            break
        cid = prog['cid']
        name = prog.text
        href = httphead(href)

        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=sublist&name=' + name + '&cid=' + cid
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    name = params['name']
    url = params['url']
    cid = params['cid']

    html = getHttpData('http://www.ximalaya.com/dq/all/')
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
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'songs')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumList(params):
    url = params['url']
    html = getHttpData(url)
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
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('div', {'class': 'pagingBar_wrapper'})
    pages = soup[0].find_all('a')

    for page in pages:
        href = page['href']
        try:
            title = page['data-page']
        except:
            continue
        if title not in href:
            continue
        href = httphead(href)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=albumlist' + '&title=' + title
        li = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playList(params):
    url = params['url']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'album_soundlist'})

    songs = soup[0].find_all('li')

    for song in songs:
        info = song.find('a', {'class': 'title'})
        href = httphead(info['href'])
        title = info.text
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playaudio' + '&title=' + title
        li = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'songs')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'sublist': 'listSubMenu(params)',
    'albumlist': 'albumList(params)',
    'playlist': 'playList(params)',
    'playaudio': 'PlayAudio(params)'
}

exec(runlist[mode])
