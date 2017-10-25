#!/usr/bin/python
#coding=utf-8

from xbmcswift2 import Plugin, xbmc, xbmcgui, ListItem
import time
import re
from random import choice
from urllib import quote_plus, urlencode
from qq import video_from_vid
from common import get_html
from iqiyi import video_from_url as iqiyi_url
from json import loads, dumps
from bs4 import BeautifulSoup

BANNER_FMT = '[COLOR gold]%s[/COLOR]'
BANNER_FMT2 = '[COLOR pink][%s][/COLOR]'

SITELIST = [
    'iqiyi.com', 'sohu.com', 'qq.com'
]

HOST = 'http://v.baidu.com'


plugin = Plugin()


def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        info = loads(kwargs['info'])
        page = str(int(page) - 1)
        info['pn'] = page
        info = dumps(info)
        kwargs['info'] = info
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        info = loads(kwargs['info'])
        page = str(int(page) + 1)
        info['pn'] = page
        info = dumps(info)
        kwargs['info'] = info
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
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
    return [{'label': title, 'path': plugin.url_for(endpoint, **kwargs)}]
    

def get_av_item(aid, **kwargs):
    result = bilibili.get_av_list(aid)
    item = dict(**kwargs)

    if len(result) == 1:
        vid = result[0].get('vid', '')
        item['is_playable'] = True
        if len(vid) > 0:
            item['label'] += '(QQ)'
        else:
            vid = '0'
        item['path'] = plugin.url_for('playmovie', cid=result[0]['cid'], vid=vid)
    else:
        item['path'] = plugin.url_for('list_video', aid=aid)
    return item


@plugin.route('/playmovie/<cid>/<vid>')
def playmovie(cid, vid='0'):
    if vid != '0':
        urls = video_from_vid(vid)
    else:
        urls = bilibili.get_video_urls(cid)

    stack_url = 'stack://' + ' , '.join(urls)
    danmu = plugin.addon.getSetting('danmu')

    playlist = xbmc.PlayList(1)
    playlist.clear()
    player = BiliPlayer()
    list_item = xbmcgui.ListItem(u'播放')
    playlist.add(stack_url, list_item)

    if danmu == 'true':
        bilibili.parse_subtitle(cid)
        player.setSubtitle(bilibili._get_tmp_dir() + '/tmp.ass')
    else:
        player.showSubtitles(False)
        player.show_subtitle = False

    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(1000)


@plugin.route('/list_video/<aid>')
def list_video(aid):
    plugin.set_content('videos')
    result = bilibili.get_av_list(aid)

    items = []
    for x in result:
        vid = x.get('vid', '')
        if len(vid) < 1:
            vid = '0'
        item = ListItem(**{
            'label': x['pagename'],
            'path': plugin.url_for('playmovie', cid=x['cid'], vid=vid)
        })
        item.set_info("video", {})
        item.set_is_playable(True)
        items.append(item)

    return items



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

@plugin.route('/video_list/<url>/<site>')
def video_list(url, site):
    html = get_html(url)
    match = re.search('<a href=\"(.+)\"', html)
    if match:
        match1 = match.group(1)
    else:
        return []
    if 'iqiyi.com' in match1:
        urls = iqiyi_url(match1)
        playurl = 'stack://' + ' , '.join(urls)
        print "PPPPPPPPPPPPPP",playurl
        xbmc.Player().play(playurl)



# 电影: /commonapi/movie2level/
# 电视剧: /commonapi/tvplay2level/
# 综艺: /commonapi/tvshow2level/
# 动漫: /commonapi/comic2level/
# 少儿 : /channel/commonapi/shaoer2level/  (channel)
@plugin.route('/channel_list/<url>/<info>')
def channel_list(url, info):
    api = HOST
    if url == 'shaoer':
        api += '/channel'
    api += '/commonapi/{}2level/?'.format(url)
    #'http://v.baidu.com/commonapi/movie2level/?channel=movie'
    req = loads(info)
    req['channel'] = url
    data = urlencode(encoded_dict(req))
    print "DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDd",data
    html = get_html(api + data)
    js = loads(html)
    videos = js['videoshow']['videos']
    page = req['pn']
    size = js['videoshow']['video_num']
    total = js['total_num']

    total_page = (total + size - 1) // size

    items = previous_page('channel_list', page, total_page, url=url, info=info)
    for video in videos:
        site_url = '0'
        for site in video['site']:
            if site['site_url'] == 'sohu.com':
                site_url = site['site_url']
                break
            if site['site_url'] == 'iqiyi.com':
                site_url = site['site_url']
                break
            if site['site_url'] == 'qq.com':
                site_url = site['site_url']
                break
        items.append({
            'label': video['title'],
            'path': plugin.url_for('video_list',
                                   url=video['url'],
                                  site=site_url),
            'thumbnail': video['imgh_url'],
            'icon': video['imgv_url'],
            'info': {
                'duration': video.get('duration'),
                'plot': video['intro']
            },
            'is_playable': True,
        })

    items += next_page('channel_list', page, total_page, url=url, info=info)

    filters = js['condition_order_list']['condition_list']
    for f in filters:
        items += [{'label': BANNER_FMT2 % f['name']}]
        areas = f['value']
        field = f['field']
        for a in areas:
            items += filter_list('channel_list', field, a, url=url, info=info)


    return items

@plugin.route('/')
def root():

    LIST = {'电影': 'movie', '电视剧': 'tvplay', '综艺': 'tvshow',
            '动漫': 'comic', '动画片': 'shaoer'}

    items = [{
        'label': item,
        'path': plugin.url_for('channel_list', url=LIST[item], info='{"pn":1}')
    } for item in LIST]

    return items


if __name__ == '__main__':
    plugin.run()
