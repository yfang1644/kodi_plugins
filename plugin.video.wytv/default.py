#!/usr/bin/python
# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, ListItem, xbmc
from bs4 import BeautifulSoup
from common import get_html
import re

EXTRA = '[COLOR FFFF00FF]({})[/COLOR]'

HOST_URL = 'https://www.wytv5.com'
plugin = Plugin()
url_for = plugin.url_for

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
        url = '/index.php?m=vod-search&wd=' + keyword
        return category(url)


@plugin.route('/play/<url>/')
def play(url):
    page = get_html(httphead(url))

    video = re.compile("var video=\['(.+?)'\]").findall(page)
    movie = video[0].strip('->video/mp4')
    plugin.set_resolved_url(movie)


@plugin.route('/episodes/<url>')
def episodes(url):
    plugin.set_content('TVShows')
    video = get_html(httphead(url))
    tree = BeautifulSoup(video, 'html.parser')

    soups = tree.find_all('dl', {'class', 'ptab'})
    items = []
    content = ''
    img = ''

    for channel in soups:
        ct = channel.find('dt').text
        if u'内容简介' in ct:
            content = channel.find('li').text
            soups.remove(channel)
        if channel.img is not None:
            img = channel.img['src']
            soups.remove(channel)

    for channel in soups:
        ct = channel.find('dt').text.encode('utf-8')
        li = channel.find_all('li')
        for item in li:
            items.append({
                'label': item.text.encode('utf-8') + EXTRA.format(ct),
                'path': url_for('play', url=item.a['href']),
                'is_playable': True,
                'thumbnail': httphead(img),
                'info': {'title': item.text, 'plot': content}
        })
    return items


# list catagories
@plugin.route('/category/<url>')
def category(url):
    plugin.set_content('TVShows')
    page = get_html(httphead(url))
    tree = BeautifulSoup(page, 'html.parser')
    soups = tree.find_all('div', {'class': 'plist'})
    items = []
    films = soups[0].find_all('li')
    for item in films:
        url = item.a['href']
        img = item.img['src']
        try:
            title = item.find('label', {'class', 'title'}).text.encode('utf-8')
        except:
            title = ''
        try:
            name = item.find('label', {'class', 'name'}).text.encode('utf-8')
        except:
            name = ''
        if name == '':
            name = item.img['alt']

        items.append({
            'label': name + EXTRA.format(title),
            'path': url_for('episodes', url=url),
            'thumbnail': httphead(img)
        })

    page = tree.find('div', {'id': 'xwajaxpage'})
    if page:
        pages = page.find_all('a')
        for page in pages:
            items.append({
                'label': page.text,
                'path': url_for('category', url=page['href'])
            })
    return items


# main entrance
@plugin.route('/')
def index():
    home = get_html(HOST_URL)
    tree = BeautifulSoup(home, 'html.parser')
    soup = tree.find_all('div', {'class': 'menu'})
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
            'path': url_for('category', url=url),
        }


if __name__ == '__main__':
    plugin.run()
