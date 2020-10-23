#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
from xbmcswift2 import Plugin, xbmc, xbmcgui
from bs4 import BeautifulSoup
if sys.version[0]=='3':
    from urllib.parse import urlparse, quote_plus, unquote_plus
else:
    from urlparse import urlparse
    from urllib import quote_plus, unquote_plus
from json import loads
import re
from common import get_html, r1

m3u8_file = xbmc.translatePath('special://home/temp/m3u8')

YONGJIU = 'http://www.yongjiuzy1.com'
OKZYW = 'https://www.okzyw.com'
JIDE87 = 'http://www.jide87.com'

EXTRA = u'[COLOR magenta]({})[/COLOR]'
BANNER = '[COLOR FFDEB887]{}[/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

def httphead(host, url):
    if len(url) < 2:
        return url
    if url[:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = host + url
    return url


@plugin.route('/play/<url>/<m3u8>/')
def play(url, m3u8):
    parsed = urlparse(url)
    server = parsed.scheme + '://' + parsed.netloc
    page = get_html(url)
    if int(m3u8) == 1:
        #videourl = r1('(\S.*m3u8)', page)
        #m3u8 = get_html(server + videourl)
        #m3u8 = re.sub('\n/', '\n'+server + '/', m3u8)
        #with open(m3u8_file, "wb") as m3u8File:
        #    m3u8File.write(m3u8)
        #    m3u8File.close()

        plugin.set_resolved_url(url)
    else:
        redir = r1('var redirecturl.*"(.+)"', page)
        mp4 = r1('var main.*"(.+)"', page)
        movie = server + mp4
        plugin.set_resolved_url(movie)


@plugin.route('/stay/')
def stay():
    return

@plugin.route('/jdplay/<url>/')
def jdplay(url):
    html = get_html(httphead(JIDE87, url))
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.find('div', {'id': 'cms_player'})
    vurl = tree.script['src']

    html = get_html(httphead(JIDE87, vurl))
    data = r1('cms_player\s*=\s*({.+?\});', html)
    jdata = loads(data)

    plugin.set_resolved_url(jdata['url'])


@plugin.route('/jdfilter/<url>/')
def jdfilter(url):
    html = get_html(url)
    surl = url.split('-')
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.find('dl', {'class': 'dl-horizontal'})
    if tree is None:
        return
    dialog = xbmcgui.Dialog()

    dt = tree.findAll('dt')
    dd = tree.findAll('dd')

    flt = [surl[3]]
    for i in range(1, len(dt)):
        t = dd[i].findAll('a')
        content = [x.text for x in t]
        for x in range(len(content)):
            if quote_plus(content[x].encode('utf-8')) == surl[3+i*2]:
                content[x] = '[COLOR gold]%s[/COLOR]' % content[x]
                break
        sel = dialog.select(dt[i].text, content)
        if sel >= 0:
            purl = t[sel]['href']
            su = purl.split('-')
            flt += [su[3+i*2]]
        else:
            flt += [surl[3+i*2]]

    for i, x in enumerate(flt):
        if x == '': flt[i] = '0'
    return jdcategory(flt[0], flt[1], flt[2], flt[3], 1)


@plugin.route('/jdepisodes/<url>/')
def jdepisodes(url):
    plugin.set_content('TVShows')
    html = get_html(httphead(JIDE87, url))
    soup = BeautifulSoup(html, 'html.parser')
    desc = soup.find('span', {'class': 'ff-collapse'})
    desc = desc.text
    tree = soup.find('div', {'class': 'media'})
    img = tree.img['data-original']
    info = soup.find('div', {'class': 'media-body'})
    title = info.h1.a.text
    dd = info.find('dd')
    a = dd.findAll('a')
    cast = [x.text for x in a]

    items = []
    items.append({
        'label': BANNER.format('剧集'),
        'path': url_for('stay'),
        'is_playable': True
    })
    
    tree = soup.findAll('ul', {'class': 'list-unstyled'})
    for i, subtree in enumerate(tree):
        t = subtree.findAll('li', {'class', 'col-md-1'})
        if not t:
            break

        for item in t:
            items.append({
                'label': title + '--' + item.text,
                'path': url_for('jdplay', url=item.a['href']),
                'thumbnail': img,
                'is_playable': True,
                'info': {'title': title+'--'+item.text, 'plot': desc, 'artist': cast}
            })
            if (item.text).isdigit():
                items[-1]['info']['episode'] = int(item.text)

    items.append({'label': BANNER.format('同主演推荐'),
                  'path': url_for('stay'),
                  'is_playable': True
                 })
    films = tree[i].findAll('li')
    for item in films:
        info = item.find('p', {'class': 'image'})    
        if info.img['alt'] == title:
            films.remove(item)
                                 
    items += filmlist(films)

    items.append({
        'label': BANNER.format('热门推荐'),
        'path': url_for('stay'),
        'is_playable': True
    })

    films = tree[i+1].findAll('li')
    items += filmlist(films)

    return items


def filmlist(films):
    items = []
    for item in films:
        info = item.find('p', {'class': 'image'})
        url = info.a['href']
        img = info.img['data-original']
        title = info.img['alt']
        extra = info.span.text
        extra = extra.replace('\t', '')
        extra = extra.replace('\n', '')
        extra = extra.replace(' ', '')
        extra = u'[COLOR magenta] ({})[/COLOR]'.format(extra)
        h4 = item.find('h4', {'class': 'text-nowrap'})
        a = h4.findAll('a')
        cast = [x.text for x in a]

        items.append({
            'label': title + extra,
            'path': url_for('jdepisodes', url=url),
            'thumbnail': img,
            'info': {'title': title, 'artist': cast}
        })

    return items


@plugin.route('/jdcategory/<id>/<type>/<area>/<year>/<page>/')
def jdcategory(id, type, area, year, page):
    plugin.set_content('TVShows')
    gurl = JIDE87 + '/vod-type-id-{}-type-{}-area-{}-year-{}-star--state--order-addtime-p-{}.html'
    t = '' if type == '0' else type
    a = '' if area == '0' else area
    y = '' if year == '0' else year

    html = get_html(gurl.format(id, t, a, y, page))
    soup = BeautifulSoup(html, 'html.parser')

    items = []

    items.append({
        'label': '[COLOR gold]分类过滤 (%s-%s-%s)[/COLOR]' % (unquote_plus(t.encode('utf-8')), unquote_plus(a.encode('utf-8')), unquote_plus(y.encode('utf-8'))),
        'path': url_for('jdfilter', url=gurl.format(id, t, a, y, page))
    })

    tree = soup.find('ul', {'class': 'list-unstyled'})
    films = tree.findAll('li')
    items += filmlist(films)

    pageblock = soup.find('ul', {'class': 'pagination'})
    if not pageblock:
        return items
    items.append({
        'label': BANNER.format('分页'),
        'path': url_for('stay'),
        'is_playable': True
    })
    pages = pageblock.findAll('li')
    for x in pages:
        purl = x.a['href']
        p = r1('-p-(\d+).html', purl)
        if not p: continue
        items.append({
            'label': p,
            'path': url_for('jdcategory', id=id, type=type, area=area, year=year, page=p),
        })

    return items


@plugin.route('/jdsearch')
def jdsearch():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        plugin.set_content('TVShows')
        keyword = keyboard.getText()
        url = HOST_URL + '/video/search/{}.html'.format(quote_plus(keyword))
        html = get_html(url)
        soup = BeautifulSoup(html, 'html.parser')
        tree = soup.find('ul', {'class': 'list-unstyled'})
        films = tree.findAll('li')

        items = filmlist(films)

        return items


@plugin.route('/jdmain/<url>/')
def jdmain(url):
    yield {
        'label': u'[COLOR yellow]搜索[/COLOR]',
        'path': url_for('jdsearch'),
    }
    lists = [{'电影': 1},{'电视剧': 2}, {'动漫': 3}, {'福利': 4}]
    for item in lists:
        title = item.keys()[0]
        yield {
            'label': title,
            'path': url_for('jdcategory', id=item[title], type=0, area=0, year=0, page=1),
        }


@plugin.route('/oksearch')
def oksearch():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = '/index.php?m=vod-search&wd=' + quote_plus(keyword)
        return okcategory(url, '/?m=vod-type-id-2.html')


@plugin.route('/okfilter/<curl>/')
def okfilter(curl):
    html = get_html(httphead(OKZYW, curl))
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.find('div', {'class': 'sddm'})
    lists = tree.findAll('li')
    pattern = r1('(id-\d+).html', curl)
    for x in lists:
        if pattern in x.a.get('href', ''):
            selects = x.findAll('a')
            break

    dialog = xbmcgui.Dialog()
    content = [x.text for x in selects]
    sel = dialog.select('分类', content)
    if sel >= 0:
        return okcategory(selects[sel]['href'], curl)


def ip_replace(url):
    ip_table = (
        ('v-mtime\.com', 'youku.com-www-163.com'),
        ('vip\.okzybo\.com' ,'youku.cdn-56.com'),
        ('youku\.com-www-163\.com' , 'ifeng.com-v-ifeng.com'),
        ('cdn\.okokyun\.com', 'sohu.com-v-sohu.com'),
        ('cn2\.okokyun\.com', 'youku.cdn1-letv.com'),
        ('163\.com-l-163\.com', 'bilibili.com-l-163.com'),
        ('youku\.com-i-youku\.com', 'bilibili.com-l-163.com'),
        ('789\.com-l-163\.com', 'bilibili.com-l-163.com'),
        ('youku\.cdn1-okzy\.com', 'youku.cdn11-okzy.com')
    )
    for a, b in ip_table:
        url = re.sub(a, b, url)
    return url


@plugin.route('/okepisode/<url>/')
def okepisode(url):
    plugin.set_content('TVShows')
    html = get_html(httphead(OKZYW, url))
    soup = BeautifulSoup(html, 'html.parser')
    info = soup.find('div', {'class': 'vodplayinfo'})
    textinfo = info.text
    img = soup.find('img', {'class': 'lazy'})
    title = img['alt']
    img = httphead(OKZYW, img['src'])

    lists = soup.findAll('input', {'type': 'checkbox'})
    items = []
    i = 0
    for item in lists:
        url = item['value']
        if 'http' not in url or 'm3u8' not in url:
            continue
        i += 1
        url = ip_replace(url)
        items.append({
            'label': title + '(' + str(i) + ')',
            'path': url_for('play', url=url, m3u8=1),
            'is_playable': True,
            'thumbnail': img,
            'info': {'title': title +'-'+ str(i), 'plot': textinfo}
        })

    return items
    

@plugin.route('/okcategory/<url>/<curl>/')
def okcategory(url, curl):
    plugin.set_content('TVShows')
    items = []
    items.append({
        'label': u'[COLOR yellow]分类[/COLOR]',
        'path': url_for('okfilter', curl=curl),
    })
    
    html = get_html(httphead(OKZYW, url))
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.find('div', {'class': 'xing_vb'})
    lists = tree.findAll('li')
    for item in lists[1:]:
        try:
            items.append({
                'label': item.a.text,
                'path': url_for('okepisode', url=item.a['href'])
            })
        except:
            pass

    tree = soup.find('div', {'class': 'pages'})
    pages = tree.findAll('a')
    for page in pages:
        try:
            url = page['href']
        except:
            continue
        items.append({
            'label': page.text,
            'path': url_for('okcategory', url=url ,curl=curl)
        })
    return items


@plugin.route('/okmain/<url>/')
def okmain(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.find('div', {'class': 'sddm'})
    lists = tree.findAll('li')

    yield {
        'label': u'[COLOR yellow]搜索[/COLOR]',
        'path': url_for('oksearch'),
    }

    for item in lists[1:]:
        yield {
            'label': item.a.text,
            'path': url_for('okcategory', url=item.a['href'], curl=item.a['href']),
        }


# get search result by input keyword
@plugin.route('/yjsearch')
def yjsearch():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = YONGJIU + '/index.php?m=vod-search&wd=' + keyword
        return yjcategory(url)


@plugin.route('/yjepisodes/<url>/')
def yjepisodes(url):
    plugin.set_content('TVShows')
    video = get_html(httphead(YONGJIU, url))
    soup = BeautifulSoup(video, 'html.parser')
    title = soup.title.text
    title = r1('(.+?)-*', title)
    tree = soup.find('div', {'class': 'contentNR'})
    textinfo = tree.text
    tree = soup.find('div', {'class': 'videoPic'})
    thumb = tree.img['src']

    selmode = plugin.addon.getSetting('m3u8')
    lists = soup.findAll('input', {'type': 'checkbox'})
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
@plugin.route('/yjcategory/<url>/')
def yjcategory(url):
    plugin.set_content('TVShows')
    page = get_html(httphead(YONGJIU, url))
    soup = BeautifulSoup(page, 'html.parser')
    tree = soup.findAll('tr', {'class': 'DianDian'})
    items = []
    for item in tree:
        td = item.find('td', {'class': 'l'})
        url = td.a['href']
        text = item.td.text.replace('\n', ' ')
        items.append({
            'label': text,
            'path': url_for('yjepisodes', url=url)
        })

    page = soup.find('div', {'class': 'page_num'})
    pages = page.findAll('a')
    for page in pages:
        items.append({
            'label': page.text,
            'path': url_for('yjcategory', url=page['href'])
        })
    return items


# main entrance
@plugin.route('/yjmain/<url>/')
def yjmain(url):
    yongjiu = url
    url = ''
    home = get_html(yongjiu)
    if len(home) < 1000:
        prehome = re.search('var (.*);;', home)
        exec (prehome.group(1))

    home = get_html(yongjiu + url)

    soup = BeautifulSoup(home, 'html.parser')
    tree = soup.findAll('div', {'class': 'nav'})
    lists = tree[0].findAll('li')

    yield {
        'label': u'[COLOR yellow]搜索[/COLOR]',
        'path': url_for('yjsearch'),
    }

    for item in lists[1:]:
        yield {
            'label': item.a.text,
            'path': url_for('yjcategory', url=item.a['href']),
        }

# main entrance
@plugin.route('/')
def root():
    yield {
        'label': '永久资源',
        'path': url_for('yjmain', url=YONGJIU)
    }
    yield {
        'label': 'OK资源网',
        'path': url_for('okmain', url=OKZYW)
    }
    yield {
        'label': '记得87',
        'path': url_for('jdmain', url=JIDE87)
    }


if __name__ == '__main__':
    plugin.run()
