#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from common import get_html
from json import loads
import re

HOST = 'https://www.huya.com'
playurl = 'http://aldirect.hls.huya.com/huyalive'
category = [
    {'全部': 0},
    #{'全部电影': 2067,}
    {'喜剧电影': 2069 },
    {'动作电影': 2071 },
    {'惊悚电影': 2073 },
    {'科幻电影': 2075 },
    {'古装电影': 2077 },
    #{'全部电视剧': 2079},
    {'古装电视剧': 2081},
    {'军旅电视剧': 2083},
    {'搞笑电视剧': 2085},
    {'悬疑电视剧': 2087},
    {'都市电视剧': 2087},
    {'综艺': 1011     },
    {'原创': 987      },
    {'正能量': 1223   }
]

cateAPI = HOST + '/cache.php?m=LiveList&do=getTmpLiveByPage&gameId=2135&tmpId=%s'
listAPI = HOST + '/cache.php?m=LiveList&do=getLiveListByPage&gameId=2135&page=%s'
BANNER_FMT = '[COLOR gold][%s][/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

@plugin.route('/playvideo/<url>/')
def playvideo(url):

    plugin.set_resolved_url(url)


@plugin.route('/listpages/<page>/')
def listpages(page):
    plugin.set_content('TVShows')
    html = get_html(listAPI%page)
    data = loads(html)
    rooms = data['data']['datas']
    items = []

    for item in rooms:
        screenshot = item['screenshot']
        vurl = re.sub('http.+?/huyalive', playurl, screenshot)
        url = re.sub('/[^\/]*.jpg', '.m3u8', vurl)
        homepage = HOST + '/' + item['profileRoom']
        items.append({
            'label': item['nick'],
            'path': url_for('playvideo', url=url),
            'thumbnail': screenshot,
            'is_playable': True,
            'info': {'title': item['nick'], 'plot': item['introduction']}
        })

    pages = int(data['data']['totalPage'])
    for x in range(pages):
        items.append({
            'label': '第{}页'.format(x+1),
            'path': url_for('listpages', page=x+1)
        })
    return items


@plugin.route('/categorylist/<dataid>/')
def categorylist(dataid):
    plugin.set_content('TVShows')
    html = get_html(cateAPI%dataid)
    data = loads(html)
    rooms = data['data']['datas']

    items = []
    for item in rooms:
        screenshot = item['screenshot']
        vurl = re.sub('http.+?/huyalive', playurl, screenshot)
        url = re.sub('/[^\/]*.jpg', '.m3u8', vurl)
        homepage = HOST + '/' + item['profileRoom']
        items.append({
            'label': item['nick'],
            'path': url_for('playvideo', url=url),
            'thumbnail': screenshot,
            'is_playable': True,
            'info': {'title': item['nick'], 'plot': item['introduction']}
        })
    return items


@plugin.route('/')
def index():

    yield {
        'label': '全部',
        'path': url_for('listpages', page=1)
    }
    for dic in category[1:]:
        c = (dic.items())
        yield {
            'label': c[0][0],
            'path': url_for('categorylist', dataid=c[0][1])
        }


if __name__ == '__main__':
    plugin.run()
