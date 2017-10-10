# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, ListItem
from urllib import urlencode
import urllib2
from json import load
from common import get_html


LIST = ['为你推荐', '最热', '流行', '摇滚', '民谣', '原声',
        '轻音乐', '古典', '电子', '华语', '欧美', '日语',
        '粤语', '独立', '动漫', '新世纪', '中国摇滚', 'R&B']

__UserAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2'
# songAPI = 'https://douban.fm/j/mine/playlist?type=n&from=mainsite&channel='

plugin = Plugin()
HOST = 'https://douban.fm/j/v2/'

def GetInfo(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', __UserAgent)
    response = urllib2.urlopen(req)
    info = load(response)
    return info

@plugin.route('/play/<url>')
def play(url):
    plugin.set_content('episode')
    plugin.set_resolved_url(url)


@plugin.route('/list_in_channel/<channel_id>')
def list_in_channel(channel_id):
    songAPI = HOST + 'playlist'
    req = {
        'kbps': 128,
        'channel': channel_id,
        'app_name': 'radio_website',
        'version': 100,
        'type': 'n'
    }
    data = urlencode(req)
    results = GetInfo(songAPI + '?' + data)
    song = results.get('song', [])
    if len(song) > 0:
        song = song[0]
        print song
        item = {
            'label': song['title'],
            'path': plugin.url_for('play', url=song['url']),
            'thumbnail': song['picture'],
            'icon': song['singers'][0]['avatar'],
            'is_playable': True,
            'info': {'duration': song['length']}
        }
        return [item]
    else:
        return []


@plugin.route('/channels')
def channels():
    channelurl = 'http://www.douban.com/j/app/radio/channels'
    results = GetInfo(channelurl)

    items = [{
        'label': item['name'],
        'path': plugin.url_for('list_in_channel', channel_id=item['channel_id'])
    } for item in results['channels']]
    return items


@plugin.route('/albumlist/<albumid>')
def albumlist(albumid):
    playlistAPI = HOST + 'songlist/{}/?kbps=128'
    results = GetInfo(playlistAPI.format(albumid))

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
    albumAPI = HOST + 'songlist/explore'

    req = {
        'type': 'hot',
        'limit': 500,          # assume max count
        'sample_cnt': 1,
        'genre': cid
    }
    data = urlencode(req)
    results = GetInfo(albumAPI + '?' + data)

    items = [{
        'label': item['title'].encode('utf-8'),
        'path': plugin.url_for('albumlist', albumid=item['id']),
        'icon': item['creator']['picture'],
        'thumbnail': item['cover'],
        'info': {
            'plot': item['description'],
            'genre': LIST[int(cid)],
            'duration': item['duration']
        }
    } for item in results]
    return items
    

@plugin.route('/')
def root():
    items = [{'label': '频道列表',
              'path': plugin.url_for('channels'),
             }]
    items += [{
        'label': title,
        'path': plugin.url_for('catalog', cid=i),
    } for (i, title) in enumerate(LIST)]

    return items

if __name__ == '__main__':
    plugin.run()
