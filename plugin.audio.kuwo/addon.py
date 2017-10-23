#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
import re
from bs4 import BeautifulSoup
from common import get_html, r1

# Plugin constants

URL_BASE = 'http://yinyue.kuwo.cn'
BANNER_FMT = '[COLOR gold][%s][/COLOR]'
musicAPI = 'http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_'
sourceAPI = 'http://antiserver.kuwo.cn/anti.s?type=convert_url&response=url'

plugin = Plugin()

@plugin.route('/stay')
def stay():
    pass

@plugin.route('/musiclist/<url>')
def musiclist(url):
    plugin.set_content('music')
    supported_stream_types = ['aac', 'wma', 'mp3']
    if url.startswith('/'):
        url = URL_BASE + url
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('li', {'class': 'clearfix'})

    musicList = []
    mvList = []
    for music in soup:
        mid = music.input['mid']
        song = music.find_all('p', {'class': ['m_name','a_name','video']})
        title = song[0].a.text
        albumname = song[1].a.text

        html = get_html(musicAPI + mid)
        iconimage = r1('<artist_pic240>(.*)</artist_pic240>', html)
        artist = r1('<artist>(.*)</artist>', html)

        for t in supported_stream_types:
            url = get_html(sourceAPI + '&format={}&rid=MUSIC_{}'.format(t, mid))
            if url:
                musicList.append({
                    'label': title +'-'+ albumname,
                    'path': url,
                    'thumbnail': iconimage,
                    'is_playable': True,
                    'info': {'title': title, 'artist': artist}
                })
                break

        if song[2].a is not None:
            html = get_html(mv.a['href'])
            mp4 = r1('var mp4url.+(http:.+?mp4)', html)
            mvList.append({
                'label': title +'-'+ albumname,
                'path': mp4,
                'is_playable': True,
                'thumbnail': iconimage,
                'info': {'title': title, 'artist': artist}
            })

    if len(musicList) > 0:
        musicList.insert(0, {
            'label': BANNER_FMT % u'音乐',
            'path': plugin.url_for('stay')
        })

    if len(mvList) > 0:
        mvList.insert(0, {
            'label': BANNER_FMT % u'MV',
            'path': plugin.url_for('stay')
        })

    return musicList + mvList

@plugin.route('/albumlist/<url>')
def albumlist(url):
    html = get_html(URL_BASE + url)
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('ul', {'class': 'singer_list clearfix'})
    li = soup[0].find_all('li')

    for item in li:
        itemp = item.p.text
        attr = 'albumlist' if u'列表' in itemp else 'musiclist'
        name = item.a['title']
        name = name + '(' + itemp + ')'
        yield {
            'label': name,
            'path': plugin.url_for(attr, url=item.a['href']),
            'thumbnail': item.img['lazy_src']
        }

@plugin.route('/singeralbum/<url>/<id>/<page>')
def singeralbum(url, id, page):
    plugin.set_content('music')
    SINGER = 'http://www.kuwo.cn'
    page = int(page)

    yield {
        'label': BANNER_FMT % u'专辑',
        'path': plugin.url_for('stay')
    }

    html = get_html(SINGER + url.replace(' ', '%20')) # some singer name has ' '
    tree = BeautifulSoup(html, "html.parser")

    # ALBUM #######################################
    soup = tree.find_all('div', {'id': 'album'})
    li = soup[0].find_all('li')
    for album in li:
        name = album.find('span', {'class': 'name'})
        thumb = album.find('div', {'class': 'cover'})
        image = thumb.img['src']
        yield {
            'label': name.text.strip(),
            'path': plugin.url_for('musiclist', url=name.a['href']),
            'thumbnail': str(image)   # why is unicode not string??
        }

    # MV ###############################################
    soup = tree.find_all('div', {'id': 'mv'})
    li = soup[0].find_all('li')
    yield {
        'label': BANNER_FMT % u'MV',
        'path': plugin.url_for('stay')
    }
    for mv in li:
        name = mv.find('span', {'class': 'name'})
        html = get_html(name.a['href'])
        mp4 = r1('var mp4url.+(http:.+?mp4)', html)
        image = mv.find('div', {'class': 'cover'})
        image = image.img['src']
        yield {
            'label': name.text.strip(),
            'path': mp4,
            'is_playable': True,
            'thumbnail': str(image),
            'info': {'title': name.text.strip()}
        }

    # SONGS ###############################################
    yield {
        'label': BANNER_FMT % u'单曲',
        'path': plugin.url_for('stay')
    }
    aurl = 'http://www.kuwo.cn/artist/contentMusicsAjax'
    aurl += '?artistId=%s&pn=%d&rn=15' % (id, page)
    html = get_html(aurl)
    l = re.compile('"id":"MUSIC_(\d+)').findall(html)
    maxpage = re.compile('data-page="(\d+)"').findall(html)
    maxpage = int(maxpage[0])

    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('li', {'class': 'onLine'})

    if page > 0:
        yield {
            'label': BANNER_FMT % u'上一页',
            'path': plugin.url_for('singeralbum', url=url, id=id, page=page-1)
        }

    for song in soup:
        mid = re.compile('\d+').findall(song.a['href'])
        mid = mid[0]
        html = get_html(musicAPI + mid)
        iconimage = r1('<artist_pic240>(.*)</artist_pic240>', html)
        artist = r1('<artist>(.*)</artist>', html)

        for t in ['aac', 'wma', 'mp3']:
            url = get_html(sourceAPI + '&format={}&rid=MUSIC_{}'.format(t, mid))
            if url:
                break
        yield {
            'label': song.a.text,
            'path': url,
            'thumbnail': iconimage,
            'is_playable': True,
            'info': {'title': song.a.text, 'artist': artist}
        }

    if page < maxpage:
        yield {
            'label': BANNER_FMT % u'下一页',
            'path': plugin.url_for('singeralbum', url=url, id=id, page=page+1)
        }

@plugin.route('/singergroup/<url>/<page>/<letter>')
def singergroup(url, page, letter):
    SINGER = 'http://www.kuwo.cn'
    page = int(page)
    cletter = letter if letter != '0' else ''
    html = get_html(SINGER + url + cletter + '&pn='.format(page))
    # pn=page number, prefix=alphabet, initial singer name
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'artistTop'})

    if page > 0:
        yield {
            'label': BANNER_FMT % u'上一页',
            'path': plugin.url_for('singergroup', url=url, page=page-1, letter=letter)
        }

    for artist in soup:
        aurl = artist.a['href'].encode('utf-8')
        name = re.compile('name=(.+)').findall(aurl)
        name = name[0]
        artistid = artist.find('div', {'class': 'artistnav'})['data-id']
        yield {
            'label': name,
            'path': plugin.url_for('singeralbum', url=aurl, id=artistid, page=0),
            'thumbnail': artist.img['src']
        }

    soup = tree.find('div', {'class': 'page'})
    maxpage = int(soup['data-page'])
    if page < maxpage:
        yield {
            'label': BANNER_FMT % u'下一页',
            'path': plugin.url_for('singergroup', url=url, page=page+1, letter=letter)
        }

    for abc in range(0x41, 0x5B):   # A--Z
        yield {
            'label': chr(abc),
            'path': plugin.url_for('singergroup', url=url, page=page, letter=chr(abc))
        }

@plugin.route('/singerlist')
def singerlist():
    html = get_html('http://www.kuwo.cn/artist/index')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('dl', {'class': 'area'})

    for singer in soup:
        yield {
            'label': BANNER_FMT % singer.span.text,
            'path': plugin.url_for('stay')
        }
        li = singer.find_all('dd')
        for item in li:
            url = item.a['href'].encode('utf-8')
            yield {
                'label': item.text.strip(),
                'path': plugin.url_for('singergroup', url=url, page=0, letter='0')
            }

@plugin.route('/sortitem/<url>')
def sortitem(url):
    html = get_html(url)
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'music clearfix'})

    for item in soup:
        yield {
            'label': item.a['title'],
            'path': plugin.url_for('musiclist', url=item.a['href']),
            'thumbnail': item.img['lazy_src']
        }

    soup = tree.find_all('div', {'class': 'page'})
    li = soup[0].find_all('a')

    for item in li:
        url = item['href']
        curr = item.get('class', '')
        if 'current' in curr:
            continue
        yield {
            'label': item.text,
            'path': plugin.url_for('sortitem', url=item['href'])
        }

@plugin.route('/sortlist')
def sortlist():
    html = get_html('http://www.kuwo.cn/album/')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'sdlist clearfix'})

    for sdlist in soup:
        yield {
            'label': BANNER_FMT % sdlist.h1.text,
            'path': plugin.url_for('stay')
        }
        li = sdlist.find_all('li')

        for item in li:
            yield {
                'label': item.text,
                'path': plugin.url_for('sortitem', url=item.a['href'])
            }

@plugin.route('/category')
def category():
    html = get_html(URL_BASE + '/category.htm')
    tree = BeautifulSoup(html, "html.parser")
    soup = tree.find_all('div', {'class': 'hotlist'})

    for hotlist in soup:
        yield {
            'label': BANNER_FMT % hotlist.h1.text,
            'path': plugin.url_for('stay')
        }
        x = hotlist.find_all('ul', {'class': 'clearfix'})
        li = x[0].find_all('li')

        for item in li:
            yield {
                'label': item.text,
                'path': plugin.url_for('albumlist', url=item.a['href'])
            }

@plugin.route('/')
def root():
    LIST = {u'分类': 'category', u'歌手': 'singerlist', u'专辑': 'sortlist'}
    for item in LIST:
        yield {'label': item, 'path': plugin.url_for(LIST[item])}

if __name__ == '__main__':
    plugin.run()
