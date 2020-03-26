#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon

from lib.bilibili import Bilibili
from lib.subtitle import subtitle_offset
from lib.bilivideo import video_from_vid
import sys
if sys.version[0]=='3':
    from urllib.parse import urlencode, quote_plus, parse_qsl
else:
    from urllib import urlencode, quote_plus
    from urlparse import parse_qsl

import time
import re
from qq import video_from_vid as video_from_qq
from common import get_html
from json import loads

bilibili = Bilibili()

__assfile__   = xbmc.translatePath("special://temp/tmp.ass")

class BiliPlayer(xbmc.Player):
    def __init__(self):
        self.subtitle = ''
        self.show_subtitle = False

    def setSubtitle(self, subtitle):
        if len(subtitle) > 0:
            self.show_subtitle = True
            self.subtitle = subtitle
        else:
            self.show_subtitle = False
            self.subtitle = ''

    def onPlayBackStarted(self):
        time = float(self.getTime())
        if self.show_subtitle:
            if time > 1:
                self.setSubtitles(subtitle_offset(self.subtitle, -time))
            else:
                self.setSubtitles(self.subtitle)
        else:
            self.showSubtitles(False)

player = BiliPlayer()

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        li = ListItem('上一页 - {0}/{1}'.format(page, str(total_page)))
        filter = kwargs['filter']
        filter = dict(parse_qsl(filter))
        kwargs.update(filter)
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) - 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        li = ListItem('下一页 - {0}/{1}'.format(page, str(total_page)))
        filter = kwargs['filter']
        filter = dict(parse_qsl(filter))
        kwargs.update(filter)
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) + 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
        addDirectoryItem(int(sys.argv[1]), u, li, True)


def playvideo(params):
    name = params['name']
    vid = params['vid']
    cid = params['cid']
    level = int(xbmcaddon.Addon().getSetting('resolution'))

    if vid != '0':
        urls = video_from_qq(vid, level=level)
    else:
        urls = video_from_vid(cid, level=level)

    stack_url = 'stack://' + ' , '.join(urls)
    danmu = xbmcaddon.Addon().getSetting('danmu')

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    list_item = ListItem(name)
    if danmu == 'true':
        bilibili.parse_subtitle(cid)
        player.setSubtitle(__assfile__)

    playlist.add(stack_url, list_item)
    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(500)


def list_video(params):
    aid = params['aid']
    result = bilibili.get_av_list(aid)

    for x in result:
        vid = x.get('vid', '')
        if len(vid) < 1:
            vid = '0'

        li = ListItem(x['pagename'])
        li.setInfo(type='Video', infoLabels={'title': x['pagename']})
        req = {
            'mode': 'playvideo',
            'cid': x['cid'],
            'vid': vid,
            'name': x['pagename'].encode('utf-8')
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def search(params):
    keyboard = xbmc.Keyboard('', '请输入关键字 (片名/AV)')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return 
    keyword = keyboard.getText()
    search_api = 'https://search.bilibili.com/all?keyword={}&from_source=nav_search'

    html = get_html(search_api.format(quote_plus(keyword)))
    data = re.search('__INITIAL_STATE__\s*=\s*({.+?\});', html)
    jsdata = loads(data.group(1))

    key = 'getMixinFlowList-jump-keyword-' + keyword.decode('utf-8')
    lists = jsdata['flow'][key]['result']

    for x in lists:
        for y in x['data']:
            title = y.get('title')
            if title is None: continue
            title = title.replace('<em class="keyword">', '[COLOR FFDEB887]')
            title = title.replace('</em>', '[/COLOR]')
            cover = y.get('cover')
            if cover is None:
                cover = y.get('pic', '')
            if cover[0:2] == '//': cover = 'https:' + cover 

            link = y.get('goto_url')
            if link is None:
                link = y.get('url')
            if link is None:
                link = y.get('arcurl')
            if link is None: continue
            type = y.get('season_type_name')
            if type is None:
                type = y.get('typename', '')
            type = '(' + type + ')'
            aid = y.get('aid')
            li = ListItem(title + type, thumbnailImage=cover)
            if aid:
                li.setInfo(type='Video',
                           infoLabels={'title':title, 'plot': y.get('description')})
                req = {
                    'mode': 'list_video',
                    'aid': aid
                }
                u = sys.argv[0] + '?' + urlencode(req)
                addDirectoryItem(int(sys.argv[1]), u, li, False)
            else:
                li.setInfo(type='Video',
                           infoLabels={'title':title, 'plot': y.get('desc')})
                req = {
                    'mode': 'season',
                    'link': link
                }
                u = sys.argv[0] + '?' + urlencode(req)
                addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def season(params):
    link = params['link']
    html = get_html(link)
    data = re.search('__INITIAL_STATE__\s*=\s*({.+?\});', html)
    jsdata = loads(data.group(1))
    
    info = jsdata['mediaInfo']
    title = info['title']
    desc = info['evaluate']

    li = ListItem('[COLOR FFDEB887]%s[/COLOR]' % title)
    li.setInfo(type='Video', infoLabels={'title': title, 'plot':desc})
    u = sys.argv[0]
    addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in jsdata['epList']:
        title = item.get('titleFormat')
        if title is None: title = item.get('title')
        cover = item['cover']
        if cover[0:2] == '//': cover = 'https:' + cover
        cid = item['cid']
        vid = item['vid']
        if vid == '': vid = 0
        title = title.encode('utf-8')
        li = ListItem(title, thumbnailImage=cover)
        li.setInfo(type='Video',
                   infoLabels={'title': title, 'plot': item['longTitle']})
        req = {
            'mode': 'playvideo',
            'cid': cid,
            'vid': vid,
            'name': title,
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def select(params):
    url = 'https://www.bilibili.com/{}/index/'
    html = get_html(url.format(params['name']))
    data = re.search('__INITIAL_STATE__\s*=\s*({.+?\});', html)
    jsdata = loads(data.group(1))

    filters = {}
    dialog = Dialog()
    for x in jsdata['filters']:
        title = x['title']
        key = x['key']
        lst = [y['name'] for y in x['list']]
        item = [y['value'] for y in x['list']]

        sel = dialog.select(title, lst)
        if sel >=0: filters[key] = item[sel]

    filters['name'] = params['name']
    filters['page'] = 1
    category(filters)


def category(params):
    name = params['name']
    page = params['page']
    li = ListItem('[COLOR yellow][筛选过滤][/COLOR]')
    req = {
        'mode': 'select',
        'name': name
    }
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    type = {'movie': 2, 'tv':5, 'documentary': 3}
    req = params
    del (req['name'])
    req['season_type'] = type[name]
    req['pagesize'] = 20
    req['type'] = 1    # unknow function, but required
    filter = urlencode(req)
    api = 'https://api.bilibili.com/pgc/season/index/result?'
    html = get_html(api + filter)
    data = loads(html)

    total= int(data['data']['total'])
    total_page = (total + 19) // 20

    previous_page('category', page, total_page, name=name, filter=filter)
    for item in data['data']['list']:
        title = item['title']
        extra = item['index_show']
        badge = item.get('badge')
        if badge:
            badge = u'[COLOR magenta]({})[/COLOR]'.format(badge)
        else:
            badge = ''
        li = ListItem(title + '(' + extra + ')' + badge)
        req = {
            'mode': 'season',
            'link': item['link'],
            'thumbnail': item['cover']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    next_page('category', page, total_page, name=name, filter=filter)
    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def root():
    CATEGORY = {'电影': 'movie', '电视剧': 'tv', '纪录片': 'documentary'}
    li = ListItem('[COLOR magenta][搜索][/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    for item in CATEGORY:
        li = ListItem(item)
        req = {
            'mode': 'category',
            'name': CATEGORY[item],
            'page': 1,
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)
    endOfDirectory(int(sys.argv[1]))

# main programs goes here #########################################
runlist = {
    'category': 'category(params)',
    'season': 'season(params)',
    'search': 'search(params)',
    'select': 'select(params)',
    'list_video': 'list_video(params)',
    'playvideo': 'playvideo(params)'
}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
if mode:
    del (params['mode'])
    exec(runlist[mode])
else:
    root()
