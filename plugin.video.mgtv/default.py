#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
from bs4 import BeautifulSoup
import simplejson
from common import get_html, r1
from mgtv import video_from_vid

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
BANNER_FMT2 = '[COLOR FFDE0087]%s[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

LIST_URL = 'http://list.mgtv.com'
HOST_URL = 'http://www.mgtv.com'

RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if len(url) < 2:
        return url
    if url[:2] == '/b':
        url = HOST_URL + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def mainMenu():
    http = get_html(LIST_URL)
    tree = BeautifulSoup(http, 'html.parser')
    soup = tree.find_all('div', {'class': 'm-catgory-listbox'})

    title0 = soup[0].span.text
    items = soup[0].find_all('li')
    for item in items:
        name = item.a.text
        href = httphead(item.a['href'])
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=mainlist&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def changeList(params):
    url = params['url']
    name = params['name']
    filter = params.get('filter')

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'm-catgory-listbox'})

    surl = url.split('/')
    purl = surl[-1].split('-')

    dialog = xbmcgui.Dialog()

    filter = ''
    for iclass in soup[1:]:
        title = iclass.find('span', {'class': 'u-meta'}).text
        si = iclass.find_all('a')
        list = []
        item = []
        for subitem in si:
            list.append(subitem.text)
            item.append(subitem['href'])
        sel = dialog.select(title, list)

        if sel < 0:
            continue

        filter += '|' + title + '(' + si[sel].text + ')'
        seurl = si[sel]['href'].split('/')[-1]
        seurl = seurl.split('-')
        for i in range(0, len(purl)):
            if seurl[i] != '':
                purl[i] = seurl[i]

    surl[-1] = '-'.join(purl)
    params['url'] = '/'.join(surl)
    params['filter'] = filter

    listSubMenu(params)


def listSubMenu(params):
    url = params['url']
    name = params['name']
    filter = params.get('filter', '')
    filter = filter.encode('utf-8')
    li = xbmcgui.ListItem(BANNER_FMT % (name + '[分类过滤]' + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    soup = tree.find_all('ul', {'class': 'v-list-inner'})
    items = soup[0].find_all('li')
    for item in items:
        thumb = item.img['src']
        t = item.find('a', {'class': 'u-title'})
        title = t.text
        href = t['href']
        t = item.find('a', {'class': 'u-video'})
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        try:
            exinfo = '(' + item.em.text + ')'
        except:
            exinfo = ''

        # pay info
        pay = item.find('i', {'class': 'v-mark-v5'})
        if pay:
            pay = BANNER_FMT2 % ('(' + pay.text + ')')
        else:
            pay = ''

        pinfo = item.find('span', {'class': 'u-desc'})
        info = pinfo.text.replace(' ', '')
        li = xbmcgui.ListItem(title + exinfo + pay,
                              iconImage=thumb, thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(thumb)
        u += '&filter=' + urllib.quote_plus(filter)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # multiple pages
    setpage = tree.find_all('div', {'class': 'w-pages'})
    try:
        pages = setpage[0].find_all('li')
        for page in pages:
            try:
                title = page.a['title']
            except:
                continue
            href = page.a['href']
            if href == 'javascript:;':
                continue
            else:
                href = httphead(href)
            li = xbmcgui.ListItem(BANNER_FMT % title)
            u = sys.argv[0] + '?url=' + href + '&mode=mainlist'
            u += '&name=' + urllib.quote_plus(name)
            u += '&filter=' + urllib.quote_plus(filter)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    except:
        pass

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    url = params['url']
    name = params.get('name')
    episode_api = 'http://pcweb.api.mgtv.com/movie/list'   # ???
    episode_api = 'http://pcweb.api.mgtv.com/episode/list'
    episode_api += '?video_id=%s&page=%d&size=40'
    thumb = params.get('thumb')
    page = params.get('page', '0')
    page = int(page)
    if url[-1] == '/':    # is a directory
        html = get_html(url)
        id = r1('vid:\s*(\d+)', html)
    else:
        id = r1('(\d+).html', url)

    html = get_html(episode_api % (id, page))
    jsdata = simplejson.loads(html)

    data = jsdata['data']
    list = data.get('list')
    total_page = data.get('total_page', 1)

    playlist = xbmc.PlayList(1)
    playlist.clear()
    j = 0
    for series in list:
        title = series['t1'] + ' ' + series['t2']
        if series['isnew'] != '0':
            title = title + u'(预)'
        img = series['img']
        href = httphead(series['url'])
        vid = series['video_id']

        vip = series.get('isvip')
        if vip and vip != '0':
            pay = '(VIP)'
        else:
            pay = ''

        li = xbmcgui.ListItem(title + pay, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo'
        u += '&thumb=' + img + '&vid=%d.%s' % (j, vid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        playlist.add(vid, li)
        j += 1

    short = data.get('short')
    for series in short:
        title = series['t1'] + ' ' + series['t2']
        if series['isnew'] != '0':
            title = title + u'(预)'
        img = series['img']
        href = httphead(series['url'])
        vid = series['video_id']

        vip = series.get('isvip')
        if vip and vip != '0':
            pay = '(VIP)'
        else:
            pay = ''

        li = xbmcgui.ListItem(title + pay, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo'
        u += '&thumb=' + img + '&vid=%d.%s' % (j, vid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        playlist.add(vid, li)
        j += 1

    if page > 0:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + url + '&mode=episodelist'
        u += '&thumb=' + thumb + '&page=%d' % (page-1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    if page < total_page - 1:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + url + '&mode=episodelist'
        u += '&thumb=' + thumb + '&page=%d' % (page+1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    related = data.get('related')
    if related:
        title = related['t1'] + ' ' + related['t2']
        img = related['img']
        href = httphead(related['url'])

        li = xbmcgui.ListItem(BANNER_FMT2 % title,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playVideo(params):
    level = int(__addon__.getSetting('resolution'))
    thumb = params['thumb']
    vid = params['vid'].split('.')
    v_pos = int(vid[0])
    vid = vid[1]

    playlistA = xbmc.PlayList(1)
    playlist = xbmc.PlayList(0)
    playlist.clear()
    psize = playlistA.size()

    playmode = __addon__.getSetting('video_vplaycont')

    for x in range(v_pos, psize):
        p_item = playlistA.__getitem__(x)
        p_vid = p_item.getfilename(x)
        p_list = p_item.getdescription(x)
        li = p_item      # pass all li items including the embedded thumb image
        li.setInfo(type='Video', infoLabels={'Title': p_list})

        m3u_url = video_from_vid(p_vid, level=level)

        playlist.add(m3u_url, li)
        if x == v_pos:
            xbmc.Player(0).play(playlist)
        if playmode == 'false':
            break

    '''
    urllist = get_mgtv_real_url(m3u_url)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    ulen = len(urllist)
    for i in range(ulen):
        playlist.add(urllist[i], li)

    xbmc.Player().play(playlist)
    '''

# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'mainlist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo(params)'
    }

exec(runlist[mode])
