#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui, xbmc
import xbmcaddon
from urllib import quote_plus
from json import loads
from bs4 import BeautifulSoup
from common import get_html, match1
from youku import video_from_url, video_from_vid

########################################################################
# 优酷 www.youku.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')

LIST_URL = 'http://list.youku.com'

BANNER_FMT = '[COLOR FFDEB887][%s][/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

############################################################################

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/playvideo/<url>')
def playvideo(url):
    level = int(__addon__.getSetting('resolution'))

    urls = video_from_url(url, level=level)

    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/playvid/<vid>')
def playvid(vid):
    level = int(__addon__.getSetting('resolution'))

    urls = video_from_vid(vid, level=level)

    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/select/<url>')
def select(url):
    filter = ''
    surl = url.split('/')
    purl = surl[-1][:-5].split('_')
    keystate = {'a': 0,            # 地区
                'ag': 0,           # 年龄
                'av': 0,           # AV
                'c': 0,            # 频道(不出现)
                'd': 0,            # 排序日期
                'g': 0,            # 门类
                'lg': 0,           # 语言
                'mt': 0,           # 音乐分类
                'pt': 0,           # 付费
                'pr': 0,           # 出品
                'r': 0,            # 时间
                'u': 0,            # 更新状态
                's': 0             # 排序方法
               }
    keyword = keystate.keys()

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    color = '[COLOR purple]%s[/COLOR]'

    lists = []
    soup = tree.find_all('div', {'class': 'item'})
    for iclass in soup[1:]:
        x = []
        si = iclass.find_all('li')
        label = iclass.label.text
        for subitem in si:
            title = subitem.text
            if subitem.get('class'):
                title = color % title
                href = ''
            else:
                href = subitem.a['href'].encode('utf-8')
            x.append(dict({title: href}))

        lists.append(dict({label: x}))

    sort = tree.find_all('div', {'class': 'yk-sort-item'})
    for iclass in sort:
        x = []
        si = iclass.find_all('li')
        label = iclass.span.text
        for subitem in si:
            title = subitem.text
            href = subitem.a['href'].encode('utf-8')
            x.append(dict({title: href}))

        lists.append(dict({label: x}))

    dialog = xbmcgui.Dialog()

    for item in lists:
        title = item.keys()[0]
        y = item[title]
        l = [x.keys()[0] for x in y]
        sel = dialog.select(title, l)

        if sel < 0:
            continue
        key = y[sel].keys()[0]
        filter += '|' + title + '(' + key + ')'
        seurl = y[sel][key]
        if seurl == '':
            continue

        seurl = seurl.split('/')[-1]
        seurl = seurl[:-5].split('_')
        ls = len(seurl)

        i = 0
        while i < ls:
            k, v = seurl[i], seurl[i+1]
            if v in keyword:
                v = ''
                i += 1
            else:
                i += 2
            if keystate[k] != 0:
                continue
            try:
                index = purl.index(k)
                if purl[index+1] not in keyword:
                    oldv = purl.pop(index+1)
                purl.insert(index+1, v)
            except:
                purl += [k, v]

            if oldv and (oldv != v):
                keystate[k] += 1

    surl[-1] = '_'.join(purl) + '.html'
    url = '/'.join(surl)

    return videolist(url=url, filter=filter.encode('utf-8'))


@plugin.route('/episodelist/<url>')
def episodelist(url):
    plugin.set_content('video')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    items = []

    # 主题视频
    #soup = tree.find_all('div', {'class': 'lists'})
    programs = tree.find_all('div', {'class': 'program'})
    if len(programs) < 1:
        info = tree.find('meta', {'name': 'description'})['content']
        title = tree.find('meta', {'name': 'title'})['content']
        items.append({
            'label': title,
            'path': url_for('playvideo', url=url),
            'is_playable': True,
            'info': {'title': title, 'plot': info}
        })
    else:
        for item in programs:
            dr = item.find('span', {'class': 'c-time'}).text
            duration = 0
            for t in dr.split(':'):
                duration = duration * 60 + int(t)
            items.append({
                'label': item['title'],
                'path': url_for('playvideo', url=httphead(item.a['href'])),
                'thumbnail': item.img['src'],
                'is_playable': True,
                'info': {'title': item['title'], 'duration': duration}
            })

    programs = tree.find_all('div', {'class': 'item '})

    for item in programs:
        intro = item.find('div', {'class': 'show_aspect'})
        items.append({
            'label': item['title'],
            'path': url_for('playvideo', url=httphead(item.a['href'])),
            'is_playable': True,
            'info': {'title': item['title'], 'plot': intro.text}
        })

    # 相关视频
    items.append({
        'label': BANNER_FMT % '相关视频',
        'path': url_for('stay')
    })
    soup = tree.find_all('div', {'class': 'textlists'})
    try:
        lists = soup[0].find_all('li')
        for item in lists:
            items.append({
                'label': item['title'],
                'path': url_for('playvideo', url=httphead(item.a['href'])),
                'is_playable': True,
                'info': {'title': item['title']}
            })
    except:
        pass

    cid = match1(html, 'catId:"(\d+)"')
    vid = match1(html, 'videoId:"(\d+)"')
    sid = match1(html, 'showid:"(\d+)"')
    pg = match1(html, 'playmode:"(\d+)"')

    api_rel = 'http://ykrec.youku.com/show/packed/list.json'

    api_rel += '?vid=%s&sid=%s&cate=%s' % (vid, sid, cid)
    api_rel += '&picSize=&apptype=1&pg=%s&module=9&pl=30' % (pg)
    html = get_html(api_rel)
    jsdata = loads(html.encode('utf-8'))
    jsdata = jsdata['data']
    for item in jsdata:
        items.append({
            'label': item['title'],
            'path': url_for('playvideo', url=httphead(item['playLink'])),
            'thumbnail': item['picUrl'],
            'is_playable': True,
            'info': {'title': item['title']}
        })
    return items


@plugin.route('/search/')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    keyword = keyboard.getText()
    key = quote_plus(keyword)
    searchapi = 'http://tv.api.3g.youku.com/openapi-wireless/videos/search/{}?pid=0ce22bfd5ef5d2c5&pz=500'

    link = get_html(searchapi.format(key))

    if link is None:
        xbmcgui.Dialog().ok(__addonname__,
                            ' 抱歉，没有找到[COLOR FFFF0000] ' + keyword +
                      ' [/COLOR]的相关视频')
        return []

    # fetch and build the video series episode list
    finds = loads(link)
    items = []
    for item in finds['results']:
        img = item['img']
        videoid = item['videoid']
        title = item['title']
        info = item['desc']
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration*60 + int(t)

        items.append({
            'label': item['title'],
            'path': url_for('playvid', vid=videoid),
            'thumbnail': item['img'],
            'is_playable': True,
            'info': {'title': item['title'], 'plot': item['desc'],
                     'duration': duration}
        })
    return items


@plugin.route('/videolist/<url>/<filter>')
def videolist(url, filter):
    filter1 = '' if filter == '0' else filter
    items = [{
        'label': BANNER_FMT % ('分类过滤: ' + filter1),
        'path': url_for('select', url=url)
    }]

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    # 分页
    soup = tree.find_all('ul', {'class': 'yk-pages'})
    try:
        pages = soup[0].find_all('li')
        for page in pages:
            try:
                href = page.a['href']
            except:
                continue
            items.append({
                'label': BANNER_FMT % page.text,
                'path': url_for('videolist', url=httphead(href), filter=filter)
            })
    except:
        pass

    # 剧目清单
    #items = soup[0].find_all('div', {'class': 'p-thumb'})
    lists = tree.find_all('div', {'class': 'yk-pack'})
    for item in lists:
        pay = item.find('span', {'class': 'vip-free'})
        if pay:
            pay = '([COLOR pink]%s' + pay.text + '[/COLOR])'
        else:
            pay = '%s'
        pt = item.find('span', {'class': 'p-time'})
        try:
            ptime = pt.text + ' '
        except:
            ptime = ''

        items.append({
            'label': item.a['title'] + pay % (ptime),
            'path': url_for('episodelist', url=httphead(item.a['href'])),
            'thumbnail': httphead(item.img['src']),
        })
    return items


@plugin.route('/')
def index():
    yield {
        'label': '[COLOR green] 【优酷视频 - 搜索】[/COLOR]',
        'path': url_for('search')
    }

    html = get_html(LIST_URL)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'yk-filter'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            continue
        yield {
            'label': prog.text,
            'path': url_for('videolist', url=httphead(href), filter='0')
        }


if __name__ == '__main__':
    plugin.run()
