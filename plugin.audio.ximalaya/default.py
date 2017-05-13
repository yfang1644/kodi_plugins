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

HOST_URL = 'http://www.ximalaya.com'

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


def url_from_id(id, stream_id=2):
    api = HOST_URL + '/tracks/%s.json' % id
    json_data = simplejson.loads(getHttpData(api))
    if 'res' in json_data:
        if json_data['res'] is False:
            raise ValueError('Server reported id %s is invalid' % id)
    if 'is_paid' in json_data and json_data['is_paid']:
        if 'is_free' in json_data and not json_data['is_free']:
            raise ValueError('%s is paid item' % id)
    if 'title' in json_data:
        title = json_data['title']

    if stream_id == 2:
        url = json_data['play_path_64']
    elif stream_id == 1:
        url = json_data['play_path_32']
    elif stream_id == 0:
        url = json_data['play_path']

    return url


def audio_from_url(url, stream_id=2):
    match = re.search(r'http://www\.ximalaya\.com/\d+/sound/(\d+)', url)
    if match:
        id = match.group(1)
        return url_from_id(id, stream_id=stream_id)
    else:
        return []


def audios_from_url(playlist_url, stream_id=2):
    if re.match(r'http://www\.ximalaya\.com/(\d+)/album/(\d+)', playlist_url):
        page_content = getHttpData(playlist_url)
        pattern = re.compile(r'<li sound_id="(\d+)"')
        ids = pattern.findall(page_content)
        urls = []
        for id in ids:
            try:
                url = url_from_id(id, stream_id=stream_id)
                urls += url
            except(ValueError):
                return None
        return urls
    else:
        return None


def ximalaya_download_playlist(url, stream_id=2):
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
            pages.append(base_url + '?page=' + str(page_num+1))
            print(pages[-1])
    for page in pages:
        ximalaya_download_page(page, stream_id=stream_id)


############################################################################
def PlayAudio(params):
    sound_id = params['sound_id']
    title = params['title']

    url = url_from_id(sound_id)

    if url:
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Music', infoLabels={'Title': title})
        xbmc.Player().play(url, li)


def PlayAlbum(params):
    url = params['url']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'album_soundlist'})
    songs = soup[0].find_all('li')

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    firstId_in_url = songs[0]
    begin_id = params.get('begin', '0')

    begin_id = int(begin_id)
    print '---------------------'
    for song in songs[begin_id:]:
        sound_id = song['sound_id']
        info = song.find('a', {'class': 'title'})
        title = info.text.strip()
        p_url = url_from_id(sound_id)
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Music', infoLabels={'Title': title})
        x = playlist.add(p_url, li)
        print x

    xbmc.Player().play(playlist, windowed=True)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

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
    html = getHttpData(HOST_URL + '/dq/all/')
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

    name = re.sub('\t|\n|\r', '', name)
    li = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    html = getHttpData(HOST_URL + '/dq/all/')
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
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'songs')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumList(params):
    url = params['url']
    title = params['title']
    li = xbmcgui.ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

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
    try:
        pages = soup[0].find_all('a')
    except:
        xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    u = sys.argv[0]
    li = xbmcgui.ListItem(BANNER_FMT % '分页')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

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
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playList(params):
    url = params['url']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    title = params['title']
    info = tree.find_all('div', {'class': 'rich_intro'})
    info = info[0].article.text
    u = sys.argv[0] + '?url=' + url + '&mode=playalbum&begin=0'
    li = xbmcgui.ListItem(BANNER_FMT % (title + '(播放全部专辑)'))
    li.setInfo(type='Music', infoLabels={'Title': title, 'Plot': info})
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('div', {'class': 'album_soundlist'})
    songs = soup[0].find_all('li')

    number = 0
    for song in songs:
        sound_id = song['sound_id']
        info = song.find('a', {'class': 'title'})
        href = httphead(info['href'])
        title = info.text.strip()
        u = sys.argv[0] + '?url=' + url
        u += '&mode=playalbum&begin=' + str(number)
        u += '&title=' + title + '&sound_id=' + sound_id
        li = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        number += 1

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
    'playaudio': 'PlayAudio(params)',
    'playalbum': 'PlayAlbum(params)'
}

exec(runlist[mode])
