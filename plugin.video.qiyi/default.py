#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, DialogProgress, ListItem
import xbmcplugin
import xbmcaddon
from urlparse import parse_qsl
from urllib import quote_plus
import re
import sys
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from iqiyi import video_from_vid

########################################################################
# 爱奇艺 list.iqiyi.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cookieFile = __profile__ + 'cookies.iqiyi'

LIST_URL = 'http://list.iqiyi.com'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'
RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def selResolution(items):
    ratelist = []
    for i in range(0, len(items)):
        if items[i] == 96:
            ratelist.append([7, '极速', i])    # 清晰度设置值, 清晰度, match索引
        if items[i] == 1:
            ratelist.append([6, '流畅', i])
        if items[i] == 2:
            ratelist.append([5, '标清', i])
        if items[i] == 3:
            ratelist.append([4, '超清', i])
        if items[i] == 4 or items[i] == 17:
            ratelist.append([3, '720P', i])
        if items[i] == 5 or items[i] == 18:
            ratelist.append([2, '1080P', i])
        if items[i] == 10 or items[i] == 19:
            ratelist.append([1, '4K', i])
    ratelist.sort()
    if len(ratelist) > 1:
        resolution = int(__addon__.getSetting('resolution'))
        if resolution == 0:    # 每次询问点播视频清晰度
            dialog = Dialog()
            list = [x[1] for x in ratelist]
            sel = dialog.select('清晰度（低网速请选择低清晰度）', list)
            if sel == -1:
                return -1
        else:
            sel = 0
            while sel < len(ratelist)-1 and resolution > ratelist[sel][0]:
                sel += 1
    else:
        sel = 0
    return ratelist[sel][2]


def PlayVideo(params):
    url = params.get('url')
    tvId = params['tvId']
    videoId = params['vid']
    title = params['title']
    thumb = params['thumb']

    sel = 1
    real_urls = video_from_vid(tvId, videoId, level=sel)
    if real_urls is None:
        Dialog().ok(__addonname__, '无法播放此视频')
        return

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    ulen = len(real_urls)
    if ulen > 0:
        for i in range(0, ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            liz = ListItem(name, thumbnailImage='')
            liz.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(real_urls[i], liz)
    xbmc.Player().play(playlist)


def mainMenu():
    li = ListItem('[COLOR FF00FF00] 【爱奇艺 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = LIST_URL + '/www/2/----------------iqiyi--.html'
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'mod_category_item'})

    grp = soup[0].find_all('a')

    for prog in grp[:-1]:
        name = prog.text.strip(' ')
        href = httphead(prog['href'])
        li = ListItem(name)
        u = sys.argv[0] + '?url=' + quote_plus(href)
        u += '&mode=videolist&name=' + name.encode('utf-8')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    url = params['url']
    name = params['name']
    html = get_html(url)
    html = re.sub('\t|\r|\n', ' ', html)
    tree = BeautifulSoup(html, 'html.parser')

    ul = url.split('/')[-1]
    page = ul.split('-')[14]
    if page == '':
        page = '1'

    li = ListItem(name + '[第%s页](分类过滤)' % page)
    u = sys.argv[0] + '?url=' + url.encode('ascii')
    u += '&mode=filter&name=' + quote_plus(name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    li = ListItem(BANNER_FMT % '排序方式')
    u = sys.argv[0] + '?url=' + url
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('div', {'class': 'sort-result-l'})
    arrange = soup[0].find_all('a')
    for sort in arrange:
        href = httphead(sort['href'])
        title = sort.text
        select = sort.get('class', '')
        if 'selected' in select:
            title = INDENT_FMT1 % title
        else:
            title = INDENT_FMT0 % title
        li = ListItem(title)
        u = sys.argv[0] + '?url=' + href.encode('ascii')
        u += '&mode=videolist&name=' + quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('div', {'class': 'site-piclist_pic'})
    for item in soup:
        href = item.a.get('href')
        img = item.img.get('src', '')
        title = item.a.get('title', '')
        try:
            info = item.find('span', {'class': 'icon-vInfo'}).text
        except:
            info = ''
        info = info.strip(' ')
        try:
            vip = item.find('span', {'class': 'icon-vip-zx'}).text
            vip = '|[COLOR FF809000]' + vip + '[/COLOR]'
        except:
            vip = ''
        try:
            pay = item.find('span', {'class': 'icon-vip-quan'}).text
            pay = '|[COLOR FF809000]' + pay + '[/COLOR]'
        except:
            pay = ''
        albumId = item.a.get('data-qidanadd-albumid', 'X')
        tvId = item.a.get('data-qidanadd-tvid', 'X')
        if albumId == 'X':
            albumId = tvId
        li = ListItem(title + '(' + info + vip + pay + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href
        u += '&mode=episodelist&name=' + quote_plus(name)
        u += '&thumb=' + quote_plus(img) + '&title=' + title
        u += '&albumId=%s&tvId=%s' % (albumId, tvId)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    u = sys.argv[0]
    li = ListItem(INDENT_FMT0 % ('分页'))
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    pages = tree.find_all('div', {'class': 'mod-page'})
    pages = pages[0].find_all('a')
    for page in pages:
        title = page.text
        href = httphead(page['href'])
        li = ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def referenceList(params):
    url = params['url']
    tvId0 = params['tvId']
    thumb = params['thumb']
    title = params['title']
    videoId = params['vid']
    # recommend
    li = ListItem(BANNER_FMT % (title + '  相关视频'),
                          iconImage=thumb, thumbnailImage=thumb)
    u = sys.argv[0] + '?mode=playvideo&tvId=%s&vid=%s' % (tvId0, videoId)
    u += '&title=' + quote_plus(title)
    u += '&thumb=' + quote_plus(thumb) + '&url=' + url
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    url = 'http://mixer.video.iqiyi.com/jp/recommend/videos?referenceId=%s&area=swan&type=video' % tvId0
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    items = json_response['mixinVideos']
    for series in items:
        title = series['name']
        videoId = series['vid']
        tvId = series['tvId']
        albumId = series['albumId']
        thumb = series['imageUrl']
        info = series['description']
        url = series['url']
        li = ListItem(title, iconImage='thumb', thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={'Title': title,
                                             'Plot': info})
        u = sys.argv[0] + '?title=' + title + '&thumb=' + thumb
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
        u += '&url=' + url
        if tvId == tvId0:
            u += '&mode=playvideo'
            dir = False
        else:
            u += '&mode=reference'
            dir = True
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isFolder=dir)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listType1(albumType, albumId):
    url = 'http://cache.video.qiyi.com/jp/sdvlst/%d/%d/' % (albumType, albumId)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    if 'data' not in json_response:
        return False

    for item in json_response['data']:
        tvId = item['tvId']
        videoId = item['vid']
        p_thumb = item['aPicUrl']
        p_name = item['videoName'] + item['tvYear']
        li = ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=playvideo&title=' + p_name
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    return True


def listType2(albumId, page, thumb, title):
    url = 'http://cache.video.qiyi.com/avlist/%d/%s/50/' % (albumId, page)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)

    try:
        totalpages = json_response['data']['pgt']
    except:
        return False

    currpage = int(page)

    for item in json_response['data']['vlist']:
        tvId = item['id']
        videoId = item['vid']
        p_thumb = item['vpic']
        p_name = item['vn']
        desc = item['desc']
        seconds = item['timeLength']
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = '%02d:%02d' % (m, s)
        if h != 0:
            time = '%d:%s' % (h, time)
        if item['vt']:
            p_name = p_name + ' ' + item['vt']
        li = ListItem(p_name + '(' + time + ')',
                              iconImage=p_thumb, thumbnailImage=p_thumb)
        li.setInfo(type='Video', infoLabels={'Title': p_name,
                                             'Plot': desc})
        u = sys.argv[0] + '?mode=playvideo&title=' + p_name
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    um = sys.argv[0] + '?mode=episodelist&title=' + title
    um += '&albumId=%d' % (albumId) + '&thumb=' + thumb + '&page='
    if currpage > 1:
        li = ListItem('上一页')
        u = um + str(currpage-1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    if currpage < totalpages:
        li = ListItem('下一页')
        u = um + str(currpage+1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    return True


def episodesList(params):
    albumId = params['albumId']
    title = params['title']
    thumb = params['thumb']

    url = 'http://cache.video.qiyi.com/a/%s' % albumId
    print '==========================', url

    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    item = json_response['data']
    if item['tvYear']:
        p_year = item['tvYear']
    else:
        p_year = '0'
    p_director = ' / '.join(item['directors'])
    p_cast = [x for x in item['mainActors']]
    info = item['tvDesc']
    tvId = item['tvId']
    videoId = item['vid']
    albumType = item['albumType']
    albumId = item['albumId']
    params['tvId'] = str(tvId)
    params['vid'] = videoId
    params['url'] = item['purl']
    li = ListItem(BANNER_FMT % title,
                          iconImage=thumb, thumbnailImage=thumb)
    li.setInfo(type="Video", infoLabels={"Title": title, 'Plot': info})
    u = sys.argv[0] + '?mode=playvideo&title=' + title
    u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
    u += '&thumb=' + thumb + '&url=' + item['purl'].encode('utf-8')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    if albumId != int(tvId):
        res = listType1(albumType, albumId)
        if res is False:
            page = params.get('page', '1')
            res = listType2(albumId, page, thumb, title)

    # recommend
    params['tvId'] = str(albumId)
    referenceList(params)


def findToPlay(params):
    url = params.get('url')
    link = get_html(url)
    tvId = r1(r'#curid=(.+)_', self.url) or \
            r1(r'tvid=([^&]+)', self.url) or \
            r1(r'data-player-tvid="([^"]+)"', link)
    videoId = r1(r'#curid=.+_(.*)$', self.url) or \
            r1(r'vid=([^&]+)', self.url) or \
            r1(r'data-player-videoid="([^"]+)"', link)

    if tvId is not None and videoId is not None:
        params['tvId'] = tvId
        params['vid'] = videoId
        PlayVideo(params)
    else:
        albumId = r1('albumid="(.+?)"', link)
        params['tvId'] = ''
        if albumId is not None:
            params['albumId'] = albumId
            episodesList(params)


def changeList(params):
    url = params.get('url')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('div', {'class': 'mod_sear_list'})

    surl = url.split('/')
    lurl = surl[-1].split('-')

    dialog = Dialog()

    for item in filter[1:]:
        title = item.h3.text
        si = item.find_all('li')
        list = []
        for x in si:
            if x.get('class') and 'selected' in x.get('class'):
                list.append('[COLOR FFF0F000]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel].a['href'].split('/')
        selurl = selurl[-1].split('-')
        if len(selurl) < 10:
            continue
        for i in range(0, len(selurl)):
            if (selurl[i] != '') and (selurl[i] != lurl[i]):
                lurl[i] = selurl[i]

    surl[-1] = '-'.join(lurl)
    url = '/'.join(surl)
    params['url'] = httphead(url).encode('ascii')
    listSubMenu(params)


###########################################################################
# search in http://so.iqiyi.com/so/q_%s?source=hot
############################################################################
def searchiQiyi(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1000)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    key = quote_plus(keyword)
    url = 'http://so.iqiyi.com/so/q_' + key + '?source=hot'

    link = get_html(url)

    if link is None:
        li = ListItem(' 抱歉，没有找到[COLOR FFFF0000] ' + keyword + '   [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    li = ListItem('[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.find_all('ul', {'class': 'mod_result_list'})
    for items in soup:
        list = items.find_all('li', {'class': 'list_item'})
        for series in list:
            href = httphead(series.a['href'])
            try:
                img = series.img.get('src')
            except:
                img = ''
            try:
                title = series.img.get('title')
            except:
                title = series.a.get('title', '')
            if title == '':
                continue
            text = series.find('span', {'class': 'result_info_txt'})
            try:
                info = text.text
            except:
                info = ''
            site = series.find_all('em', {'class': 'vm-inline'})
            for t in site:
                title += ' |' + t.text
            li = ListItem(title, iconImage='', thumbnailImage=img)
            li.setInfo(type='Video',
                       infoLabels={'Title': title, 'Plot': info})

            u = sys.argv[0] + '?url=' + href + '&mode=playfound'
            u += '&thumb=' + quote_plus(img) + '&title=' + title
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
            album = series.find_all('li', {'class': 'album_item'})
            for page in album:
                href = page.a['href']
                title = page.a['title']
                li = ListItem('--' + title, thumbnailImage=img)
                u = sys.argv[0] + '?url=' + href + '&mode=playfound'
                u += '&thumb=' + quote_plus(img) + '&title=' + title
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
dialog = Dialog()
pDialog = DialogProgress()

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
#socket.setdefaulttimeout(10)

runlist = {
    None: 'mainMenu()',
    'videolist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'reference': 'referenceList(params)',
    'playfound': 'findToPlay(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchiQiyi(params)',
    'filter': 'changeList(params)'
}

exec(runlist[mode])
