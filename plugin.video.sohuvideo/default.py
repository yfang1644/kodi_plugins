#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from lib.sohu import video_from_url, urlparse, quote_plus, parse_qsl, urlencode
from iqiyi import video_from_url as video_from_iqiyi
from qq import video_from_url as video_from_qq
from funshion import video_from_url as video_from_fun
from youku import video_from_url as video_from_youku

########################################################################
# 搜狐视频 tv.sohu.com
########################################################################

# Plugin constants
LIST_URL = 'https://so.tv.sohu.com'

BANNER_FMT = '[COLOR FFDEB887] %s [/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'
EXTRA = '[COLOR FF8080FF] %s[/COLOR]'

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def playvideo(params):
    name = params['name']
    level = int(xbmcaddon.Addon().getSetting('resolution'))

    urls = video_from_url(params['url'], level=level)
    stackurl = 'stack://' + ' , '.join(urls)
    list_item = ListItem(name, thumbnailImage=params['thumbnail'])
    list_item.setInfo('video', {'title': name})
    xbmc.Player().play(stackurl, list_item)


def playvideo_other(params):
    site = params['site']
    url = params['url']
    if site == 'qq':
        resolver = video_from_qq
    elif site == 'fun':
        resolver = video_from_fun
    elif site == 'iqiyi':
        resolver = video_from_iqiyi
    elif site == 'youku':
        resolver = video_from_youku
    else:
        return

    level = int(xbmcaddon.Addon().getSetting('resolution'))
    urls = resolver(httphead(url), level=level)

    stackurl = 'stack://' + ' , '.join(urls)
    list_item = ListItem(name, thumbnailImage=params['thumbnail'])
    list_item.setInfo('video', {'title': name})
    xbmc.Player().play(stackurl, list_item)


def select(params):
    url = params['url']
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    filter = soup.findAll('dl', {'class': 'cfix'})

    dialog = Dialog()

    surl = url.split('/')
    lurl = r1('(.+?).html', surl[-1])
    lurl = lurl.split('_')

    for item in filter:
        title = item.dt.text.strip()
        si = item.findAll('a')
        list = []
        for x in si:
            if x.get('class') == ['aon']:
                list.append('[COLOR gold]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel]['href'].split('/')
        selurl = r1('(.+?).html', selurl[-1])
        selurl = selurl.split('_')
        for i in xrange(1, 14):
            if selurl[i] != 'p%d' % i:
                lurl[i] = selurl[i]

    surl[-1] = '_'.join(lurl) + '.html'
    url = '/'.join(surl)
    params['url'] = url
    videolist(params)


def sohuvideolist(playlistid):
    #listapi = 'http://hot.vrs.sohu.com/vrs_videolist.action?'
    #listapi = 'http://pl.hd.sohu.com/videolist?playlistid=9395603&order=0&cnt=1&withLookPoint=1&preVideoRule=1'
    listapi = 'http://pl.hd.sohu.com/videolist?playlistid=%s'

    link = get_html(listapi % playlistid, decoded=False)
    videos = loads(link.decode('gbk'))['videos']

    for item in videos:
        p_name = item['showName'].encode('utf-8')
        p_thumb = item['largePicUrl'].encode('utf-8')
        p_url = item['pageUrl'].encode('utf-8')
        p_vid = str(item['vid']).encode('utf-8')
        p_tvId = str(item['tvId']).encode('utf-8')
        li = ListItem(p_name, thumbnailImage=p_thumb)
        li.setInfo(type='Video',
                   infoLabels={'title':p_name, 'duration': int(item['playLength']), 'plot': item['videoDesc'], 'episode': int(item['order'])})
        req = {
            'mode': 'playvideo',
            'url': p_url,
            'name': p_name,
            'thumbnail': p_thumb
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)


def othersite(link):
    sitemap = {'qq': 'QQ', 'youku': '优酷', 'fun': '风行', 'iqiyi': '爱奇艺'}

    tree = BeautifulSoup(link, 'html.parser')
    soups = tree.findAll('div', {'class': 'episode cfix'})

    for soup in soups:
        lists = soup.findAll('a')
        for item in lists:
            spliturl = urlparse(item['href'])
            site = spliturl.netloc.split('.')[1]
            try:
                siteinfo = sitemap[site]
            except:
                continue
            title = item.text.encode('utf-8')
            li = ListItem(title + '(' + siteinfo + ')')
            req = {
                'mode': 'playvideo_other',
                'url': item['href'],
                'site': site,
                'name': title,
            }
            u = sys.argv[0] + '?' + urlencode(req)
            addDirectoryItem(int(sys.argv[1]), u, li, True)


def episodelist1(params):
    link = get_html(params['url'])

    match0 = r1('var playlistId\s*=\s*["|\'](.+?)["|\'];', link)
    match1 = r1('var PLAYLIST_ID\s*=\s*["|\'](.+?)["|\'];', link)

    match = [match0, match1]
    if len(match) > 0:
        if match[0] != '0':
            sohuvideolist(match[0])
        else:
            othersite(link)
    else:
        soup = BeautifulSoup(link, 'html.parser')
        tree = soup.findAll('ul', {'class': 'list list-120 cfix'})

        for part in tree:
            drama = part.findAll('li')

            for item in drama:
                img = httphead(item.img['src'])
                try:
                    title = item.strong.a['title']
                except:
                    title = item.a.text
                li = ListItem(title, thumbnailImage=img)
                req = {
                    'mode': 'episodelist1',
                    'url': httphead(item.a['href']),
                    'thumbnail': img
                }
                u = sys.argv[0] + '?' + urlencode(req)
                addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def episodelist2(params):
    link = get_html(params['url'])
    #soup = BeautifulSoup(link, 'html.parser')

    listapi = 'http://my.tv.sohu.com/play/getvideolist.do?playlistid=%s&pagesize=30&order=1'

    match0 = r1('playlistId\s*=\s*["|\'](.+?)["|\'];', link)

    link = get_html(listapi % match0)
    videos = loads(link)['videos']

    for item in videos:
        length = item['playLength']
        p_date = item['publishTime'].encode('utf-8')
        p_order = int(item['order'])
        vid = item['vid']
        title = item['subName'].encode('utf-8')
        img = item['largePicUrl']
        li = listing(title, thumbnailImage=img)
        req = {
            'mode': 'playvideo',
            'url': item['pageUrl'],
            'name': title,
            'thumbnail': img
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


###########################################################################
# Get user input for Sohu site search
############################################################################
def search(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    p_url = 'http://so.tv.sohu.com/mts?chl=&tvType=-2&wd='
    url = p_url + quote_plus(keyword)

    # construct url based on user selected item
    page = 1
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=%d' % page
    link = get_html(p_url)

    #########################################################################
    # Video listing for all found related episode title
    soup = BeautifulSoup(link, 'html.parser')
    tree = soup.findAll('div', {'class': 'ssItem cfix'})

    #########################################################################
    for page in tree[0]:
        try:
            p_url = httphead(page.a['href'])
        except:
            continue
        p_name = page.a['title'].encode('utf-8')
        img = httphead(page.img['src'])
        infop = page.find('p', {'class': 'des'})
        try:
            info = infop.text
        except:
            info = ''
        li = ListItem(p_name, thumbnailImage=httphead(page.imag['src']))
        li.setInfo(type='Video', infoLabels={'title': p_name, 'plot': info})
        req = {
            'mode': 'episodelist1',
            'url': p_url
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

        album = page.findAll('a', {'class': 'ts'})
        for series in album:
            img = httphead(page.img['src'])
            li = ListItem(series['title'], thumbnailImage=img)
            req = {
                'mode': 'playvideo',
                'url': p_url,
                'name': series['title'],
                'thumbnail': img
            }
            u = sys.argv[0] + '?' + urlencode(req)
            addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def videolist(params):
    url = params['url']
    name = params['name']
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    surl = url.split('/')
    lurl = r1('(.+?).html', surl[-1])
    lurl = lurl.split('_')
    p10 = lurl[10]
    page = int(p10[3:]) if len(p10) > 3 else 1

    li = ListItem(BANNER_FMT % ('【第%d页】(分类过滤)' % (page)))
    req = {
        'mode': 'select',
        'name': name,
        'url': url
    }
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    vlists = soup.findAll('ul', {'class': 'st-list'})
    lists = [] if len(vlists) == 0 else vlists[0].findAll('li')

    for item in lists:
        pic = item.find('div', {'class': 'st-pic'})
        href = pic.a.get('href')
        href = httphead(href)
        img = pic.img.get('src')
        img = httphead(img)
        try:
            hover = item.find('div', {'class': 'list-hover'})
            title = hover.a.text
        except:
            title = pic.img.get('alt')
        if len(title) == 0:
            title = pic.a.get('title', '')

        try:
            info = item.find('p', {'class': 'lh-info'}).text
        except:
            info = ''

        try:
            mask = item.find('span', {'class': 'maskTx'}).text
        except:
            mask = ''
        extra = ''
        auth = item.find('span', {'class': 'rl-hyuan'})
        if auth:
            extra += EXTRA % u'会员 '
        auth = item.find('span', {'class': 'rl-dbo'})
        if auth:
            extra += EXTRA % u'独播'

        if name in ('电视剧', '动漫', '综艺', '娱乐', '纪录片', '明星', '体育'):
            mode = 'episodelist1'
        elif name in ('搞笑', '游戏', '做饭', '科技', '学习考试', '自媒体'):
            mode = 'episodelist2'
        else:
            mode = 'playvideo'

        li = ListItem(title + ' ' + mask + extra, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'title': title, 'plot': info})
        req = {
            'mode': mode,
            'url': href,
            'name': title.encode('utf-8'),
            'thumbnail': img
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, isFolder=(mode!='playvideo'))

    li = ListItem(INDENT_FMT0 % '分页')
    u = sys.argv[0]
    addDirectoryItem(int(sys.argv[1]), u, li, False)

    pages = soup.findAll('div', {'class': 'ssPages area'})
    pages = [] if len(pages) == 0 else pages[0].findAll('a')
    for page in pages:
        li = ListItem(page['title'].encode('utf-8'))
        req = {
            'mode': 'videolist',
            'name': name,
            'url': httphead(page['href'])
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)
        
    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def root():
    li = ListItem('[COLOR FF00FF00] 【搜狐视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = '/list_p1_p2_p3_p4_p5_p6_p7_p8_p9_p10_p11_p12_p13.html'
    html = get_html(LIST_URL + url)

    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'sort-nav cfix'})

    grp = tree[0].findAll('a')
    for prog in grp[1:]:
        title = prog.text.strip().encode('utf-8')
        li = ListItem(title)
        req = {
            'mode': 'videolist',
            'name': title,
            'url': httphead(prog['href'])
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
runlist = {
    'videolist': 'videolist(params)',
    'episodelist1': 'episodelist1(params)',
    'episodelist2': 'episodelist2(params)',
    'search': 'search(params)',
    'select': 'select(params)',
    'playvideo': 'playvideo(params)',
    'playvideo_other': 'playvideo_other(params)'
}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
if mode:
    del (params['mode'])
    exec(runlist[mode])
else:
    root()

