#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, ListItem, xbmcgui
from bs4 import BeautifulSoup
import re
from common import get_html, r1
from json import loads
import time

YYETSS = 'http://www.yyetss.com/'
TTKMJ = 'https://www.ttkmj.org/'
MEIJUXIA = 'http://www.meijuxia.vip'
BANNER = '[COLOR FFDEB887]{}[/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

@plugin.route('/stay/')
def stay():
    pass


@plugin.route('/xiaplay/<url>/')
def xiaplay(url):
    html = get_html(url)
    m = r1('cms_player\s*=\s*({.+?\});', html)
    urlinfo = loads(m)
    u = urlinfo['url']
    print "XXXXXXXXXXXXXXXXXXX",u
    t = int(time.time())
    #u = re.sub('sign=\d+', 'sign='+str(t), u)
    playurl = urlinfo['jiexi'] + u
    playurl = get_html(playurl)
    print playurl.encode('utf-8')

    print "XXXXXXXXXXXXXXXXXX", playurl+'?t='+t
    plugin.set_resolved_url(playurl + '?t=' + t)


@plugin.route('/xiafilter/<url>/')
def xiafilter(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')


@plugin.route('/xiaepisode/<url>/')
def xiaepisode(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'tab-content'})
    items = []
    
    lists = tree[0].findAll('li')
    for item in lists:
        items.append({
            'label': item.text,
            'path': url_for('xiaplay', url=MEIJUXIA+item.a['href']),
            'is_playable': True,
            'info': {'title': item.text}
        })
    return items


@plugin.route('/xiacatagory/<url>/')
def xiacatagory(url=None):
    if url is None:
        url = MEIJUXIA + '/list-select-id-2-type--area--year--star--state--order-addtime.html'
    items = []

    items.append({
        'label': '[COLOR yellow] 分类过滤[/COLOR]]',
        'path': url_for('xiafilter', url=url)
    })

    plugin.set_content('TVShows')
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('ul', {'class': 'list-unstyled'})

    lists = tree[0].findAll('li')
    for item in lists:
        url = MEIJUXIA + item.a['href']
        title = item.img['alt']
        info = item.span.text
        info = info.replace('\n', '')
        info = info.replace('\t', '')
        info = info.replace(' ', '')
        items.append({
            'label': title + '('+ info + ')',
            'path': url_for('xiaepisode', url=url),
            'thumbnail': item.img['data-original'],
        })

    pages = soup.findAll('a', {'class': 'page-link'})
    for page in pages:
        items.append({
            'label': page.text,
            'path': url_for('xiacatagory', url=MEIJUXIA + page['href'])
        })
    return items


@plugin.route('/meijuxia/')
def meijuxia():
    return xiacatagory(None)

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
            'path': url_for('stay'),
            'is_playable': True
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
        try:
            info = u'[COLOR pink]({})[/COLOR]'.format(item.span.text)
        except:
            info = ''
        items.append({
            'label': item.img['title'] + info,
            'path': url_for('ttepisodes' ,url=item.a['href']),
            'thumbnail': item.img['data-src'],
            'info': {'title': item.img['title'], 'plot': item.p.text}
        })
        
    # 分页
    items.append({
        'label': BANNER.format('分页'),
        'path': url_for('stay'),
        'is_playable': True
    })
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

    info = r1('<meta name="description.+?content="([^"]+)"', html)

    items = []
    for sect in tree:
        if u'相关推荐' in sect.text:
            items.append({
                'label': BANNER.format('相关推荐'),
                'path': url_for('stay'),
                'is_playable': True
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
                'path': url_for('stay'),
                'is_playable': True
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
                    'info': {'title': item.text, 'plot': info}
                })

    return items


@plugin.route('/yyfilter/<url>/')
def yyfilter(url): 
    dialog = xbmcgui.Dialog()
    
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    tree = soup.findAll('ul', {'class': 'navbar-nav'})
    titles = tree[0].findAll('li')
    lst = [x.text for x in titles[2:-1]]
    sel = dialog.select('分类', lst)
    sel = max(0, sel)
    href = titles[2+sel].a['href']
    hs = href.split('-')
    cate = hs[1]

    tree = soup.findAll('ul', {'class':'list-inline'})
    titles = tree[0].findAll('li')
    lst = [x.text for x in titles[1:]]
    sel = dialog.select('年份', lst)
    sel = max(0, sel)
    href = titles[1+sel].a['href']
    hs = href.split('-')
    year = hs[2]
    return yycategory(cate, year, 1)


@plugin.route('/yycategory/<cate>/<year>/<page>/')
def yycategory(cate, year, page):
    plugin.set_content('TVShows')
    items = []

    url = YYETSS + 'list-{}-{}-{}.html'.format(cate, year, page)
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    tree = soup.findAll('ul', {'class': 'navbar-nav'})
    titles = tree[0].findAll('li')
    cname = ''
    for x in titles[2:-1]:
        if cate in x.a['href']:
            cname = x.text.encode('utf-8')
            break

    items.append({
        'label': '分类 [COLOR yellow][{}-{}][/COLOR]'.format(cname, year),
        'path': url_for('yyfilter', url=url)
    })


    tree = soup.findAll('div', {'class':'c-list-box'})
    for item in tree:
        title = item.a['title']
        href = item.a['href']
        img = item.img['src']
        try:
            info = u'[COLOR pink]({})[/COLOR]'.format(item.span.text)
        except:
            info = ''
        items.append({
            'label': title + info,
            'path': url_for('yyepisodes', url=href),
            'thumbnail': img
        })

    tree = soup.findAll('ul', {'class':'pagination'})
    if not tree:
        return items
    # 分页
    items.append({
        'label': BANNER.format('分页'),
        'path': url_for('stay')
    })
    pages = tree[0].findAll('li')
    for item in pages:
        title = item.text
        href = item.a['href']
        page = r1('-(\d+).html', href)
        if href[0] == '/': href = YYETSS + href
        items.append({
            'label': title,
            'path': url_for('yycategory', cate=cate, year=year, page=page)
        })

    return items


# main entrance
@plugin.route('/')
def index():
    yield {
        'label': '人人影视',
        'path': url_for('yycategory', cate='lishi', year='all', page=1)
    }
    yield {
        'label': '天天看美剧',
        'path': url_for('ttkmj')
    }
    #yield {
    #    'label': '美剧侠',
    #    'path': url_for('meijuxia')
    #}


if __name__ == '__main__':
    plugin.run()
