# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from urllib import urlencode
import urllib2
from json import load

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
    response = urllib2.urlopen(req, timeout=15)
    info = load(response)
    return info

@plugin.route('/list_in_channel/<channel_id>')
def list_in_channel(channel_id):
    plugin.set_content('music')

    songAPI = HOST + 'playlist'
    req = {
        'kbps': 128,
        'channel': channel_id,
        'app_name': 'radio_website',
        'version': 100,
        'type': 'n'
    }
    data = urlencode(req)
    items = []
    cnt = 0
    while (True):
        results = GetInfo(songAPI + '?' + data)
        song = results.get('song', [])
        if len(song) > 0:
            song = song[0]
            items += [{
                'label': song['title'],
                'path': song['url'],
                'thumbnail': song['picture'],
                'icon': song['singers'][0]['avatar'],
                'is_playable': True,
                'info': {'title': song['title'], 'duration': song['length']}
            }]
            cnt += 1
        if cnt >= 20:
            break

    return items


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
    plugin.set_content('music')
    playlistAPI = HOST + 'songlist/{}/?kbps=128'
    results = GetInfo(playlistAPI.format(albumid))

    items = [{
        'label': item['title'],
        'thumbnail': item['picture'],
        'icon': results['cover'],
        'is_playable': True,
        'path': item['url'],
        'info': {
            'title': item['title'],
            'duration': item['length'],
            'genre': results['title'],
            'artist': item['artist'],
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
            'title': item['title'].encode('utf-8'),
            'plot': item['description'],
            'genre': LIST[int(cid)],
            'artist': '',
            'duration': item['duration'],
        }
    } for item in results]
    return items
    

@plugin.route('/')
def root():

#    MAINLIST = {'scenario': '心情/场景', 'language': '语言',
#                'artist': '艺术家', 'track': '单曲',
#                'brand':'天猫理想生活','genre': '风格/流派'}
#    rootAPI = HOST + 'rec_channels?specific=all'
#    results = GetInfo(rootAPI)
#
#    channels = results['data']['channels']
#    items = []
#    for labels in MAINLIST
#        for x in channels[labels]:
#            items.append({
#                'label': x['name'],
#                'path': plugin.url_for('list_in_channel', channel_id=x['id']),
#                'thumbnail': x['banner'],
#                'info': {'plot': x['intro']}
#            })
#
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
