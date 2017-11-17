#!/usr/bin/python
#coding=utf-8

from xbmcswift2 import Plugin, xbmc, ListItem
import re
from urllib import quote_plus, unquote_plus, urlencode
from common import get_html

from iqiyi import IQiyi
from qq import QQ
from youku import Youku
from pptv import PPTV
from sohu import Sohu
from funshion import Funshion
from letv import LeTV
from mgtv import MGTV

from json import loads, dumps
from bs4 import BeautifulSoup

BANNER_FMT = '[COLOR gold]%s[/COLOR]'
BANNER_FMT2 = '[COLOR pink][%s][/COLOR]'

HOST = 'http://v.baidu.com'

plugin = Plugin()
url_for = plugin.url_for

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        info = loads(kwargs['info'])
        page = str(int(page) - 1)
        info['pn'] = page
        info = dumps(info)
        kwargs['info'] = info
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        info = loads(kwargs['info'])
        page = str(int(page) + 1)
        info['pn'] = page
        info = dumps(info)
        kwargs['info'] = info
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict


def filter_list(endpoint, field, a, **kwargs):
    info = loads(kwargs['info'])
    title = info.get(field)
    if title == a:
        title = BANNER_FMT % title
    else:
        title = a

    if a == u'全部':
        info[field] = ''
    else:
        info[field] = a

    info = dumps(info)
    kwargs['info'] = info
    return [{'label': title, 'path': url_for(endpoint, **kwargs)}]
    

    req = {
        'filter': 'false',
        'type': '',               # 类型
        'area': '',               # 地区
        'actor': '',              # 演员
        'start': '',              # 年代
        'complete': '',           # 正片/花絮
        'order': '',              # hot/pubtime/rating
        'pn': '1',
        'rating': '',
        'prop': '',               # 版本 (动漫)
        'channel': 'movie'
    }

    return[]


@plugin.route('/play/<link>/<title>')
def play(link, title):
    if link[0] == '/':
        link = HOST + link
    page = get_html(link)
    playurl = re.compile('a href="(http.+?)\"').findall(page)[0]

    if 'sohu.com' in playurl:
        site = Sohu()
    elif 'qq.com' in playurl:
        site = QQ()
    elif 'iqiyi.com' in playurl:
        site = IQiyi()
    elif 'fun.tv' in playurl:
        site = Funshion()
    elif 'youku.com' in playurl:
        site = Youku()
    elif 'mgtv.com' in playurl:
        site = MGTV()
    else:
        pass

    urls = site.video_from_url(playurl)
    stackurl = 'stack://' + ' , '.join(urls)
    li = ListItem(title, path=stackurl)
    li.set_info('video', {'title': title})
    plugin.set_resolved_url(li)


@plugin.route('/tvshowlist/<id>')
def tvshowlist(id):
    api = HOST + '/show_intro/?'
    req = {
        'dtype': 'tvshowPlayUrl',
        'id': id,
        'service': 'json',
        'e': 1,
    }
    data = urlencode(req)
    series = loads(get_html(api + data))

    items = []
    for x in series:
        try:
            content = x['episodes']
        except:
            continue
        for item in content:
            items.append({
                'label': item['single_title'] + '--' + item['episode'],
                'path': url_for('play',
                                link=item['url'],
                                title=item['single_title'].encode('utf-8')),
                'thumbnail': item['thumbnail'],
                'is_playable': True,
                'info': {'title': item['single_title'],
                         'plot': '\n'.join(item['guest'])},
            })

    return items
    pass


@plugin.route('/comiclist/<id>')
def comiclist(id):
    api = HOST + '/comic_intro/?'
    req = {
        'dtype': 'comicplayUrl',
        'id': id,
        'service': 'json',
        'e':1
    }
    data = urlencode(req)
    series = loads(get_html(api + data))
    items = []
    for x in series:
        try:
            content = x['episodes']
        except:
            continue
        for item in content:
            items.append({
                'label': item['single_title'] + '--' + item['episode'],
                'path': url_for('play',
                                link=item['url'],
                                title=item['single_title'].encode('utf-8')),
                'thumbnail': item['thumbnail'],
                'is_playable': True,
                'info': {'title': item['single_title']}
            })

    return items

@plugin.route('/shortplay/<url>')
def shortplay(url):
    html = get_html(url)
    link = re.compile('var flashUrl.*video=(http.+?)\'').findall(html)[0]
    link = unquote_plus(link)
    plugin.set_resolved_url(link)


@plugin.route('/channellist/<url>/<info>')
def channellist(url, info):
    plugin.set_content('videos')
    req = loads(info)
    page = req['pn']
    #'http://v.baidu.com/channel/amuse?format=json&pn=1'
    api = HOST + '/' + url + '?format=json&pn=' + str(page)
    print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",api
    html = get_html(api)
    data = loads(html)['data']
    videos = data['videos']
    size = data['video_num']
    total = data['total_num']
    total_page = (total + size - 1) // size

    items = previous_page('channellist', page, total_page, url=url, info=info)

    for item in videos:
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration * 60 + int(t)
        items.append({
            'label': item['title'],
            'path': url_for('shortplay', url=item['url']),
            'thumbnail': item['imgv_url'],
            'is_playable': True,
            'info': {'title': item['title'], 'duration': duration}
        })
    items += next_page('channellist', page, total_page, url=url, info=info)

    return items


@plugin.route('/movielist/<id>')
def movielist(id):
    api = HOST + '/movie_intro/?'
    req = {
        'dtype': 'playUrl',
        'id': id,
        'service': 'json',
        'frp': 'browse',
    }
    data = urlencode(req)
    movie = loads(get_html(api + data))
    link = movie[0]['link']
    play(link, 'XX')


@plugin.route('/episodelist/<id>')
def episodelist(id):
    api = HOST + '/tv_intro/?'
    req = {
        'dtype': 'tvEpisodeIntro',
        'id': id,
        'service': 'json',
    }
    data = urlencode(req)
    series = loads(get_html(api + data))

    items = []
    for x in series:
        for item in x['intro']:
            items.append({
                'label': item['subtitle'],
                'path': url_for('play',
                                link=item['url'],
                                title=item['subtitle'].encode('utf-8')),
                'is_playable': True,
                'info': {'title': item['subtitle'], 'plot': item['intro']},
            })

    return items


# 电影: /commonapi/movie2level/
# 电视剧: /commonapi/tvplay2level/
# 综艺: /commonapi/tvshow2level/
# 动漫: /commonapi/comic2level/
# 少儿 : /channel/commonapi/shaoer2level/  (channel)
@plugin.route('/mainlist/<url>/<info>/<func>')
def mainlist(url, info, func):
    plugin.set_content('videos')
    api = HOST
    if 'channel' in url:
        api += '/channel'

    url = url.replace('channel/', '')
    api += '/commonapi/{}2level/?'.format(url)
    #'http://v.baidu.com/commonapi/movie2level/?channel=movie'
    #'http://v.baidu.com/channel/amuse?format=json&pn=1'
    req = loads(info)
    req['channel'] = url
    data = urlencode(encoded_dict(req))
    html = get_html(api + data)
    js = loads(html)
    videos = js['videoshow']['videos']
    page = req['pn']
    size = js['videoshow']['video_num']
    total = js['total_num']

    total_page = (total + size - 1) // size

    items = previous_page('mainlist', page, total_page, url=url, info=info,func=func)
    for video in videos:
        isPlay = True if func in ('movielist', 'funnylist') else False

        preview = '' if video.get('isplay', 1) else u'(预)'
        items.append({
            'label': video['title'] + preview,
            'path': url_for(func, id=video['id']),
            'thumbnail': video['imgh_url'],
            'icon': video['imgv_url'],
            'is_playable': isPlay,
            'info': {
                'title': video['title'],
                'duration': video.get('duration'),
                'plot': video['intro']
            },
        })

    items += next_page('mainlist', page, total_page, url=url, info=info,func=func)

    filters = js['condition_order_list']['condition_list']
    for f in filters:
        items += [{'label': BANNER_FMT2 % f['name']}]
        areas = f['value']
        field = f['field']
        for a in areas:
            items += filter_list('mainlist', field, a, url=url, info=info,func=func)

    return items


@plugin.route('/')
def root():

    LIST = [(u'电影', 'movie', 'movielist'),
            (u'电视剧', 'tvplay', 'episodelist'),
            (u'综艺', 'tvshow', 'tvshowlist'),
            (u'动漫', 'comic', 'comiclist'),
            (u'动画片', 'channel/shaoer', 'comiclist')]
    items = []
    for item in LIST:
        items.append({
            'label': item[0],
            'path': url_for('mainlist',
                            url=item[1],
                            info='{"pn":1}',
                            func=item[2])

        })

    LIST = [(u'搞笑', 'channel/amuse'),
            (u'娱乐', 'channel/star')]
    for item in LIST:
        items.append({
            'label': item[0],
            'path': url_for('channellist', url=item[1], info='{"pn":1}')
        })

    return items


if __name__ == '__main__':
    plugin.run()
