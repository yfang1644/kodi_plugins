#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcgui
from urlparse import parse_qsl
from urllib import quote_plus, urlencode
import re
from bs4 import BeautifulSoup
from json import loads, dumps
from common import get_html
from lib.qq import video_from_url, video_from_vid

plugin = Plugin()
url_for = plugin.url_for

# Plugin constants

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

HOST_URL = 'https://v.qq.com'

def httphead(url):
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


@plugin.route('/search/')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    url = HOST_URL + '/x/search/?q=' + quote_plus(keyword)
    url += '&stag=0'

    link = get_html(url)
    items = []
    if link is None:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            ' 抱歉，没有找到[COLOR FFFF0000] ' + keyword
                            + ' [/COLOR]的相关视频')
        return items

    items.append({
        'label': '[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]',
    })

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.find_all('div', {'class': 'result_item'})

    for item in soup:
        href = httphead(item.a['href'])
        img = httphead(item.img['src'])
        title = item.img['alt']

        info = item.find('span', {'class': 'desc_text'})
        try:
            info = info.text
        except:
            info = ''
        items.append({
            'label': title,
            'path': url_for('episodelist', url=href),
            'thumbnail': img,
            'info': {'title': title, 'plot': info}
        })

        list = item.find_all('div', {'class': 'item'})
        for series in list:
            subtitle = series.a.text
            href = httphead(series.a['href'])
            items.append({
                'label': subtitle,
                'path': url_for('playvideo', vid=href),
                'is_playable': True,
                'info': {'title': subtitle}
            })
    return items


@plugin.route('/playvideo/<vid>')
def playvideo(vid):
    sel = int(plugin.addon.getSetting('resolution'))
    if sel == 4:
        list = ['流畅(270P)', '高清(360P)', '超清(720P)', '蓝光(1080P)']
        sel = xbmcgui.Dialog().select('清晰度选择', list)
        if (sel < 0):
            return False, False

    urls = video_from_vid(vid, level=sel)

    if urls is False:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '无法获取视频地址')
        return

    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/select/<url>')
def select(url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    dialog = xbmcgui.Dialog()

    setparam = ''
    for iclass in soup:
        si = iclass.find_all('a')
        list = []
        item = []
        for subitem in si:
            list.append(subitem.text)
            item.append(subitem['href'])
        sel = dialog.select(iclass.span.text, list)

        if sel >= 0:
            setparam += item[sel]

    setparam = setparam.replace('?', '&')
    params = dict(parse_qsl(setparam.strip('&')))
    return mainlist(url, data=dumps(params))


@plugin.route('/serieslist/<name>/<url>')
def serieslist(name, url):
    html = get_html(url)
    html = re.sub('\t|\n|\r| ', '', html)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('span', {'class': 'item'})

    info = tree.find('meta', {'name': 'description'})['content']
    img = tree.find('meta', {'itemprop': 'image'})['content']

    for item in soup:
        try:
            p_title = item.a['title']
        except:
            continue
        try:
            href = httphead(item.a['href'])
        except:
            continue
        tn = item.a.text
        title = p_title + '--' + tn
        yield {
            'label': title,
            'path': url_for('playvideo', vid=0),
            'thumbnail': img,
            'info': {'title': title, 'plot': info}
        }


@plugin.route('/episodelist/<url>')
def episodelist(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    info = tree.find('meta', {'name': 'description'})['content']
    thumb = tree.find('meta', {'itemprop': 'thumbnailUrl'})['content']
    match = re.compile('var LIST_INFO\s*=\s*({.*}).*\n').search(html)
    js = loads(match.group(1))

    items = []
    for j, item in enumerate(js['vid']):
        try:
            p_title = js['data'][item]['title']
        except:
            p_title = str(j+1)
        try:
            img = js['data'][item]['preview']
        except:
            img = thumb
        img = httphead(img)
        items.append({
            'label': p_title,
            'path': url_for('playvideo', vid=item),
            'is_playable': True,
            'thumbnail': img,
            'info': {'title': p_title, 'plot': info}
        })

    soup = tree.find_all('li', {'class': 'list_item'})
    for item in soup:
        vid = item.get('data-vid')
        if not vid:
            vid = item.get('id', '')
        img = item.img.get('r-lazyload')
        if not img:
            img = item.img.get('src')
        if not img:
            img = ''
        img = httphead(img)
        href = httphead(item.a['href'])
        href = href.replace('?', '&')
        titlemsg = item.find('a', {'_stat': 'tabs-columns:title'})
        if titlemsg:
            title = titlemsg.text
        else:
            try:
                title = item.img['alt']
            except:
                title = item.a['title']
        items.append({
            'label': title,
            'path': url_for('episodelist', url=href),
            'thumbnail': img
        })

    return items


@plugin.route('/otherlist/<url>/<data>')
def otherlist(url, data):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'nav_area'})
    list1 = soup[0].find_all('a')
    soup = tree.find_all('div', {'class': 'slider_nav'})
    list2 = soup[0].find_all('a')

    items = []
    for item in list1 + list2:
        title = item.text
        href = httphead(item['href'])
        try:
            img = httphead(item['data-bgimage'])
        except:
            img = 'xxx'
        items.append({
            'label': title,
            'path': url_for('episodelist', url=href),
            'thumbnail': img
        })

    items.append({
        'label': BANNER_FMT % '其他视频',
        'path': url_for('otherlist', url=url)
    })

    soup = tree.find_all('ul', {'class': 'figures_list'})
    for group in soup:
        listitem = group.find_all('li', {'class': 'list_item'})
        for item in listitem:
            title = item.a['title']
            href = item.a['href']
            try:
                img = item.img['src']
            except:
                img = item.img['lz_src']
            items.append({
                'label': title,
                'path': url_for('episodelist', url=href),
                'thumbnail': img
            })

    return items


@plugin.route('/mainlist/<url>/<data>/')
def mainlist(url, data):
    plugin.set_content('TVShows')
    params = loads(data)
    html = get_html(url + '?' + urlencode(params))
    print "XXXXXXXXXXXXXXXXXXXX",url+'?'+urlencode(params)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})
    
    items = []
    items.append({
        'label': BANNER_FMT % '分类过滤',
        'path': url_for('select', url=url)
    })

    soup = tree.find_all('li', {'class': 'list_item'})
    for mainpage in soup:
        img = httphead(mainpage.img['r-lazyload'])
        title = mainpage.strong.a.text
        info = mainpage.find('span', {'class': 'figure_info'})
        if info:
            info = '(' + info.text + ')'
        else:
            info = ''
        href = mainpage.strong.a['href']
        mark = mainpage.find('i', {'class': 'mark_v'})
        if mark:
            info += '[COLOR FFD00080](' + mark.img['alt'] + ')[/COLOR]'

        items.append({
            'label': title + info,
            'path': url_for('episodelist', url=href),
            'thumbnail': img,
        })

    # PAGE LISTING
    soup = tree.find_all('div', {'class': 'mod_pages'})
    if len(soup) > 0:
        pages = soup[0].find_all('a')
        for site in pages:
            title = site.text
            href = site['href']
            try:
                offset = re.compile('=(\d+)').findall(href)[0]
            except:
                continue
            #  href looks like '?&offset=30'
            params['offset'] = offset
            items.append({
                'label': title,
                'path': url_for('mainlist', url=url, data=dumps(params))
            })

    return items


@plugin.route('/')
def root():
    plugin.set_content('TVShows')
    html = get_html('https://v.qq.com/x/list/tv')
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_list'})
    channels = soup[0].find_all('a')

    yield {
        'label': '[COLOR FF808F00] 【腾讯视频 - 搜索】[/COLOR]',
        'path': url_for('search')
    }

    for item in channels:
        name = item.text.encode('utf-8')
        url = item['href']
        if name in ('微电影', '时尚', '原创',
                      '生活', '财经', '汽车', '科技'):
            mode = 'otherlist'
        else:
            mode = 'mainlist'
        yield {
            'label': name,
            'path': url_for(mode, url=httphead(url), data='{"offset":0}'),
        }


if __name__ == '__main__':
    plugin.run()
