# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from urllib import quote_plus
import urllib2
from json import loads
from common import get_html
from iqiyi import video_from_vid as IQIYI_from_vid
from yinyuetai import video_from_vid as YINYUETAI_from_vid
from bs4 import BeautifulSoup
import re

__UserAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2'
# songAPI = 'https://douban.fm/j/mine/playlist?type=n&from=mainsite&channel='

plugin = Plugin()
HOST = 'http://music.baidu.com'

def pageList(tree, endpoint):
    items = []
    pages = tree.find_all('a', {'class': 'page-navigator-number'})
    for page in pages:
        title = page.text
        url = page['href'].encode('utf-8')
        url = re.sub(' |\t', '', url)

        items.append({
            'label': title,
            'path': plugin.url_for(endpoint, url=quote_plus(url))
        })

    return items


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
            'path': plugin.url_for('playMV',
                                   source=item['source'],
                                   tvid='0' if tvid == '' else tvid,
                                   vid='0' if vid == '' else vid,
                                   mvid='0' if mvid == '' else mvid,
                                   url=file_link),
            'info': {'duration': item['time']},
            'is_playable': True
        })

    return items


@plugin.route('/musiclist/<url>')
def musiclist(url):
    if url[0] == '/':
        url = HOST + url

    page = get_html(url, decoded=True)
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('li', {'class': 'mv-item'})

    items = []
    for item in soup:
        items.append({
            'label': item.a['title'],
            'thumbnail': item.img['org_src'],
            'path': plugin.url_for('MVList', url=item.a['href']),
        })

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
                'label': item.text,
                'path': plugin.url_for('musiclist', url=item.a['href'])
            })

    return items

@plugin.route('/playBD/<sid>')
def playBD(sid):
    data = loads(get_html(
        'http://music.baidu.com/data/music/fmlink?songIds=%s' % sid
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
        albumId = js['albumId']
        
        items.append({
            'label': js['songTitle'],
            'path': plugin.url_for('playBD', sid=js['id']),
            'is_playable': True
        })

    items += pageList(tree, 'taglist')
    return items

@plugin.route('/tag')
def tag():
    page = get_html(HOST + '/tag')
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('dd', {'class': 'tag-items clearfix'})

    items = []
    for soup in soups:
        p = soup.find_all('span', {'class': 'tag-list clearfix'})
        for item in p:
            items.append({
                'label': item.text,
                'path': plugin.url_for('taglist', url=item.a['href'])
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
    items += [{'label': '单曲'}] 
    soup1 = tree.find_all('div', {'class': 'song-list-wrap'})
    soups = soup1[0].find_all('span', {'class': 'music-icon-hook'})
    for item in soups:
        js = loads(item['data-musicicon'])
        albumId = js['albumId']
        
        items.append({
            'label': js['songTitle'],
            'path': plugin.url_for('playBD', sid=js['id']),
            'is_playable': True
        })

    items += pageList(pages[0], 'artistAlbum')

    # albums
    items += [{'label': '专辑'}]
    soup2 = tree.find_all('div', {'class': 'album-list-wrap'})
    soups = soup2[0].find_all('div', {'class': 'album-cover'})
    for item in soups:
        js = loads(item['data-albumdata'])
        items.append({
            'label': js['albumTitle'],
            'thumbnail': js['albumPic'],
            'path': plugin.url_for('taglist', url='/album/'+js['id']),
        })

    items += pageList(pages[1], 'artistAlbum')

    # mvs
    items += [{'label': 'MV'}]
    soup3 = tree.find_all('div', {'class': 'mv-list-wrap'})
    soups = soup3[0].find_all('li', {'class': 'mv-item'})
    for item in soups:
        items.append({
            'label': item.a['title'],
            'thumbnail': item.img['org_src'],
            'path': plugin.url_for('MVList', url=item.a['href']),
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
                    'label': item.text,
                    'path': plugin.url_for('artistAlbum', url=item.a['href'])
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
                'label': item.text,
                'path': plugin.url_for('artistName', url=item.a['href'])
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
            'path': plugin.url_for('MVList', url=c[0].a['href']),
            'thumbnail': item.img['src'],
        })

    items += pageList(tree, 'albumlist')
    return items



@plugin.route('/songlist')
def songlist():
    page = get_html(HOST + '/songlist', decoded=True) 
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('div', {'class': 'songlist-tag'})
    soups = soup[0].find_all('dd')

    print soups
    items = []
    for item in soups:
        u = item.a['href'].encode('utf-8')
        items.append({
            'label': item.text,
            'path': plugin.url_for('albumlist', url=u)
        })

    return items


@plugin.route('/')
def root():
    list = {'歌单': 'songlist', 'MV': 'mv', '分类': 'tag', '歌手': 'artist'}
    LIST = {
        '歌单': 'songlist',
        '歌手': 'artist',
        '分类': 'tag',
        'MV': 'mv'}

    items = [{
        'label': item,
        'path': plugin.url_for(list[item]),
    } for item in list]

    return items

if __name__ == '__main__':
    plugin.run()
