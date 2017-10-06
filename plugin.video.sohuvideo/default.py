#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
import xbmcplugin
import xbmcaddon
from urlparse import parse_qsl
from urllib import quote_plus
import re
import sys
import datetime
from json import loads
from bs4 import BeautifulSoup
from common import get_html
from sohu import video_from_url, video_from_vid

########################################################################
# 搜狐视频 tv.sohu.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cookieFile    = __profile__ + 'cookies.sohu'

LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'
HOST_URL = 'http://tv.sohu.com'
LIST_URL = 'http://so.tv.sohu.com'
PROGRAM_URL = 'http://poll.hd.sohu.com/live/stat/menu-segment.jsonp?num=8&sid=%d'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'
EXTRA = '[COLOR FF8080FF] %s[/COLOR]'


def PlayVideo(params):
    vid = params.get('vid')
    tvId = params.get('tvId')
    if vid is None or tvId is None:
        url = params['url']
        urls = video_from_url(url, level=level)
    else:
        urls = video_from_vid(vid, level=level)

    thumb = params.get('thumb', '')
    name = params['title']
    level = int(__addon__.getSetting('resolution'))
    site = int(__addon__.getSetting('videosite'))


    ulen = len(urls)
    if ulen < 1:
        Dialog().ok(__addonname__, '节目暂不能播放')
        return

    playlist = xbmc.PlayList(0)
    playlist.clear()

    for i in range(0, ulen): 
        title = name + '(%d/%d)'% (i+1, ulen)
        li = ListItem(title, thumbnailImage=thumb)
        li.setInfo(type="Video", infoLabels={"Title": title})
        playlist.add(urls[i], li)

    xbmc.Player(0).play(playlist)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def mainMenu():
    li = ListItem('[COLOR FF00FF00] 【搜狐视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    name = u'电视直播'
    li = ListItem(name)
    u = sys.argv[0] + '?url=' + 'http://tvimg.tv.itc.cn/live/stations.jsonp'
    u += '&mode=livechannel&name=' + name

    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = '/list_p1_p2_p3_p4_p5_p6_p7_p8_p9_p10_p11_p12_p13.html'
    html = get_html(LIST_URL + url)
    html = re.sub('\r|\n|\t', ' ', html)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'sort-nav cfix'})

    grp = soup[0].find_all('a')
    for prog in grp[1:]:
        title = prog.text.strip(' ')
        href = prog['href']
        href = httphead(href)
        li = ListItem(title)
        u = sys.argv[0] + '?url=%s&mode=videolist&name=%s' % (href, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    url = params['url']
    name = params.get('name')
    html = get_html(url)
    html = re.sub('\r|\n|\t', ' ', html)
    tree = BeautifulSoup(html, 'html.parser')

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')
    p10 = lurl[10]
    page = int(p10[3:]) if len(p10) > 3 else 1
    li = ListItem(BANNER_FMT % (name+'【第%d页】(分类过滤)' % (page)))
    u = sys.argv[0] + '?url=' + quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    items = tree.find_all('ul', {'class': 'st-list'})
    items = items[0].find_all('li')

    for item in items:
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

        li = ListItem(title + ' ' + mask + extra,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        if name in ('电视剧', '动漫', '综艺', '娱乐', '纪录片', '明星', '体育'):
            mode = 'episodelist1'
        elif name in ('搞笑', '游戏', '做饭', '科技', '学习考试', '自媒体'):
            mode = 'episodelist2'
        else:
            mode = 'playvideo'
        u = sys.argv[0] + '?url=' + href
        u += '&mode=' + mode
        u += '&name=' + quote_plus(name)
        u += '&thumb=' + quote_plus(img)
        u += '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    u = sys.argv[0]
    li = ListItem(INDENT_FMT0 % ('分页'))
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    pages = tree.find_all('div', {'class': 'ssPages area'})
    pages = pages[0].find_all('a')
    for page in pages:
        title = page['title'].encode('utf-8')
        href = httphead(page['href'])
        li = ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('dl', {'class': 'cfix'})

    dialog = Dialog()

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')

    for item in filter:
        title = item.dt.text
        si = item.find_all('a')
        list = []
        for x in si:
            if x.get('class') == ['aon']:
                list.append('[COLOR FFF0F000]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel]['href'].split('/')
        selurl = re.compile('(.+?).html').findall(selurl[-1])
        selurl = selurl[0].split('_')
        for i in range(1, 14):
            if selurl[i] != 'p%d' % i:
                lurl[i] = selurl[i]

    surl[-1] = '_'.join(lurl) + '.html'
    url = '/'.join(surl)
    params['url'] = url
    listSubMenu(params)


def episodesList1(params):
    name = params['name']
    title0 = params.get('title', '')
    url = params['url']
    link = get_html(url)

    match0 = re.compile('var playlistId\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)
    match0 += re.compile('var PLAYLIST_ID\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)

    if len(match0) > 0:
        listapi = 'http://hot.vrs.sohu.com/vrs_videolist.action?'
        listapi = 'http://pl.hd.sohu.com/videolist?playlistid=9395603&order=0&cnt=1&withLookPoint=1&preVideoRule=1'
        listapi = 'http://pl.hd.sohu.com/videolist?playlistid=%s'

        link = get_html(listapi % match0[0], decoded=False)
        items = loads(link.decode('gbk'))['videos']

        for item in items:
            p_name = item['showName'].encode('utf-8')
            p_thumb = item['largePicUrl'].encode('utf-8')
            p_url = item['pageUrl'].encode('utf-8')
            p_vid = str(item['vid']).encode('utf-8')
            p_tvId = str(item['tvId']).encode('utf-8')
            info = {
                'label': p_name,
                'duration': int(item['playLength']),
                'plot': item['videoDesc'],
                'episode': int(item['order'])
            }

            li = ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
            li.setInfo(type="Video", infoLabels=info)
            u = sys.argv[0] + '?url=' + quote_plus(p_url) + '&mode=playvideo'
            u += '&name=' + name + '&title=' + p_name
            u += '&thumb=' + quote_plus(p_thumb)
            u += '&vid={}&tvId={}'.format(p_vid , p_tvId)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    else:
        tree = BeautifulSoup(link, 'html.parser')
        soup2 = tree.find_all('ul', {'class': 'list list-120 cfix'})

        if len(soup2) > 0:
            for part in soup2:
                drama = part.find_all('li')

                for item in drama:
                    img = httphead(item.img['src'])
                    try:
                        title = item.strong.a['title']
                    except:
                        title = item.a.text
                    href = httphead(item.a['href'])
                    li = ListItem(title, iconImage=img, thumbnailImage=img)
                    li.setInfo(type='Video', infoLabels={'Title': title})
                    u = sys.argv[0] + '?url=' + href + '&mode=episodelist1'
                    u += '&name=' + quote_plus(name) + '&thumb=' + img
                    u += '&title=' + title
                    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

        #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
        #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList2(params):
    name = params['name']
    title0 = params.get('title', '')
    url = params['url']
    link = get_html(url)
    tree = BeautifulSoup(link, 'html.parser')

    listapi = 'http://my.tv.sohu.com/play/getvideolist.do?playlistid=%s&pagesize=30&order=1'

    match0 = re.compile('playlistId\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)

    link = get_html(listapi % match0[0])
    jsdata = loads(link)['videos']

    for item in jsdata:
        p_name = item['subName'].encode('utf-8')
        p_thumb = item['largePicUrl'].encode('utf-8')
        p_url = item['pageUrl'].encode('utf-8')
        length = item['playLength']
        p_date = item['publishTime'].encode('utf-8')
        p_order = int(item['order'])
        vid = item['vid']
        li = ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?url=' + quote_plus(p_url)
        u += '&mode=playvideo&name=' + name
        u += '&title=' + quote_plus(p_name)
        u += '&thumb=' + quote_plus(p_thumb)
        u += '&vid=%d' % vid
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Menu List
############################################################################
def LiveChannel(params):
    url = params['url']
    name = params['name']
    link = get_html(url)
    link = link[link.find('=')+1: link.find(';channelList')]

    jsdata = loads(link)
    stations = jsdata['STATIONS']

    for item in stations:
        title = item['STATION_NAME'].encode('utf-8')
        p_thumb = item['STATION_PIC']
        id = item['STATION_ID']
        p_thumb = httphead(p_thumb)
        if item['IsSohuSource'] == 1:
            disp_title = INDENT_FMT0 % title
        else:
            disp_title = INDENT_FMT1 % title
        u = sys.argv[0] + '?mode=liveplay&id=%d' % id
        u += '&name=' + name + '&title=' + title

        u += '&thumb=' + quote_plus(p_thumb)
        html = get_html(PROGRAM_URL % id)

        schedule = ''
        try:
            program = loads(html)
        except:
            continue
        try:
            program = program['attachment'][0]['MENU_LIST']
        except:
            continue
        for s in program:
            schedule += '%s %s\n' % (s['START_TIME'], s['NAME'])
        li = ListItem(disp_title,
                              iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type='Video', infoLabels={'Title': disp_title, 'Plot': schedule})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Player
############################################################################
def LivePlay(params):
    id = params['id']
    channel = params['title']
    thumb = params['thumb']
    link = get_html(LIVEID_URL % id)
    parsed_json = loads(link.decode('utf-8'))
    url = httphead(parsed_json['data']['hls'].encode('utf-8'))

    # link = get_html(url)
    # parsed_json = loads(link.decode('utf-8'))
    # url = parsed_json['url'].encode('utf-8')
    li = ListItem(channel, iconImage='', thumbnailImage=thumb)
    xbmc.Player().play(url, li)


###########################################################################
# Get user input for Sohu site search
############################################################################
def searchSohu(params):
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

    li = ListItem('[COLOR FFFF0000]当前搜索:' + keyword + '[/COLOR]')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    #########################################################################
    # Video listing for all found related episode title
    tree = BeautifulSoup(link, 'html.parser')
    soup = tree.find_all('div', {'class': 'ssItem cfix'})

    #########################################################################
    for page in soup[0]:
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
        li = ListItem(p_name, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': p_name, 'Plot': info})
        u = sys.argv[0] + '?url=' + quote_plus(p_url)
        u += '&mode=episodelist&title=' + quote_plus(p_name)
        u += '&thumb=' + quote_plus(img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

        album = page.find_all('a', {'class': 'ts'})
        for series in album:
            title = series['title']
            href = httphead(series['href'])
            li = ListItem(title)
            u = sys.argv[0] + '?url=' + quote_plus(href)
            u += '&mode=playvideo&title=' + quote_plus(title)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'livechannel': 'LiveChannel(params)',
    'liveplay': 'LivePlay(params)',
    'videolist': 'listSubMenu(params)',
    'episodelist1': 'episodesList1(params)',
    'episodelist2': 'episodesList2(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchSohu(params)',
    'select': 'normalSelect(params)'
}

exec(runlist[mode])
