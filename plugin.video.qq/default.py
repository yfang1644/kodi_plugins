#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
import re
from bs4 import BeautifulSoup
from json import loads
from common import get_html
from lib.qq import video_from_url, video_from_vid, urlencode, quote_plus, parse_qsl

PAGESIZE = 20

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'

HOST_URL = 'https://v.qq.com'
CHANNEL_LIST = {'电视剧': 'tv',
                '综艺': 'variety',
                '电影': 'movie',
                '动漫': 'cartoon',
                '少儿': 'children',
                '娱乐': 'ent',
                '音乐': 'music',
                '纪录片': 'doco',
                '微电影': 'dv',
                '新闻': 'news',
                '体育': 'sports',
                '教育': 'education',
                '搞笑': 'fun',
                '时尚': 'fashion',
                '生活': 'life',
                '科技': 'tech',
                '知识': 'knowledge',
                '汽车': 'auto',
                '财经': 'finance'}

def httphead(url):
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url

############################################################################

def select(params):
    channel = params.get('channel')
    api = 'https://v.qq.com/x/bu/pagesheet/list?'
    req = {
        '_all': 1,
        'channel': channel,
        'pagesize': PAGESIZE,
        'listpage': 1,
    }
    html = get_html(api + urlencode(req))
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class':'filter_line'})

    dialog = Dialog()

    for t in tree:
        name = t.findAll('span')[0].text
        label = []
        type = []
        key = t['data-key']
        items = t.findAll('a')
        for x in items:
            label += [x.text]
            type += [x['data-value']]

        sel = dialog.select(name, label)

        if sel >= 0:
            req[key] = type[sel]

    req['title'] = params['title']
    mainlist(req)

def playvideo(params):
    sel = int(xbmcaddon.Addon().getSetting('resolution'))
    if sel == 4:
        list = ['流畅(270P)', '高清(360P)', '超清(720P)', '蓝光(1080P)']
        sel = Dialog().select('清晰度选择', list)
        if (sel < 0):
            return False

    url = params['url']
    if ('http://' in url) or ('https://' in url):
        urls = video_from_url(url, level=sel)
    else:
        urls = video_from_vid(url, level=sel)

    stackurl = 'stack://' + ' , '.join(urls)
    title = params['title']

    li = ListItem(title, thumbnailImage=params['thumbnail'])
    li.setInfo(type='Video', infoLabels={'Title': title})
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for url in urls:
        playlist.add(url, li)
    xbmc.Player().play(playlist)


def search(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    url = HOST_URL + '/x/search/?q=' + quote_plus(keyword)
    url += '&stag=0'

    link = get_html(url)
    if link is None:
        li = ListItem('抱歉，没有找到[COLOR FFFF0000]' + keyword + '[/COLOR]的相关视频')
        addDirectoryItem(int(sys.argv[1]), u, li, False)
        endOfDirectory(int(sys.argv[1]))
        return

    li = ListItem('[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]')
    u = sys.argv[0]
    addDirectoryItem(int(sys.argv[1]), u, li, False)

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.findAll('div', {'class': 'result_item'})

    for items in soup:
        href = httphead(items.a['href'])
        img = httphead(items.img['src'])
        title = items.img['alt']

        info = items.find('span', {'class': 'desc_text'})
        try:
            info = info.text
        except:
            info = ''

        req = {
            'title': title.encode('utf-8'),
            'mode': 'episodelist',
            'thumbnail': img,
            'url': href.encode('utf-8')
        }
        u = sys.argv[0] + '?' + urlencode(req)
        li = ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        addDirectoryItem(int(sys.argv[1]), u, li, True)

        list = items.findAll('div', {'class': 'item'})
        for series in list:
            subtitle = series.a.text.encode('utf-8')
            href = httphead(series.a['href'])
            li = ListItem(subtitle)
            li.setInfo(type='Video', infoLabels={'Title': subtitle})
            req = {
                'title': subtitle,
                'mode': 'playvideo',
                'url': href.encode('utf-8'),
                'thumbnail': ''
            }
            u = sys.argv[0] + '?' + urlencode(req)
            addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def episodelist(params):
    url = params['url']
    thumb = params['thumbnail']
    title = params['title']

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    info = tree.find('meta', {'name': 'description'})['content']

    match = re.compile('var LIST_INFO\s*=\s*({.*}).*\n').search(html)
    js = loads(match.group(1))

    for j, item in enumerate(js['vid']):
        try:
            p_title = js['data'][item]['title']
        except:
            p_title = title + '-' + str(j+1)
        vid = item
        try:
            img = js['data'][item]['preview']
        except:
            img = thumb
        img = httphead(img)
        li = ListItem(p_title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': p_title, 'Plot': info})
        req = {
            'title': p_title,
            'mode': 'playvideo',
            'url': vid,
            'thumbnail': img
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    li = ListItem(BANNER_FMT % '相关视频')
    u = sys.argv[0]
    addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.findAll('li', {'class': 'list_item'})
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
        li = ListItem(title, iconImage=img, thumbnailImage=img)
        req = {
            'title': quote_plus(title.encode('utf-8')),
            'mode': 'episodelist',
            'url': quote_plus(href),
            'thumbnail': img,
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'videos')
    endOfDirectory(int(sys.argv[1]))


def mainlist(params):
    channel = params['channel']
    page = int(params.get('page', 1))
    api = 'https://v.qq.com/x/bu/pagesheet/list?'
    req = {
        '_all': 1,
        'channel': channel,
        'pagesize': PAGESIZE,
        'listpage': page,
        'offset': 20*(page-1),
    }

    name = params.pop('title')
    params.update(req)
    html = get_html(api + urlencode(params))
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'filter_line'})

    t =soup.findAll('div', {'class':'filter_result'})
    total= int(t[0]['data-total'])
    total_page = total // PAGESIZE

    li = ListItem(BANNER_FMT % (name + ' (分类过滤)'))
    req = {
        'title': name,
        'mode': 'select',
        'channel': channel
    }
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    if page > 1:
        li = ListItem('上一页')
        req = {
            'title': name,
            'mode': 'mainlist',
            'channel': channel,
            'page': page - 1
        }
        params.update(req)
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    li = ListItem(BANNER_FMT % (name+' (分类过滤)'))

    tree = soup.findAll('div', {'class': 'list_item'})
    for mainpage in tree:
        img = mainpage.findAll(None, {'class': 'figure'})[0].findAll('img')[0]['src']
        info = mainpage.findAll(None, {'class': 'figure_desc'})
        if info: info = '(' + info[0].text + ')'
        else: info = ''
        cap = mainpage.findAll(None, {'class': 'figure_caption'})
        try:
            cap = cap[0].text
        except:
            cap = ''
        duration = 0
        try:
            for t in cap.split(':'):
                duration = duration*60 + int(t)
            cap = ''
        except:
            cap = '('+ cap + ')'

        title = mainpage.findAll(None, {'class': 'figure'})[0]['title']
        href = mainpage.findAll(None, {'class': 'figure'})[0]['href']
        vid = mainpage.findAll(None, {'class': 'figure'})[0]['data-float']
        mark = mainpage.find('i', {'class': 'mark_v'})
        if mark:
            info += '[COLOR FFD00080](%s)[/COLOR]' % mark.img['alt']

        img = httphead(img)
        li = ListItem(title + cap, iconImage=img, thumbnailImage=img)
        li.setInfo(type='video', infoLabels={'Title': title, 'plot': info, 'duration': duration})
        req = {
            'title': title.encode('utf-8'),
            'mode': 'episodelist' if duration==0 else 'playvideo',
            'url': href,
            'thumbnail': img
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, duration==0)

    if page <= total_page:
        li = ListItem('下一页')
        req = {
            'title': name,
            'mode': 'mainlist',
            'channel': channel,
            'page': page + 1
        }
        params.update(req)
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))

def root():
    li = ListItem('[COLOR FF808F00] 【腾讯视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    for name in CHANNEL_LIST:
        li = ListItem(name)
        req = {
            'title': name,
            'mode': 'mainlist',
            'channel': CHANNEL_LIST[name],
            'page': 1
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)
    endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
runlist = {
    None: 'root()',
    'mainlist': 'mainlist(params)',
    'episodelist': 'episodelist(params)',
    'search': 'search(params)',
    'select': 'select(params)',
    'playvideo': 'playvideo(params)'
}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')

if mode is not None:
    del(params['mode'])

exec(runlist[mode])
