#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from lib.youku import video_from_vid, video_from_url, urlencode, quote_plus, parse_qsl


HOST = 'http://tv.api.3g.youku.com'
BASEIDS = {
    'pid': '0ce22bfd5ef5d2c5',
    'guid': '12d60728bd267e3e0b6ab4d124d6c5f0',
    'ngdid': '357e71ee78debf7340d29408b88c85c4',
    'ver': '2.6.0',
    'operator': 'T-Mobile_310260',
    'network': 'WIFI',
    'launcher': 0
}

BANNER_FMT = '[COLOR gold][%s][/COLOR]'

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = 'https://list.youku.com' + url

    return url

category = [
    {'剧集':['show', 97]},
    {'电影':['show', 96]},
    {'综艺':['show', 85]},
    {'动漫':['show', 100]},
    {'少儿':['show', 177]},
    {'音乐':['show', 95]},
    {'教育':['show', 87]},
    {'纪实':['show', 84]},
    {'体育':['show', 98]},
    {'文化':['show', 178]},
    {'娱乐':['show', 86]},
    {'游戏':['show', 99]},
    {'资讯':['video', 91]},
    {'搞笑':['video', 94]},
    {'生活':['video', 103]},
    {'汽车':['video', 104]},
    {'科技':['video', 105]},
    {'时尚':['video', 89]},
    {'亲子':['video', 90]},
    {'旅游':['video', 88]},
    {'微电影':['video', 171]},
    {'网剧':['video', 172]},
    {'拍客':['video', 174]},
    {'创意视频':['video', 175]},
    {'自拍':['video', 176]},
    {'广告':['video', 102]}]


############################################################################
def previous_page(endpoint, page, total_page, params):
    if int(page) > 1:
        li = ListItem('上一页 - {0}/{1}'.format(page, str(total_page)))
        params = dict(parse_qsl(params))
        params['mode'] = endpoint
        params['p'] = int(page) - 1
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def next_page(endpoint, page, total_page, params):
    if int(page) < int(total_page):
        li = ListItem('下一页 - {0}/{1}'.format(page, str(total_page)))
        params = dict(parse_qsl(params))
        params['mode'] = endpoint
        params['p'] = int(page) + 1
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def playvideo(params):
    level = int(xbmcaddon.Addon().getSetting('resolution'))

    urls = video_from_vid(params['vid'], level=level)
    if not urls:
        Dialog().ok(xbmcaddon.Addon().getAddonInfo('name'), '无法播放此视频')
        return

    stackurl = 'stack://' + ' , '.join(urls)
    name = params['name']
    li = ListItem(name, thumbnailImage=params['thumbnail'])
    li.setInfo(type="video", infoLabels={"Title": name})
    xbmc.Player().play(stackurl, li)


def select(params):
    type = params['type']
    cid = params['c']
    url = 'https://list.youku.com/category/{}/c_{}.html'.format(type, cid)
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class':'item'})

    dialog = Dialog()

    ntype = {}
    for item in tree[1:]:
        c = item.findAll('li')
        lst = [x.text for x in c]
        sel = dialog.select(item.label.text, lst)
        if sel >= 0:
            try:
                surl = c[sel].a['href'].split('_')
                ntype[surl[-2]] = surl[-1].replace('.html', '').encode('utf-8')
            except:
                pass

    params.update(ntype)
    mainlist(params)


def search(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    keyword = keyboard.getText()
    key = quote_plus(keyword)

    searchapi = HOST + '/layout/smarttv/showsearch?'
    req = {'video_type':1, 'keyword': keyword}
    req.update(BASEIDS)
    link = get_html(searchapi + urlencode(req))
    results = loads(link)['results']

    for item in results:
        li = ListItem(item['showname'], thumbnailImage=item['show_vthumburl_hd'])
        req = {
            'mode': 'episodelist',
            'vid': item['showid']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)


    searchapi = HOST + '/openapi-wireless/videos/search/{}?'
    req = {'pz': 500}
    req.update(BASEIDS)

    link = get_html(searchapi.format(key) + urlencode(req))

    # fetch and build the video series episode list
    finds = loads(link)
    for item in finds['results']:
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration*60 + int(t)

        li = ListItem(item['title'], thumbnailImage=item['img'])
        li.setInfo(type='Video',
                   infoLabels={'title': item['title'], 'plot': item['desc'], 'duration': duration})
        req = {
            'mode': 'playvideo',
            'vid': item['videoId'],
            'name': item['title'],
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def episodelist(params):
    vid = params['vid']
    url = 'http://v.youku.com/v_show/id_{0}.html'.format(vid)
    html = get_html(url)

    m = r1('__INITIAL_DATA__\s*=({.+?\});', html)
    
    p = loads(m)
    try:
        series = p['data']['data']['nodes'][0]['nodes'][2]['nodes']
    except:
        series = p['data']['data']['nodes'][0]['nodes'][1]['nodes']
    content = p['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['desc']
    items = []
    for film in series:
        vid = film['data']['action']['value']
        title = film['data']['title'].encode('utf-8')
        li = ListItem(title, thumbnailImage=film['data']['img'])
        li.setInfo(type='video', infoLabels={'title': title, 'plot': content})
        req = {
            'mode': 'playvideo',
            'vid': vid,
            'name': title,
            'thumbnail': film['data']['img']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def mainlist(params):
    cid = params['c']
    type = params['type']
    page = params.get('p', 1)
    previous_page('mainlist', page, 300, params=urlencode(params))
    c = '分类'
    li = ListItem('[COLOR yellow][{0}][/COLOR]'.format(c))
    req = {
        'mode': 'select',
        'c': params['c'],
        'type': params['type']
    }
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    api = 'https://list.youku.com/category/page?'
    req = params.copy()
    req['p'] = page
    req.pop('title')
    html = get_html(api + urlencode(req))
    data = loads(html)

    series = (97, 85, 100, 177, 87, 84, 98, 178, 86, 99) 
    for item in data['data']:
        vid = item.get('videoId')
        if not vid:
            continue
        li = ListItem(item['title'] + '(' + item['summary'] +')',
                      thumbnailImage=httphead(item['img']))
        li.setInfo(type='Video',
                   infoLabels={'title': item['title'], 'plot': item.get('subTitle', '')})
        req = {
            'mode': 'episodelist' if int(cid) in series else 'playvideo',
            'vid': vid,
            'thumbnail': httphead(item['img']),
            'name': item['title'].encode('utf-8')
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li,
                         isFolder=True if int(cid) in series else False)

    next_page('mainlist', page, 300, params=urlencode(params))
    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def root():
    li = ListItem('[COLOR magenta][搜索][/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    for item in category:
        title = item.keys()[0]
        li = ListItem(title)
        req = {
            'mode': 'mainlist',
            'title': title,
            'type': item[title][0],
            'c': item[title][1],
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)
    endOfDirectory(int(sys.argv[1]))

# main programs goes here #########################################
runlist = {
    'mainlist': 'mainlist(params)',
    'episodelist': 'episodelist(params)',
    'search': 'search(params)',
    'select': 'select(params)',
    'playvideo': 'playvideo(params)'
}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
if mode:
    del (params['mode'])
    exec(runlist[mode])
else:
    root()
