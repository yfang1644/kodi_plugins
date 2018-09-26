#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui, xbmc
from bs4 import BeautifulSoup
from urllib import urlencode
import re
from json import loads
from common import get_html
from lib.pptv import video_from_vid

# Plugin constants

plugin = Plugin()
url_for = plugin.url_for

PPTV_LIST = 'http://list.pptv.com/'
PPTV_TV_LIST = 'http://live.pptv.com/list/tv_list'
VIP = '[COLOR FFFF00FF](VIP)[/COLOR]'
NEW = u'[COLOR 808000FF](新)[/COLOR]'

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []


def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []


@plugin.route('/tvstudio/<url>/<page>')
def tvstudio(url, page):
    pass


@plugin.route('/playvideo/<vid>')
def playvideo(vid):
    quality = int(plugin.addon.getSetting('movie_quality'))

    urls = video_from_vid(vid, level=quality)
    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/search')
def search():
    return []
    keyboard = xbmc.Keyboard('', '请输入搜索内容')

    keyboard.doModal()
    if (keyboard.isConfirmed()):
        key = keyboard.getText()
        if len(key) > 0:
            u = sys.argv[0] + '?mode=searchlist&key=' + key
            xbmc.executebuiltin('Container.Update(%s)' % u)


@plugin.route('/select/<url>')
def select(url):
    html = get_html(url)
    # html has an extra </dt>
    html = re.sub('<\/dt>\n *<\/dt>', '<\/dt>', html)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('div', {'class': 'sear-menu'})

    filter = filter[0].find_all('dl')
    dialog = xbmcgui.Dialog()

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
            return videolist(url, 1)


@plugin.route('/episodelist/<url>')
def episodelist(url):
    html = get_html(url)
    playcfg = re.compile('var webcfg\s*=\s*({.+?);\n').findall(html)
    if playcfg:
        jsplay = loads(playcfg[0])
    else:
        return []

    items = []
    content = jsplay['share_content']
    for item in jsplay['playList']['data']['list']:
        vip = '' if int(item['vip']) == 0 else VIP
        new = NEW if item.get('isNew') else ''
        items.append({
            'label': item['title'] + vip + new,
            'path': url_for('playvideo', vid=item['id']),
            'thumbnail': item['capture'],
            'is_playable': True,
            'info': {'title': item['title']},
        })

    return items


@plugin.route('/videolist/<url>/<page>')
def videolist(url, page):
    plugin.set_content('TVShows')
    items = [{
        'label': '[COLOR green]分类过滤[/COLOR]',
        'path': url_for('select', url=url)
    }]

    p = get_html(url)
    c = re.compile('pageNum.*\/ (\d+)<\/p>').findall(p)
    total = c[0]
    items += previous_page('videolist', page=page, total_page=total, url=url)

    c = re.compile('.*/(.*).html').findall(url)
    utype = c[0].split('_')
    req = {'page': page}
    for x in range(0, len(utype), 2):
        req[utype[x]] = utype[x+1]
    data = urlencode(req)
    html = get_html(PPTV_LIST + 'channel_list.html?' + data)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('a', {'class': 'ui-list-ct'})

    for item in soup:
        text = item.find('span', {'class': 'msk-txt'})
        if text:
            text = '(' + text.text + ')'
        else:
            text = ''
        items.append({
            'label': item['title'] + text,
            'path': url_for('episodelist', url=item['href']),
            'thumbnail': item.img['data-src2'],
        })

    items += next_page('videolist', page=page, total_page=total, url=url)
    return items


@plugin.route('/')
def root():
    # show search entry
    #yield {
    #    'label': '[COLOR FF00FFFF]<搜索...>[/COLOR]',
    #    'path': url_for('search')
    #}
    #yield {
    #    'label': u'全国电视台',
    #    'path': url_for('tvstudio', url=PPTV_TV_LIST, page=1)
    #}

    data = get_html(PPTV_LIST)
    soup = BeautifulSoup(data, 'html.parser')
    menu = soup.find_all('div', {'class': 'detail_menu'})
    tree = menu[0].find_all('li')
    for item in tree:
        url = item.a['href']
        t = re.compile('type_(\d+)').findall(url)
        if len(t) < 1:
            continue
        yield {
            'label': item.a.text,
            'path': url_for('videolist', url=url, page=1)
        }


if __name__ == '__main__':
    plugin.run()
