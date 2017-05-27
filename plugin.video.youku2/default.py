#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import sys
import os
import gzip
import StringIO
import cookielib
import simplejson
from bs4 import BeautifulSoup
from common import get_html, match1
from youku import video_from_url as video_from_url

########################################################################
# 优酷 www.youku.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
#UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

LIST_URL = 'http://list.youku.com'

BANNER_FMT = '[COLOR FFDEB887][%s][/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'


############################################################################
def PlayVideo(params):
    url = params['url']
    title = params.get('title', '')
    thumb = params.get('thumb')
    level = int(__addon__.getSetting('resolution'))

    if level == 4:
        dialog = xbmcgui.Dialog()
        level = dialog.select('清晰度选择', ['流畅', '高清', '超清', '1080P'])
        level = max(0, level)

    urls = video_from_url(url, level=level)

    ulen = len(urls)
    if ulen > 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for i in range(ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
            listitem.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(urls[i], listitem)

        xbmc.Player().play(playlist)
    else:
        xbmcgui.Dialog().ok(__addonname__, '未匹配到VID')
        return


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【优酷视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = get_html(LIST_URL)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'yk-filter'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            break
        name = prog.text
        href = httphead(href)

        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    name = params['name']
    url = params['url']
    filter = params.get('filter', '')
    sort = params.get('sort', '')

    li = xbmcgui.ListItem(BANNER_FMT % (name+'(分类过滤 %s)' % filter.encode('utf-8')))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    # 分页
    soup = tree.find_all('ul', {'class': 'yk-pages'})
    pages = soup[0].find_all('li')
    for page in pages:
        try:
            href = page.a['href']
        except:
            continue
        title = page.text
        href = httphead(href)
        li = xbmcgui.ListItem(BANNER_FMT % title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # 剧目清单
    #items = soup[0].find_all('div', {'class': 'p-thumb'})
    items = tree.find_all('div', {'class': 'yk-pack'})
    for item in items:
        title = item.a['title']
        href = httphead(item.a['href'])
        img = httphead(item.img['src'])
        pay = item.find('span', {'class': 'vip-free'})
        if pay:
            pay = '([COLOR FFFF00FF]%s' + pay.text + '[/COLOR])'
        else:
            pay = '%s'
        pt = item.find('span', {'class': 'p-time'})
        try:
            ptime = pt.text + ' '
        except:
            ptime = ''
        li = xbmcgui.ListItem(title + pay % (ptime),
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=episodelist&title=' + title
        u += '&thumb=' + urllib.quote_plus(img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    name = params.get('name')
    filter = params.get('filter', '')
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
    color = '[COLOR FF00FF00]%s[/COLOR]'

    list = []
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

        list.append(dict({label: x}))

    sort = tree.find_all('div', {'class': 'yk-sort-item'})
    for iclass in sort:
        x = []
        si = iclass.find_all('li')
        label = iclass.span.text
        for subitem in si:
            title = subitem.text
            href = subitem.a['href'].encode('utf-8')
            x.append(dict({title: href}))

        list.append(dict({label: x}))

    dialog = xbmcgui.Dialog()

    for item in list:
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
    params['url'] = url

    params['filter'] = filter
    listSubMenu(params)


def episodesList(params):
    url = params['url']
    thumb = params['thumb']
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    # 主题视频
    #soup = tree.find_all('div', {'class': 'lists'})
    items = tree.find_all('div', {'class': 'program'})
    if len(items) < 1:
        desc = tree.find_all('meta', {'name': 'description'})
        info = desc[0]['content']
        title = params['title']
        p_thumb = params['thumb']
        u = sys.argv[0] + '?url=' + url
        u += '&mode=playvideo'
        u += '&title=' + urllib.quote_plus(title)
        u += '&thumb=' + p_thumb
        li = xbmcgui.ListItem(title,
                              iconImage=p_thumb, thumbnailImage=p_thumb)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
    else:
        for item in items:
            title = item['title']
            href = httphead(item.a['href'])
            img = item.img['src']
            t = item.find('span', {'class': 'c-time'})
            time = t.text
            u = sys.argv[0] + '?url=' + href
            u += '&mode=playvideo'
            u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
            u += '&thumb=' + img
            li = xbmcgui.ListItem(title + '(' + time + ')',
                                  iconImage=img, thumbnailImage=img)
            li.setInfo(type='Video', infoLabels={'Title': title})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    items = tree.find_all('div', {'class': 'item '})

    for item in items:
        title = item['title']
        href = httphead(item.a['href'])
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playvideo'
        u += '&thumb=' + thumb
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
    u = sys.argv[0] + '?url=' + url
    u += '&mode=episodelist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    # 相关视频
    soup = tree.find_all('div', {'class': 'textlists'})
    try:
        items = soup[0].find_all('li')
        for item in items:
            title = item['title']
            href = httphead(item.a['href'])
            u = sys.argv[0] + '?url=' + href
            u += '&mode=playvideo'
            u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
            li = xbmcgui.ListItem(title)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

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
    jsdata = simplejson.loads(html.encode('utf-8'))
    jsdata = jsdata['data']
    for item in jsdata:
        title = item['title']
        href = httphead(item['playLink'])
        img = item['picUrl']
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playvideo'
        u += '&title=' + title
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def searchInYouku(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    keyword = keyboard.getText()
    key = urllib.quote_plus(keyword)
    p_url = 'http://www.soku.com/search_video/q_'

    link = get_html(p_url + key)

    if link is None:
        li = xbmcgui.ListItem(' 抱歉，没有找到[COLOR FFFF0000] ' + keyword + ' [/COL  OR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup1 = content.find_all('div', {'class': 's_movie clearfix'})
    soup2 = content.find_all('div', {'class': 's_tv clearfix'})

    for item in soup1 + soup2:
        img = item.img['src']
        detail = item.find('div', {'class': 's_detail'})
        href = detail.a['href']
        title = detail.a.text
        info = item.find('div', {'class': 'info_cont'})
        info = info.span.text

        li = xbmcgui.ListItem(title, iconImage='', thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&thumb=' + img
        u += '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'videolist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchInYouku(params)',
    'select': 'normalSelect(params)'
}

exec(runlist[mode])
