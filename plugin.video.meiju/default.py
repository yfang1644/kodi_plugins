#!/usr/bin/python
# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, ListItem, xbmc
from bs4 import BeautifulSoup
from common import get_html, r1

YYETSS = 'http://www.yyetss.com/'
TTKMJ = 'https://www.ttkmj.org/'
BANNER = '[COLOR FFDEB887]{}[/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

@plugin.route('/stay/')
def stay():
    pass

@plugin.route('/ttepisodes/<url>/')
def ttepisodes(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'episode_list'})

    items = []
    for part in tree:
        pl = part.findAll('a')
        items.append({
            'label': BANNER.format('源组'),
            'path': url_for('stay')
        })
        for item in pl:
            items.append({
                'label': item.text,
                'path': url_for('yyplay', url=item['href']),
                'is_playable': True,
                'info': {'title': item.text}
            })

    return items


@plugin.route('/ttcategory/<url>/')
def ttcategory(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('li', {'class': 'subject-item'})
    items = []
    for item in tree:
        items.append({
            'label': item.img['title'],
            'path': url_for('ttepisodes' ,url=item.a['href']),
            'thumbnail': item.img['data-src']
        })
        
    # 分页
    tree = soup.findAll('div', {'class': 'page_navi'})
    pages = tree[0].findAll('a')
    for page in pages:
        items.append({
            'label': page.text,
            'path': url_for('ttcategory', url=page['href'])
        })

    return items


@plugin.route('/ttkmj/')
def ttkmj():
    html = get_html(TTKMJ)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'nav-items'})
    tree = tree[0].findAll('li')
    items = []
    for item in tree[2:-1]:
        items.append({
            'label': item.text,
            'path': url_for('ttcategory', url=item.a['href'])
        })

    return items


@plugin.route('/yyplay/<url>/')
def yyplay(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('iframe')
    try:
        playurl = tree[0]['src']
    except:
        playurl = r1('(https://.+?m3u8)', html)
    if 'm3u8' not in playurl:
        host = r1('(https?://.+?)/', playurl)
        html = get_html(playurl)
        playurl = host + r1('var main\s*=\s*"(.+?)"', html)

    if "url=" in playurl:
        playurl = r1('url=(.+?$)', playurl)

    plugin.set_resolved_url(playurl)


@plugin.route('/yyepisodes/<url>/')
def yyepisodes(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class':'tab_set_info'})

    items = []
    for sect in tree:
        if u'相关推荐' in sect.text:
            items.append({
                'label': BANNER.format('相关推荐'),
                'path': url_for('stay')
            })

            refers = sect.findAll('li')
            for item in refers:
                href = item.a['href']
                if href[0] == '/': href = YYETSS + href
                items.append({
                    'label': item.text,
                    'path': url_for('yyepisodes', url=href),
                })
        elif (u'网盘' in sect.text) or (u'地址列表' in sect.text):
            pass
        else:
            items.append({
                'label': BANNER.format('源组'),
                'path': url_for('stay')
            })
            section = sect.findAll('li')
            for item in section:
                try:
                    href = item.a['href']
                except:
                    continue
                if href[0] == '/': href = YYETSS + href
                items.append({
                    'label': item.text,
                    'path': url_for('yyplay', url=href),
                    'is_playable': True,
                    'info': {'title': item.text}
                })

    return items


@plugin.route('/yycategory/<url>/')
def yycategory(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('ul', {'class':'list-inline'})
    years = tree[0].findAll('li')
    items = []

    items.append({
        'label': BANNER.format('年份'),
        'path': url_for('stay')
    })
    # 年份
    for item in years[1:]:
        title = item.text
        try:
            href = item.a['href']
        except:
            href = url
        if href[0] == '/': href = YYETSS + href
        items.append({
            'label': title,
            'path': url_for('yycategory', url=href)
        })
    
    items.append({
        'label': BANNER.format('剧集'),
        'path': url_for('stay')
    })
    tree = soup.findAll('div', {'class':'c-list-box'})
    for item in tree:
        title = item.a['title']
        href = item.a['href']
        img = item.img['src']
        try:
            info = u'[COLOR pink]({})[/COLOR]'.format(item.span.text)
        except:
            info = 'XXX'
        items.append({
            'label': title + info,
            'path': url_for('yyepisodes', url=href),
            'thumbnail': img
        })

    items.append({
        'label': BANNER.format('分页'),
        'path': url_for('stay')
    })
    tree = soup.findAll('ul', {'class':'pagination'})
    pages = tree[0].findAll('li')
    for item in pages:
        title = item.text
        href = item.a['href']
        if href[0] == '/': href = YYETSS + href
        items.append({
            'label': title,
            'path': url_for('yycategory', url=href)
        })

    return items


@plugin.route('/yyetss/')
def yyetss(): 
    html = get_html(YYETSS)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('li')
    items = []
    for item in tree[2:-1]:
        url = item.a['href']
        if url[0] == '/': url = YYETSS + url
        items.append({
            'label': item.text,
            'path': url_for('yycategory', url=url)
        })

    return items


# main entrance
@plugin.route('/')
def index():
    yield {
        'label': '人人影视',
        'path': url_for('yyetss')
    }

    yield {
        'label': '天天看美剧',
        'path': url_for('ttkmj')
    }

if __name__ == '__main__':
    plugin.run()
