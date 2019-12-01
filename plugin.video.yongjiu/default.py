#!/usr/bin/python
# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, ListItem, xbmc
from bs4 import BeautifulSoup
from urlparse import urlparse
from json import loads
from common import get_html
import re

m3u8_file = xbmc.translatePath('special://home/temp/m3u8')

HOST_URL = 'http://www.yongjiuzy1.com'
plugin = Plugin()
url_for = plugin.url_for

SEASON_CACHE = plugin.get_storage('season')
HISTORY = plugin.get_storage('history')

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url
    return url


# get search result by input keyword
@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = HOST_URL + '/index.php?m=vod-search&wd=' + keyword
        return category(url)


@plugin.route('/play/<url>/<m3u8>')
def play(url, m3u8):
    parsed = urlparse(url)
    server = parsed.scheme + '://' + parsed.netloc
    page = get_html(url)
    if int(m3u8) == 1:
        #videourl = re.compile('(\S.*m3u8)').findall(page)
        #m3u8 = get_html(server + videourl[0])
        #m3u8 = re.sub('\n/', '\n'+server + '/', m3u8)
        #with open(m3u8_file, "wb") as m3u8File:
        #    m3u8File.write(m3u8)
        #    m3u8File.close()

        plugin.set_resolved_url(url)
    else:
        redir = re.compile('var redirecturl.*"(.+)"').findall(page)[0]
        mp4 = re.compile('var main.*"(.+)"').findall(page)[0]
        movie = server + mp4
        plugin.set_resolved_url(movie)


@plugin.route('/episodes/<url>')
def episodes(url):
    plugin.set_content('TVShows')
    video = get_html(url)
    tree = BeautifulSoup(video, 'html.parser')
    title = tree.title.text
    title = re.compile('(.+?) - *').findall(title)[0]
    soups = tree.find('div', {'class': 'contentNR'})
    textinfo = soups.text
    soups = tree.find('div', {'class': 'videoPic'})
    thumb = soups.img['src']

    selmode = plugin.addon.getSetting('m3u8')
    lists = tree.find_all('input', {'type': 'checkbox'})
    items = []
    for item in lists:
        value = item['value'].split('$')
        if len(value) < 2:
            continue
        if 'http' not in value[1]:
            continue
        if 'm3u8' in value[1]:
            m3u8 = 1
        else:
            m3u8 = 0

        if selmode == 'true' and m3u8:
            items.append({
                'label': title + '(m3u8)'*m3u8 + '(' + value[0] + ')',
                'path': url_for('play', url=value[1], m3u8=m3u8),
                'is_playable': True,
            'thumbnail': thumb,
                'info': {'title': title +'-'+value[0], 'plot': textinfo}
            })
        if selmode != 'true' and m3u8 == 0:
            items.append({
                'label': title + '(m3u8)'*m3u8 + '(' + value[0] + ')',
                'path': url_for('play', url=value[1], m3u8=m3u8),
                'is_playable': True,
            'thumbnail': thumb,
                'info': {'title': title +'-'+value[0], 'plot': textinfo}
            })

    return items


# list catagories
@plugin.route('/category/<url>')
def category(url):
    plugin.set_content('TVShows')
    page = get_html(url)
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('tr', {'class': 'DianDian'})
    items = []
    for item in soups:
        td = item.find('td', {'class': 'l'})
        url = td.a['href']
        text = item.td.text.replace('\n', ' ')
        items.append({
            'label': text,
            'path': url_for('episodes', url=httphead(url))
        })

    page = tree.find('div', {'class': 'page_num'})
    pages = page.find_all('a')
    for page in pages:
        items.append({
            'label': page.text,
            'path': url_for('category', url=httphead(page['href']))
        })
    return items


# main entrance
@plugin.route('/')
def index():
    url = ''
    home = get_html(HOST_URL)
    if (len(home) < 1000):
        prehome = re.search('var (.*);;', home)
        exec (prehome.group(1))

    home = get_html(HOST_URL + url)
    tree = BeautifulSoup(home, 'html.parser')
    soup = tree.find_all('div', {'class': 'nav'})
    lists = soup[0].find_all('li')

    yield {
        'label': u'[COLOR yellow]搜索[/COLOR]',
        'path': url_for('search'),
    }

    for item in lists[1:]:
        title = item.a.text
        url = item.a['href']
        yield {
            'label': title,
            'path': url_for('category', url=httphead(url)),
        }


if __name__ == '__main__':
    plugin.run()
