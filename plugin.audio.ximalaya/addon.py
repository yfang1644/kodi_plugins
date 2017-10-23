#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcaddon
import re
from json import loads
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

plugin = Plugin()

def url_from_id(id, stream_id=2):
    api = HOST_URL + '/tracks/%s.json' % id
    json_data = loads(get_html(api))
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

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


@plugin.route('/')
def root():
    plugin.set_content('music')
    html = get_html(HOST_URL + '/dq/all/')
    html = re.sub('\t|\r|\n', '', html)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'sort_list'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            continue
        cid = prog['cid']
        name = prog.text
        href = httphead(href)
        yield {
            'label': prog.text,
            'path': plugin.url_for('sublist', cid=prog['cid'])
        }

@plugin.route('/sublist/<cid>')
def sublist(cid):
    plugin.set_content('music')
    html = get_html(HOST_URL + '/dq/all/')
    tree = BeautifulSoup(html, 'html.parser')

    soup = tree.find_all('div', {'data-cache': cid})
    pages = soup[0].find_all('a')
    for page in pages:
        url = httphead(page['href'].encode('utf-8'))
        yield {
            'label': page['tid'],
            'path': plugin.url_for('albumlist', url=url)
        }

@plugin.route('/albumlist/<url>')
def albumlist(url):
    plugin.set_content('music')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'discoverAlbum_wrapper'})

    albums = soup[0].find_all('div', {'class', 'discoverAlbum_item'})
    for album in albums:
        yield {
            'label': album.img['alt'],
            'thumbnail': album.img['src'],
            'path': plugin.url_for('playList', url=album.a['href'], page=1, order='asc')
        }

    soup = tree.find_all('div', {'class': 'pagingBar_wrapper'})
    try:
        pages = soup[0].find_all('a')
    except:
        return

    for page in pages:
        url = page['href']
        if url == 'javascript:;':
            continue
        yield {
            'label': page.text,
            'path': plugin.url_for('albumlist', url=httphead(url.encode('utf-8')))
        }


@plugin.route('/playList/<url>/<page>/<order>')
def playList(url, page, order):
    plugin.set_content('music')
    html = get_html(url + '?page={}&order={}'.format(page, order))
    tree = BeautifulSoup(html, 'html.parser')

    info = tree.find_all('div', {'class': 'rich_intro'})
    if info:
        info = info[0].article.text
    else:
        info = ''

    if order == 'asc':
        corder = 'desc'
    else:
        corder = 'asc'
    yield {
        'label': u'更改排序',
        'path': plugin.url_for('playList', url=url, page=page, order=corder),
        'info': {'plot': info}
    }

    soup = tree.find_all('div', {'class': 'album_soundlist'})
    songs = soup[0].find_all('li')

    for song in songs:
        api = HOST_URL + '/tracks/%s.json' % song['sound_id']
        json_data = loads(get_html(api))

        yield {
            'label': json_data.get('title'),
            'path': json_data.get('play_path_64'),
            'thumbnail': json_data.get('cover_url'),
            'is_playable': True,
            'info': {
                'title': json_data.get('title'),
                'duration': json_data.get('duration'),
                'plot': json_data.get('intro')
            }
        }

    # pagelist
    soup = tree.find_all('div', {'class': 'pagingBar_wrapper'})
    try:
        pages = soup[0].find_all('a')
        for pagen in pages:
            url = pagen['href']
            if 'javascript' in url:
                continue
            url = url.split('?')[0]
            url = httphead(url.encode('utf-8'))
            yield {
                'label': pagen.text.encode('utf-8'),
                'path': plugin.url_for('playList', url=url, page=page, order=order)
            }
    except:
        pass

# main programs goes here #########################################
if __name__ == '__main__':
    plugin.run()
