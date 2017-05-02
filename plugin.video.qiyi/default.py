# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import urlparse
import re
import sys
import os
import gzip
import StringIO
import cookielib
import socket
import hashlib
import time
from random import random
import simplejson
from bs4 import BeautifulSoup

########################################################################
# 爱奇艺 list.iqiyi.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cookieFile = __profile__ + 'cookies.iqiyi'

if (__addon__.getSetting('keyboard') != '0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

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


def httpBegin0(url):
    surl = url.split('/')
    hurl = surl[-1].split('-')
    hurl[10] = '0'
    hurl = '-'.join(hurl)
    url = '/'.join(surl)
    return url


############################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
############################################################################
def getHttpData(url):
    charset = ''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req, timeout=2.0)
        httpdata = response.read()
        if httpdata[-1] == '\n':    # some windows zip files have extra '0a'
            httpdata = httpdata[:-1]
        if response.headers.get('Content-Encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        xbmc.log("%s: %s (%d) [%s]" % (
            __addonname__,
            sys.exc_info()[2].tb_frame.f_code.co_name,
            sys.exc_info()[2].tb_lineno,
            sys.exc_info()[1]
            ), level=xbmc.LOGERROR)
        return ''
    httpdata = re.sub('\r|\n|\t', ' ', httpdata)

    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')

    return httpdata


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
            dialog = xbmcgui.Dialog()
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


def getVMS(tvid, vid):
    t = int(time.time() * 1000)
    src = '76f90cbd92f94a2e925d83e8ccd22cb7'
    key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
    sc = hashlib.md5(str(t) + key + vid).hexdigest()
    vmsreq = 'http://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid,vid,t,sc,src)

    return simplejson.loads(getHttpData(vmsreq))


def PlayVideo(params):
    tvId = params['tvId']
    videoId = params['vid']
    title = params['title']
    thumb = params['thumb']

    info = getVMS(tvId, videoId)
    if info["code"] != "A00000":
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '无法播放此视频')
        return

    vs = info["data"]["vidl"]
    sel = selResolution([x['vd'] for x in vs])
    if sel == -1:
        return

    video_links = vs[sel]["m3u"]

    listitem = xbmcgui.ListItem(title, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": title})
    xbmc.Player().play(video_links, listitem)


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【爱奇艺 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = LIST_URL + '/www/1/----------------iqiyi--.html'
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'mod_category_item'})

    grp = soup[0].find_all('a')

    for prog in grp[:-1]:
        name = prog.text.strip(' ')
        href = httphead(prog['href'])
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&mode=videolist&name=' + name.encode('utf-8')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    url = params['url']
    name = params['name']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    ul = url.split('/')[-1]
    page = ul.split('-')[14]
    if page == '':
        page = '1'

    li = xbmcgui.ListItem(name + '[第%s页](分类过滤)' % page)
    u = sys.argv[0] + '?url=' + url.encode('ascii')
    u += '&mode=filter&name=' + urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    li = xbmcgui.ListItem(BANNER_FMT % '排序方式')
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
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href.encode('ascii')
        u += '&mode=videolist&name=' + urllib.quote_plus(name)
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
        except:
            vip = ''
        albumId = item.a.get('data-qidanadd-albumid', 'X')
        tvId = item.a.get('data-qidanadd-tvid', 'X')
        if albumId == 'X':
            albumId = tvId
        li = xbmcgui.ListItem(title + '(' + info + '|' + vip + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href
        u += '&mode=episodelist&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(img) + '&title=' + title
        u += '&albumId=%s&tvId=%s' % (albumId, tvId)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    u = sys.argv[0] + '?url=' + href
    li = xbmcgui.ListItem(INDENT_FMT0 % ('分页'))
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    pages = tree.find_all('div', {'class': 'mod-page'})
    pages = pages[0].find_all('a')
    for page in pages:
        title = page.text
        href = httphead(page['href'])
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def referenceList(params):
    tvId0 = params['tvId']
    thumb = params['thumb']
    title = params['title']
    videoId = params['vid']
    # recommend
    li = xbmcgui.ListItem(BANNER_FMT % (title + '  相关视频'),
                          iconImage=thumb, thumbnailImage=thumb)
    u = sys.argv[0] + '?mode=playvideo&tvId=%s&vid=%s' % (tvId0, videoId)
    u += '&title=' + urllib.quote_plus(title)
    u += '&thumb=' + urllib.quote_plus(thumb)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    url = 'http://mixer.video.iqiyi.com/jp/recommend/videos?referenceId=%s&area=swan&type=video' % tvId0
    link = getHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)
    items = json_response['mixinVideos']
    for series in items:
        title = series['name']
        videoId = series['vid']
        tvId = series['tvId']
        albumId = series['albumId']
        thumb = series['imageUrl']
        info = series['description']
        li = xbmcgui.ListItem(title, iconImage='thumb', thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={'Title': title,
                                             'Plot': info})
        u = sys.argv[0] + '?title=' + title + '&thumb=' + thumb
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
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
    link = getHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)
    if 'data' not in json_response:
        return False

    for item in json_response['data']:
        tvId = item['tvId']
        videoId = item['vid']
        p_thumb = item['aPicUrl']
        p_name = item['videoName'] + item['tvYear']
        li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=playvideo&title=' + p_name
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
    
    return True


def listType2(albumId, page, thumb, title):
    url = 'http://cache.video.qiyi.com/avlist/%d/%s/' % (albumId, page)
    link = getHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)

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
        if item['vt']:
            p_name = p_name + ' ' + item['vt']
        li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=playvideo&title=' + p_name
        u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    um = sys.argv[0] + '?mode=episodelist&title=' + title
    um += '&albumId=%d' % (albumId) + '&thumb=' + thumb + '&page='
    if currpage > 1:
        li = xbmcgui.ListItem('上一页')
        u = um + str(currpage-1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    if currpage < totalpages:
        li = xbmcgui.ListItem('下一页')
        u = um + str(currpage+1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    return True


def episodesList(params):
    albumId = params['albumId']
    title = params['title']
    thumb = params['thumb']

    url = 'http://cache.video.qiyi.com/a/%s' % albumId
    link = getHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)
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

    print '=============albumId %d, albumType %d tvId %d======' % (albumId, albumType, tvId)

    li = xbmcgui.ListItem(BANNER_FMT % title, iconImage=thumb, thumbnailImage=thumb)
    li.setInfo(type="Video", infoLabels={"Title": title, 'Plot': info})
    u = sys.argv[0] + '?mode=playvideo&title=' + title
    u += '&tvId=%d&vid=%s' % (tvId, videoId.encode('utf-8'))
    u += '&thumb=' + thumb
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
    link = getHttpData(url)
    tvId = re.compile('data-player-tvid="(.+?)"', re.DOTALL).findall(link)
    videoId = re.compile('data-player-videoid="(.+?)"', re.DOTALL).findall(link)
    if len(tvId) > 0 and len(videoId) > 0:
        params['tvId'] = tvId[0]
        params['vid'] = videoId[0]
        PlayVideo(params)
    else:
        albumId = re.compile('albumid="(.+?)"', re.DOTALL).findall(link)
        params['tvId'] = ''
        if len(albumId) > 0:
            params['albumId'] = albumId[0]
            episodesList(params)
        else:
            return


def changeList(params):
    url = params.get('url')
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('div', {'class': 'mod_sear_list'})

    surl = url.split('/')
    lurl = surl[-1].split('-')

    dialog = xbmcgui.Dialog()

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
    keyboard = Apps('', '请输入搜索内容')
    xbmc.sleep(1000)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    key = urllib.quote_plus(keyword)
    url = 'http://so.iqiyi.com/so/q_' + key + '?source=hot'

    link = getHttpData(url)

    if link is None:
        li = xbmcgui.ListItem(' 抱歉，没有找到[COLOR FFFF0000] ' + keyword + '   [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]')
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
            li = xbmcgui.ListItem(title, iconImage='', thumbnailImage=img)
            li.setInfo(type='Video',
                       infoLabels={'Title': title, 'Plot': info})

            u = sys.argv[0] + '?url=' + href + '&mode=playfound'
            u += '&thumb=' + urllib.quote_plus(img) + '&title=' + title
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
            album = series.find_all('li', {'class': 'album_item'})
            for page in album:
                href = page.a['href']
                title = page.a['title']
                li = xbmcgui.ListItem('--' + title, thumbnailImage=img)
                u = sys.argv[0] + '?url=' + href + '&mode=playfound'
                u += '&thumb=' + urllib.quote_plus(img) + '&title=' + title
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
dialog = xbmcgui.Dialog()
pDialog = xbmcgui.DialogProgress()

params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')
socket.setdefaulttimeout(10)

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

eval(runlist[mode])
