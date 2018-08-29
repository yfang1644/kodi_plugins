#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcgui
from urllib import quote_plus
import re
import os
from json import loads
from bs4 import BeautifulSoup
from common import get_html
from lib.letv import video_from_vid

plugin = Plugin()
url_for = plugin.url_for

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url

########################################################################
# 乐视网(LeTv) by cmeng
########################################################################
# Version 1.5.9 2016-05-25 (cmeng)
# Implement all possible fixes to handle slow network response (starve network data)
# Add video server selection option
# Stop last video from repeating playback
# Improve user UI feedback on slow network data fetching actual status (background)

# See changelog.txt for previous history
########################################################################

# Plugin constants
__profile__   = xbmc.translatePath(plugin.addon.getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8')).decode("utf-8")

HOST_URL = 'https://www.le.com'
LIST_URL = 'http://list.le.com'
ALBULM_URL = 'http://d.api.m.le.com/play/getAllVideoList?id=%s&platform=pc'
ALBULM_URL = 'http://d.api.m.le.com/card/dynamic?vid=%s&platform=pc'


@plugin.route('/filter/<url>')
def filter(url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'list_nav'})
    dialog = xbmcgui.Dialog()

    urlsplit = url.split('/')
    urltype = re.compile('\w{1}.+?_').findall(urlsplit[-1])
    marktype = []
    for item in soup:
        typelist = item.span.text
        title= re.sub('\r|\n|\t| ', '', typelist)
        li = item.findAll('li')
        sel = dialog.select(title, [x.text for x in li])

        if sel >= 0:
            if 'href' not in li[sel]: li[sel]['href'] = url
            selurl = li[sel]['href'].split('/')
            seltype = re.compile('\w{1}.+?_').findall(selurl[-1])
            for i in seltype:
                if i not in urltype:
                    marktype.append(i)

    u1 = urlsplit[-1]
    for type in marktype:
        u1 = re.sub(type[0] + '.+?_', type, u1)
    urlsplit[-1] = u1
    url = '/'.join(urlsplit)
    return videolist(url=url, page=1)


@plugin.route('/playvideo/<vid>')
def playvideo(vid):
    v_urls = video_from_vid(vid, m3u8=__m3u8__, level=3)
    xbmc.Player().play(__m3u8__)


@plugin.route('/episodelist/<vids>/<name>')
def episodelist(vids, name):
    plugin.set_content('TVShows')
    items = []
    vlist = vids.split(',')
    for i, vid in enumerate(vlist):
        title = name + '-' + str(i+1)
        items.append({
            'label': title,
            'path': url_for('playvideo', vid=vid, name=title),
            'is_playable': True,
            'info': {'title': title}
        })
    return items


###############################################################################
# Search LeTV site based on keyword
###############################################################################
@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    # keyboard.setHiddenInput(hidden)
    xbmc.sleep(1000)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()

    page = 1
    p_url = 'http://so.le.com/s?hl=1&dt=2&ph=420001&from=pcjs&ps=30&wd='
    p_url = p_url + quote_plus(keyword)
    link = get_html(p_url)
    items = []
    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')

    soup = content.find_all('li', {'class': 'list_item'})
    soup1 = content.find_all('div', {'class': 'So-detail Movie-so'})
    soup2 = content.find_all('div', {'class': 'So-detail Tv-so'})
    for item in soup1 + soup2:
        try:
            href = item.a['href']
        except:
            continue
        title = item.a['title']
        try:
            img = item.a['src']
        except:
            img = item.img['src']

        info = item.find('div', {'class': 'info-cnt'})
        try:
            info = info.text
        except:
            info = ''
        items.append({
            'label': title,
            'path': url_for('episodelist', vids=1, name=title.encode('utf-8')),
            'thumbnail': img,
            'info': {'title': title, 'plot': info}
        })
    return items


@plugin.route('/videolist/<url>/<page>')
def videolist(url, page):
    plugin.set_content('TVShows')
    html = get_html(url)
    frontUrl = re.compile("frontUrl: '(.+)'").findall(html)[0]
    tree = BeautifulSoup(html, 'html.parser')

    items = []

    # filter by types
    soup = tree.find_all('div', {'class': 'list_nav'})

    title = u'[COLOR yellow]分类过滤[/COLOR]|'
    for item in soup:
        typelist = item.span.text
        typelist = re.sub('\r|\n|\t| ', '', typelist)
        li = item.findAll('li')
        curr = item.find('li', {'class': 'cur'})
        try:
            type = curr.text
        except:
            type = ''
        type = re.sub('\r|\n|\t| ', '', type)
        title += typelist + '(' + type + ')' + '|'

    items.append({
        'label': title,
        'path': url_for('filter', url=url)
    })

    page = int(page)
    if page > 1:
        items.append({
            'label': '上一页',
            'path': url_for('videolist', url=url, page=page-1)
        })

    newpage = '&pn=' + str(page)
    frontUrl = re.sub('&pn=\d+', newpage, frontUrl)
    html = get_html(frontUrl)
    jsdata = loads(html)['data']['arr']
    for item in jsdata:
        vids = item.get('vids')
        if vids is None:
            vids = item.get('vid')
        if ',' in vids:
            items.append({
                'label': item['name'],
                'path': url_for('episodelist', vids=vids, name=item['name'].encode('utf-8')),
                'thumbnail': item['imgUrl'],
                'info': {'title': item['name'], 'plot': item['description']},
            })
        else:
            items.append({
                'label': item['name'],
                'path': url_for('playvideo', vid=vids),
                'is_playable': True,
                'thumbnail': item['imgUrl'],
                'info': {'title': item['name'], 'plot': item['description']},
            })

    items.append({
        'label': '下一页',
        'path': url_for('videolist', url=url, page=page+1)
    })

    return items


@plugin.route('/')
def index():
    plugin.set_content('videos')
    yield {
        'label': '[COLOR green]【乐视网 - 搜索】[/COLOR]',
        'path': url_for('search')
    }

    url = LIST_URL + '/listn/c2_t-1_a-1_y-1_s1_md_o7_d1_p.html'
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'list_cnt'})

    grp = soup[0].find_all('li')
    for prog in grp:
        try:
            href = prog.a['href']
        except:
            href = url
        title = prog.text
        title = re.sub('\n| ', '', title)
        yield {
            'label': title,
            'path': url_for('videolist', url=httphead(href), page=1)
        }


if __name__ == '__main__':
    plugin.run()

#http://list.le.com/getLesoData?from=pc&src=1&stype=1&ps=30&pn=2&ph=420001&dt=1&cg=2&or=4&stt=1&vt=180001&sc=30024&yr=2017&s=1
