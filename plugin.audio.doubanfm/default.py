# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, ListItem
from urllib import urlencode
from json import loads
from common import get_html


LIST = ['为你推荐', '最热', '流行', '摇滚', '民谣', '原声',
        '轻音乐', '古典', '电子', '华语', '欧美', '日语',
        '粤语', '独立', '动漫', '新世纪', '中国摇滚', 'R&B']

plugin = Plugin()


@plugin.route('/play/<url>')
def play(url):
    plugin.set_content('videos')
    plugin.set_resolved_url(url)


@plugin.route('/albumlist/<albumid>')
def albumlist(albumid):
    playlistAPI = 'https://douban.fm/j/v2/songlist/{}/?kbps=128'
    results = loads(get_html(playlistAPI.format(albumid)))

    items = [{
        'label': item['title'],
        'thumbnail': item['picture'],
        'icon': results['cover'],
        'is_playable': True,
        'path': plugin.url_for(play, url=item['url']),
        'info': {
            'duration': item['length'],
            'plot': results['description']
        }
    } for item in results['songs']]
    return items


@plugin.route('/catalog/<cid>')
def catalog(cid):
    albumAPI = 'https://douban.fm/j/v2/songlist/explore'

    req = {
        'type': 'hot',
        'limit': 500,          # assume max count
        'sample_cnt': 1,
        'genre': cid
    }
    data = urlencode(req)
    results = loads(get_html(albumAPI + '?' + data))

    items = [{
        'label': item['title'].encode('utf-8'),
        'path': plugin.url_for('albumlist', albumid=item['id']),
        'thumbnail': item['creator']['picture'],
        'icon': item['cover'],
        'info': {
            'plot': item['description'],
            'genre': LIST[int(cid)],
            'duration': item['duration']
        }
    } for item in results]
    return items
    

@plugin.route('/')
def root():
    items = [{
            'label': title,
            'path': plugin.url_for('catalog', cid=i),
        } for (i, title) in enumerate(LIST)]

    return items

if __name__ == '__main__':
    plugin.run()
