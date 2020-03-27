#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from common import get_html, r1
from json import loads
import random

HOST = 'https://www.huya.com/'
playurl = 'https://al.hls.huya.com/huyalive'
BANNER = '[COLOR FFDEB887]{0}[/COLOR]'

category = [
    {BANNER.format('全部'): 0},
    {BANNER.format('全部电影'): 2067},
    {'  喜剧电影': 2069 },
    {'  动作电影': 2071 },
    {'  惊悚电影': 2073 },
    {'  科幻电影': 2075 },
    {'  古装电影': 2077 },
    {BANNER.format('全部电视剧'): 2079},
    {'  古装电视剧': 2081},
    {'  军旅电视剧': 2083},
    {'  搞笑电视剧': 2085},
    {'  悬疑电视剧': 2087},
    {'  都市电视剧': 2089},
    {'综艺': 1011     },
    {'原创': 987      },
    {'正能量': 1223   }
]

cateAPI = HOST + 'cache.php?m=LiveList&do=getTmpLiveByPage&gameId=2135&tmpId={0}&page={1}'
listAPI = HOST + 'cache.php?m=LiveList&do=getLiveListByPage&gameId=2135&page={0}'

plugin = Plugin()
url_for = plugin.url_for

@plugin.route('/playvideo/<room>/')
def playvideo(room):
    url = HOST + room
    html = get_html(url)
    json_stream = r1('"stream": ({.+?})\s*};', html)
    assert json_stream, "live video is offline"
    data = loads(json_stream)
    assert data['status'] == 200, data['msg']

    room_info = data['data'][0]['gameLiveInfo']

    stream_info = random.choice(data['data'][0]['gameStreamInfoList'])
    sHlsUrl = stream_info['sHlsUrl']
    sStreamName = stream_info['sStreamName']
    sHlsUrlSuffix = stream_info['sHlsUrlSuffix']
    sHlsAntiCode = stream_info['sHlsAntiCode']
    hls_url = u'{0}/{1}.{2}?{3}'.format(sHlsUrl, sStreamName, sHlsUrlSuffix, sHlsAntiCode)

    plugin.set_resolved_url(hls_url)


@plugin.route('/categorylist/<dataid>/<page>/')
def categorylist(dataid, page):
    plugin.set_content('TVShows')
    api = listAPI.format(page) if dataid=='0' else cateAPI.format(dataid, page)
    html = get_html(api)
    data = loads(html)
    rooms = data['data']['datas']
    items = []

    for item in rooms:
        #vurl = re.sub('http.+?/huyalive', playurl, screenshot)
        #url = re.sub('/[^\/]*.jpg', '.m3u8', vurl)
        blueray = item.get('isBluRay')
        title = item['nick'] + (u'(蓝光)' if int(blueray) else '')
        items.append({
            'label': title,
            'path': url_for('playvideo', room=item['profileRoom']),
            'thumbnail': item['screenshot'],
            'is_playable': True,
            'info': {'title': title, 'plot': item['introduction']}
        })

    thispage = int(data['data']['page'])
    pages = int(data['data']['totalPage'])
    for x in range(pages):
        if x+1 == thispage: continue
        items.append({
            'label': '第{0}页'.format(x+1),
            'path': url_for('categorylist', dataid=dataid, page=x+1)
        })
    return items


@plugin.route('/')
def index():
    for dic in category:
        c = list(dic.items())
        yield {
            'label': c[0][0],
            'path': url_for('categorylist', dataid=c[0][1], page=1)
        }


if __name__ == '__main__':
    plugin.run()
