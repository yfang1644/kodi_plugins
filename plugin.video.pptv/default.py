#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
from bs4 import BeautifulSoup
import re
from json import loads
from common import get_html
from lib.pptv import video_from_vid, urlencode, parse_qsl

# Plugin constants

PPTV_LIST = 'http://list.pptv.com/'
PPTV_TV_LIST = 'http://live.pptv.com/list/tv_list'
VIP = '[COLOR FFFF00FF](VIP)[/COLOR]'
NEW = u'[COLOR 808000FF](新)[/COLOR]'

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        li = ListItem('上一页 - {0}/{1}'.format(page, str(total_page)))
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) - 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        li = ListItem('下一页 - {0}/{1}'.format(page, str(total_page)))
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) + 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
        addDirectoryItem(int(sys.argv[1]), u, li, True)


def playvideo(params):
    quality = int(xbmcaddon.Addon().getSetting('movie_quality'))
    urls = video_from_vid(params['vid'], level=quality)
    stackurl = 'stack://' + ' , '.join(urls)

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    list_item = ListItem(params['name'], thumbnailImage=params['thumbnail'])
    list_item.setInfo(type="video", infoLabels={"Title": params['name']})
    playlist.add(stackurl, list_item)
    xbmc.Player().play(playlist)
    xbmc.sleep(500)


def search(params):
    return
    keyboard = xbmc.Keyboard('', '请输入搜索内容')

    keyboard.doModal()
    if (keyboard.isConfirmed()):
        key = keyboard.getText()
        if len(key) > 0:
            u = sys.argv[0] + '?mode=searchlist&key=' + key
            xbmc.executebuiltin('Container.Update(%s)' % u)


def select(params):
    html = get_html(params['url'])
    # html has an extra </dt>
    html = re.sub('<\/dt>\n *<\/dt>', '<\/dt>', html)
    soup = BeautifulSoup(html, 'html.parser')
    filter = soup.findAll('div', {'class': 'sear-menu'})

    filter = filter[0].findAll('dl')
    dialog = Dialog()

    for item in filter:
        try:
            title = item.dt.text        # zongyi has no <dt>
        except:
            title = 'xxx'
        tx = re.compile(u'(.*)：.*').findall(title)
        if len(tx) > 0:
            title = tx[0]
        dd = item.find_all('dd')
        if len(dd) < 1:
            continue
        si = dd[0].find_all('a')
        list = []
        u = []
        sel0 = 0
        for sel, x in enumerate(si):
            name = x.get('title')
            if name is None:
                continue
            on = x.get('class')
            if on:
                on = ''.join(on)
            if on and on.strip() == 'all':
                list.append('[COLOR gold]' + x.text + '[/COLOR]')
                sel0 = sel 
            else:
                list.append(x.text)
            u.append(x['href'])

        sel = dialog.select(title, list)
        if sel >= 0 and sel != sel0:
            url = u[sel]
            req = {'url': url, 'page':1}
            videolist(req)


def episodelist(params):
    html = get_html(params['url'])
    playcfg = re.compile('var webcfg\s?=\s?({.+?);\n').findall(html)
    if playcfg:
        jsplay = loads(playcfg[0])
    else:
        return

    content = jsplay['share_content']
    for item in jsplay['playList']['data']['list']:
        vip = '' if int(item['vip']) == 0 else VIP
        new = NEW if item.get('isNew') else ''
        li = ListItem(item['title']+vip+new, thumbnailImage=item['capture'])
        req = {
            'mode': 'playvideo',
            'name': item['title'].encode('utf-8'),
            'vid': item['id'],
            'thumbnail': item['capture'].encode('utf-8')
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def videolist(params):
    page = int(params['page'])
    url = params['url']
    li = ListItem('[COLOR green]分类过滤[/COLOR]')
    u = sys.argv[0] + '?mode=select&url=' + 'url'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    p = get_html(url)
    c = re.compile('pageNum.*\/ (\d+)<\/p>').findall(p)
    total = c[0]
    previous_page('videolist', page=page, total_page=total, url=url)

    c = re.compile('.*/(.*).html').findall(url)
    utype = c[0].split('_')
    req = {'page': page}
    for x in range(0, len(utype), 2):
        req[utype[x]] = utype[x+1]
    data = urlencode(req)
    html = get_html(PPTV_LIST + 'channel_list.html?' + data)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('a', {'class': 'ui-list-ct'})

    for item in tree:
        text = item.find('span', {'class': 'msk-txt'})
        if text:
            text = '(' + text.text + ')'
        else:
            text = ''

        li = ListItem(item['title']+text, thumbnailImage=item.img['data-src2'])
        req = {
            'mode': 'episodelist',
            'url': item['href']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    next_page('videolist', page=page, total_page=total, url=url)
    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def root():
    data = get_html(PPTV_LIST)
    soup = BeautifulSoup(data, 'html.parser')
    menu = soup.findAll('div', {'class': 'detail_menu'})
    tree = menu[0].findAll('li')
    for item in tree:
        url = item.a['href']
        t = re.compile('type_(\d+)').findall(url)
        if len(t) < 1:
            continue
        li = ListItem(item.a.text)
        req = {
            'mode': 'videolist',
            'url': url,
            'page': 1
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
runlist = {
    'videolist': 'videolist(params)',
    'episodelist': 'episodelist(params)',
    'search': 'search(params)',
    'select': 'select(params)',
    'playvideo': 'playvideo(params)',

}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
if mode:
    del (params['mode'])
    exec(runlist[mode])
else:
    root()
