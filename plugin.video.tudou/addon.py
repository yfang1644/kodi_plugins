#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcswift2 import Plugin, xbmcgui
from urllib import quote_plus
import re
from bs4 import BeautifulSoup
from common import get_html, r1
from youku import Youku
from tudou import Tudou

plugin = Plugin()
url_for = plugin.url_for

########################################################################
# 土豆 www.tudou.com
########################################################################


HOST_URL = 'http://www.tudou.com'

BANNER = '[COLOR yellow]【%s】[/COLOR]'
BANNER_FMT = '[COLOR green]【%s】[/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


############################################################################
@plugin.route('/playvideo/<url>')
def playvideo(url):
    level = int(plugin.addon.getSetting('resolution'))

    if level == 4:
        dialog = xbmcgui.Dialog()
        level = dialog.select('清晰度选择', ['流畅', '高清', '超清', '1080P'])
        level = max(0, level)

    if 'youku' in url:
        urls = Youku().video_from_url(httphead(url), level=level)
    elif 'tudou' in url:
        urls = Tudou().video_from_url(httphead(url), level=level)

    stack_url = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stack_url)


def gettudoulist(url):
    html = get_html(httphead(url))
    tree = BeautifulSoup(html, 'html.parser')

    items = []

    soup = tree.find_all('div', {'class': 'td-listbox__list__item--show'})
    for item in soup:
        soup2str = str(item)
        title = re.compile('title=\"(.+?)\"').findall(soup2str)
        if not title:
            title = re.compile('title=\'(.+?)\'').findall(soup2str)
        thumb = re.compile('src="(.+?)"').findall(soup2str)
        purl = re.compile(' href="(.+?)"').findall(soup2str)
        if not (title and thumb and purl): continue

        items.append({
            'label': title[0],
            'path': url_for('playvideo', url=purl[0]),
            'is_playable': True,
            'thumbnail': thumb[0],
            'info': {'title': title[0]}
        })
    return items


def getyoukulist(url):
    html = get_html(httphead(url))
    tree = BeautifulSoup(html, 'html.parser')

    items = []
    progs = tree.find_all('div', {'class': 'program'})
    if len(progs) < 1:
        title = tree.find('meta', {'name': 'title'})['content']
        desc = tree.find_all('meta', {'name': 'description'})
        info = desc[0]['content']
        items.append({
            'label': title,
            'path': url_for('playvideo', url=url),
            'is_playable': True,
        })
    else:
        for item in progs:
            title = item['title']
            href = httphead(item.a['href'])
            img = item.img['src']
            t = item.find('span', {'class': 'c-time'})
            time = t.text
            items.append({
                'label': title + '(' + time + ')',
                'path': url_for('playvideo', url=item.a['href']),
                'is_playable': True,
                'thumbnail': item.img['src'],
            })

    soup = tree.find_all('div', {'class': 'items clearfix'})
    if not soup:
        return items

    soups = soup[0].find_all('div', {'class': 'item'})
    for item in soups:
        desc = item.find('div', {'class': 'show_aspect'})
        info = desc.text if desc is not None else ''
        try:
            title = item['title']
        except:
            continue
        items.append({
            'label': item['title'].encode('utf-8'),
            'path': url_for('playvideo', url=item.a['href']),
            'is_playable': True,
            'info': {'title': item['title'], 'plot': info},
        })
    return items


@plugin.route('/movielist/<url>')
def episodelist(url):
    plugin.set_content('video')
    if 'youku' in url:
        items = getyoukulist(url)
    elif 'tudou' in url:
        items = gettudoulist(url)

    return items


@plugin.route('/videolist/<url>')
def videolist(url):
    html = get_html(httphead(url))

    items = []

    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'td__category__filter__panel__item'})

    for item in soup:
        si = item.find_all('li')
        for subitem in si:
            if 'current' in subitem.get('class', ''):
                subtitle = '[B]{}[/B]'.format(subitem.text.encode('utf-8'))
        key = item.label.text.encode('utf-8')
        items.append({
            'label': BANNER % (key+subtitle),
            'path': url_for('select', url=url, filter=key)
        })

    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'v-pack--p'})

    for item in soup:
        items.append({
            'label': item.a['title'],
            'path': url_for('episodelist', url=item.a['href']),
            'thumbnail': item.img['src']
        })

    # page list
    soup = tree.find_all('div', {'class': 'yk-pager'})
    pages = soup[0].find_all('li')
    for page in pages:
        try:
            href = page.a['href']
        except:
            continue
        items.append({
            'label': page.a.text.encode('utf-8'),
            'path': url_for('videolist', url=href.encode('utf-8'))
        })

    return items


@plugin.route('/select/<url>/<filter>')
def select(url, filter):
    html = get_html(httphead(url))
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'td__category__filter__panel__item'})

    dialog = xbmcgui.Dialog()
    color = '[COLOR FF00FF00]%s[/COLOR]'
    for item in soup:
        if filter != item.label.text.encode('utf-8'):
            continue
        si = item.find_all('li')
        list = []
        i = 0
        for subitem in si:
            title = subitem.text
            if 'current' in subitem.get('class', ''):
                title = '[B]{}[/B]'.format(title.encode('utf-8'))
                mark = i
            list.append(title)
            i += 1
        sel = dialog.select(item.label.text, list)

        if sel >= 0:
            url = si[sel].a['href']
    return videolist(url.encode('utf-8'))


@plugin.route('/search')
def search():
    plugin.set_content('video')
    keyboard = xbmc.Keyboard('', '请输入搜索内容')

    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return []

    keyword = keyboard.getText()
    p_url = 'http://www.soku.com/nt/search/q_'
    url = p_url + quote_plus(keyword)
    page = get_html(url)
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('div', {'class': 's_base'})
    items = []
    for item in soup:
        title = item.a['_log_title']
        href = item.a['href']
        info = item.find('div', {'class': 'info-cont'})
        info = info.span['data-text'] if info else ''

        items.append({
            'label': title,
            'path': url_for('playvideo', url=href),
            'is_playable': True,
            'info': {'title': title, 'plot': info},
        })
    soup = tree.find_all('ul', {'class': 'clearfix'})
    soups = soup[0].find_all('li')
    for item in soups:
        try:
            items.append({
                'label': item.a['_log_title'] + item.span.text,
                'path': url_for('playvideo', url=item.a['href']),
                'is_playable': True,
            })
        except:
            continue
    return items


@plugin.route('/')
def index():
    yield {
        'label': BANNER % '土豆视频 - 搜索',
        'path': url_for('search')
    }

    url = HOST_URL + '/category'

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'td__category__filter__nav__item'})

    for prog in soup[1:]:
        cur = prog['class']
        if len(cur) > 1:
            href = url
        else:
            href = prog.a['href']
        nametype = href.split('/')[-1][:3]

        yield {
            'label': prog.text,
            'path': url_for('videolist', url=href)
        }


# main programs goes here #########################################
if __name__ == '__main__':
    plugin.run()

runlist = {
    None: 'mainMenu()',
    'videolist': 'listSubMenu(params)',
    'videolist1': 'listSubMenu1(params)',
    'videolist2': 'listSubMenu2(params)',
    'albumlist': 'albumList(params)',
    'codelist': 'relatedPlayList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchInTudou(params)',
    'select': 'normalSelect(params)'
}

