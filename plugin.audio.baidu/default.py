# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from json import loads
from bs4 import BeautifulSoup
import re
from common import get_html
from iqiyi import video_from_vid as IQIYI_from_vid
from yinyuetai import video_from_vid as YINYUETAI_from_vid

plugin = Plugin()
url_for = plugin.url_for

HOST = 'http://music.baidu.com'
BANNER_FMT = '[COLOR gold][%s][/COLOR]'


def pageList(tree, endpoint):
    pages = tree.find_all('a', {'class': 'page-navigator-number'})
    items = [{
        'label': page.text.strip(),
        'path': url_for(endpoint, url=page['href'].encode('utf-8'))
        } for page in pages]

    return items

@plugin.route('/stay')
def stay():
    pass

@plugin.route('/playMV/<source>/<tvid>/<vid>/<mvid>/<url>')
def playMV(source, tvid, vid, mvid, url):
    if source == 'iqiyi':
        urls = IQIYI_from_vid(tvid, vid)

    elif source == 'yinyuetai':
        match = re.search('yinyuetai.com.*/(\d+)', url)
        urls = YINYUETAI_from_vid(match.group(1))

    url = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(url)

@plugin.route('/MVList/<url>')
def MVList(url):
    if url[0] == '/':
        url = HOST + url
    page = get_html(url)
    songs= re.findall('data.push\((.+)\)', page)
    items = []

    for str_item in songs:
        item = loads(str_item)
        songId = item['songId']
        albumId = item['albumId']
        albumTitle = item['albumTitle']
        author = item['author']
        authorId = item['authorId']
        tvid = item['tvid']
        vid = item['vid']
        mvid = item['mvid']
        file_link = item.get('file_link')
        if file_link is None:
            file_link = ''

        items.append({
            'label': item['title'],
            'path': url_for('playMV',
                            source=item['source'],
                            tvid='0' if tvid == '' else tvid,
                            vid='0' if vid == '' else vid,
                            mvid='0' if mvid == '' else mvid,
                            url=file_link),
            'info': {'title': item['title'], 'duration': item['time']},
            'is_playable': True
        })

    return items


@plugin.route('/musiclist/<url>')
def musiclist(url):
    url = url.strip()
    if url[0] == '/':
        url = HOST + url

    page = get_html(url, decoded=True)
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('li', {'class': 'mv-item'})

    items = [{
        'label': item.a['title'],
        'thumbnail': item.img['org_src'],
        'path': url_for('MVList', url=item.a['href']),
    } for item in soup]

    items += pageList(tree, 'musiclist')

    return items


@plugin.route('/mv')
def mv():
    page = get_html(HOST + '/mv/ml')
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('ul', {'class': 'clearfix'})

    items = []
    for soup in soups:
        p = soup.find_all('li')
        for item in p:
            items.append({
                'label': item.text.strip(),
                'path': url_for('musiclist', url=item.a['href'])
            })

    return items

@plugin.route('/playBD/<sid>')
def playBD(sid):
    data = loads(get_html(
        HOST + '/data/music/fmlink?songIds=%s' % sid
        ))['data']

    if data['xcode'] != '':        # inside china mainland
        url = data['songList'][0]['songLink']
        plugin.set_resolved_url(url)


@plugin.route('/taglist/<url>')
def taglist(url):
    if url[0] == '/':
        url = HOST + url

    page = get_html(url, decoded=False)
    tree = BeautifulSoup(page, 'html.parser')
    soups= tree.find_all('span', {'class': 'music-icon-hook'})
    
    items = []

    for item in soups:
        js = loads(item['data-musicicon'])
        try:
            playable = item.a['data-action']
            title = js['songTitle']
        except:
            playable = False
            title = js['songTitle'] + u'(该歌曲已下架)' 

        albumId = js['albumId']
        items.append({
            'label': title,
            'path': url_for('playBD', sid=js['id']),
            'is_playable': True if playable else False,
            'info': {'title': js['songTitle']}
        })

    items += pageList(tree, 'taglist')
    return items

@plugin.route('/tag')
def tag():
    page = get_html(HOST + '/tag')
    tree = BeautifulSoup(page, 'html.parser')
    items = []
    soups = tree.find_all('dl', {'class': 'tag-mod'})

    for soup in soups:
	items += [{'label': BANNER_FMT % soup.dt.text, 'path': url_for('stay')}]
        p = soup.find_all('span', {'class': 'tag-list clearfix'})
        for item in p:
            items.append({
                'label': item.text.strip(),
                'path': url_for('taglist', url=item.a['href'])
            })

    return items

@plugin.route('/artistAlbum/<url>')
def artistAlbum(url):
    if url[0] == '/':
        url = HOST + url

    page = get_html(url, decoded=False)
    tree = BeautifulSoup(page, 'html.parser')
    pages = tree.find_all('div', {'class': 'page-inner'})
    
    items = []

    # songs
    items += [{'label': '单曲', 'path': url_for('stay')}]
    soup1 = tree.find_all('div', {'class': 'song-list-wrap'})
    soups = soup1[0].find_all('span', {'class': 'music-icon-hook'})
    for item in soups:
        js = loads(item['data-musicicon'])
        albumId = js['albumId']
        
        items.append({
            'label': js['songTitle'],
            'path': url_for('playBD', sid=js['id']),
            'is_playable': True,
            'info': {'title': js['songTitle']}
        })

    items += pageList(pages[0], 'artistAlbum')

    # albums
    items += [{'label': '专辑', 'path': url_for('stay')}]
    soup2 = tree.find_all('div', {'class': 'album-list-wrap'})
    soups = soup2[0].find_all('div', {'class': 'album-cover'})
    for item in soups:
        js = loads(item['data-albumdata'])
        items.append({
            'label': js['albumTitle'],
            'thumbnail': js['albumPic'],
            'path': url_for('taglist', url='/album/'+js['id']),
        })

    items += pageList(pages[1], 'artistAlbum')

    # mvs
    items += [{'label': 'MV', 'path': url_for('stay')}]
    soup3 = tree.find_all('div', {'class': 'mv-list-wrap'})
    soups = soup3[0].find_all('li', {'class': 'mv-item'})
    for item in soups:
        items.append({
            'label': item.a['title'],
            'thumbnail': item.img['org_src'],
            'path': url_for('MVList', url=item.a['href']),
        })
    items += pageList(pages[2], 'artistAlbum')
    return items


@plugin.route('/artistName/<url>')
def artistName(url):
    if url[0] == '/':
        url = HOST + url

    page = get_html(url)
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('ul', {'class': 'clearfix'})
    items = []
    for soup in soups:
        p = soup.find_all('li')
        for item in p:
            try:
                items.append({
                    'label': item.text.strip(),
                    'path': url_for('artistAlbum', url=item.a['href'])
                })
            except:
                pass

    return items

@plugin.route('/artist')
def artist():
    page = get_html(HOST + '/artist')
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('dl', {'class': 'tree_main'})
    
    items = []
    for soup in soups:
        p = soup.find_all('dd')
        for item in p:
            items.append({
                'label': item.text.strip(),
                'path': url_for('artistName', url=item.a['href'])
            })

    return items

@plugin.route('/albumlist/<url>')
def albumlist(url):
    if url[0] == '/':
        url = HOST + url

    page = get_html(url)
    tree = BeautifulSoup(page, 'html.parser')
    soup= tree.find_all('div', {'class': 'songlist-list'})
    soups = soup[0].find_all('li')
    items = []

    for item in soups:
        c = item.find_all('p', {'class': 'text-title'})
        items.append({
            'label': c[0].text,
            'path': url_for('taglist', url=c[0].a['href']),
            'thumbnail': item.img['src'],
        })

    items += pageList(tree, 'albumlist')
    return items



@plugin.route('/songlist')
def songlist():
    page = get_html(HOST + '/songlist')
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('div', {'class': 'songlist-tag'})
    soups = soup[0].find_all('dl')

    items = []
    for soup in soups:
	items += [{'label': BANNER_FMT % soup.dt.text, 'path': url_for('stay')}]
	p = soup.find_all('dd')
	for item in p:
            items.append({
                'label': item.text.strip(),
                'path': url_for('albumlist', url=item.a['href'].encode('utf-8'))
            })

    return items


@plugin.route('/')
def root():
    mainlist = {
        '歌单': 'songlist',
        '歌手': 'artist',
        '分类': 'tag',
        'MV': 'mv'}

    items = [{
        'label': item,
        'path': url_for(mainlist[item]),
    } for item in mainlist]

    return items

if __name__ == '__main__':
    plugin.run()
