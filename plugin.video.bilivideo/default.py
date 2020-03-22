#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcgui
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

plugin = Plugin()
url_for = plugin.url_for

bilibili = Bilibili()

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
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def get_av_item(aid, **kwargs):
    result = bilibili.get_av_list(aid)
    if not result:
        return {'label': '(空)', 'path': plugin.url_for('stay')}

    item = dict(**kwargs)
    if len(result) == 1:
        vid = result[0].get('vid', '')
        #item['icon'] = kwargs.get('thumbnail')
        item['is_playable'] = True
        if len(vid) > 0:
            item['label'] += '(QQ)'
        else:
            vid = '0'
        item['path'] = plugin.url_for('playvideo', cid=result[0]['cid'], vid=vid, name=item['label'].encode('utf-8'))
        item['info'] = {'title': item['label']}
    else:
        item['path'] = plugin.url_for('list_video', aid=aid)
    return item


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/playvideo/<cid>/<vid>/<name>/')
def playvideo(cid, vid, name):
    level = int(plugin.addon.getSetting('resolution'))
    if vid != '0':
        urls = video_from_qq(vid, level=level)
    else:
        urls = video_from_vid(cid, level=level)

    stack_url = 'stack://' + ' , '.join(urls)
    danmu = plugin.addon.getSetting('danmu')

    playlist = xbmc.PlayList(1)
    playlist.clear()
    list_item = xbmcgui.ListItem(name)
    if danmu == 'true':
        bilibili.parse_subtitle(cid)
        player.setSubtitle(bilibili._get_tmp_dir() + '/tmp.ass')

    playlist.add(stack_url, list_item)
    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(500)

    #   plugin.set_resolved_url(stack_url)

@plugin.route('/list_video/<aid>/')
def list_video(aid):
    plugin.set_content('TVShows')
    result = bilibili.get_av_list(aid)

    items = []
    for x in result:
        vid = x.get('vid', '')
        if len(vid) < 1:
            vid = '0'
        items.append({
            'label': x['pagename'],
            'path': plugin.url_for('playvideo', cid=x['cid'], vid=vid, name=x['pagename'].encode('utf-8')),
            'is_playable': True,
            'info': {'title': x['pagename'], 'type':'video'}
        })

    return items


@plugin.route('/search')
def search():
    plugin.set_content('TVShows')
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

    items = []
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
            if aid:
                items.append({
                    'label': title + type,
                    'path': url_for('list_video', aid=aid),
                    'thumbnail': cover,
                    'info': {'title': title, 'plot': y.get('description')}
                })
            else:
                items.append({
                    'label': title + type,
                    'path': url_for('season', link=link),
                    'thumbnail': cover,
                    'info': {'title': title, 'plot': y.get('desc')}
                })

    return items


@plugin.route('/season/<link>/')
def season(link):
    plugin.set_content('TVShows')
    html = get_html(link)
    data = re.search('__INITIAL_STATE__\s*=\s*({.+?\});', html)
    jsdata = loads(data.group(1))
    
    info = jsdata['mediaInfo']
    title = info['title']
    desc = info['evaluate']

    items = [{
        'label': '[COLOR FFDEB887]%s[/COLOR]' % title,
        'path': url_for('stay'),
        'info': {'title': title, 'plot': desc}
    }]
    for item in jsdata['epList']:
        title = item.get('titleFormat')
        if title is None: title = item.get('title')
        cover = item['cover']
        if cover[0:2] == '//': cover = 'https:' + cover
        cid = item['cid']
        vid = item['vid']
        if vid == '': vid = 0
        title = title.encode('utf-8')
        items.append({
            'label': title,
            'path': plugin.url_for('playvideo', cid=cid, vid=vid, name=title),
            'thumbnail': cover,
            'is_playable': True,
            'info': {'title': title, 'plot': item['longTitle']}
        })

    return items


@plugin.route('/select/<name>/')
def select(name):
    url = 'https://www.bilibili.com/{}/index/'
    html = get_html(url.format(name))
    data = re.search('__INITIAL_STATE__\s*=\s*({.+?\});', html)
    jsdata = loads(data.group(1))

    filters = {}
    dialog = xbmcgui.Dialog()
    for x in jsdata['filters']:
        title = x['title']
        key = x['key']
        lst = [y['name'] for y in x['list']]
        item = [y['value'] for y in x['list']]

        sel = dialog.select(title, lst)
        if sel >=0: filters[key] = item[sel]

    return category(name, page=1, filter=urlencode(filters))


@plugin.route('/category/<name>/<page>/<filter>/')
def category(name, page, filter):
    plugin.set_content('TVShows')
    type = {'movie': 2, 'tv':5, 'documentary': 3}
    req = dict(parse_qsl(filter))
    req['page'] = page
    req['season_type'] = type[name]
    req['pagesize'] = 20
    req['type'] = 1
    filter = urlencode(req)
    api = 'https://api.bilibili.com/pgc/season/index/result?'
    html = get_html(api + filter)
    data = loads(html)

    items = [{'label': '[COLOR yellow][筛选过滤][/COLOR]',
              'path': url_for('select', name=name)}]

    total= int(data['data']['total'])
    total_page = (total + 19) // 20

    items += previous_page('category', page, total_page, name=name, filter=filter)
    for item in data['data']['list']:
        title = item['title']
        extra = item['index_show']
        badge = item.get('badge')
        if badge:
            badge = u'[COLOR magenta]({})[/COLOR]'.format(badge)
        else:
            badge = ''
        items.append({
            'label': title + '(' + extra + ')' + badge,
            'path': plugin.url_for('season', link=item['link']),
            'thumbnail': item['cover']
        })

    items += next_page('category', page, total_page, name=name, filter=filter)
    return items


@plugin.route('/')
def root():
    CATEGORY = {'电影': 'movie', '电视剧': 'tv', '纪录片': 'documentary'}

    yield {
        'label': '搜索...',
        'path': url_for('search')
    }
    req = urlencode({'page':1})
    for item in CATEGORY:
        yield {
            'label': item,
            'path': url_for('category', name=CATEGORY[item], page=1, filter=req)
        }


if __name__ == '__main__':
    plugin.run()
