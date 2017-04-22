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
import simplejson
from bs4 import BeautifulSoup
from youku import getaddress_by_vid
from youku import get_content as getHttpData

########################################################################
# 土豆 www.tudou.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8')).decode("utf-8")

if (__addon__.getSetting('keyboard')=='0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
#UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

HOST_URL = 'http://www.tudou.com'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'


############################################################################
def PlayVideo(params):
    title = params.get('title', '')
    thumb = params.get('thumb')
    level = int(__addon__.getSetting('resolution'))

    vcode = params.get('vcode')
    iid = params.get('iid')

    if vcode:
        urls = getaddress_by_vid(vcode, stream_id=level)
    elif iid:
        urls = tudou_download_by_iid(iid)
    else:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '未匹配到VID')
        return

    ulen = len(urls)
    if ulen > 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for i in range(0, ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
            listitem.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(urls[i], listitem)

        xbmc.Player().play(playlist)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


def tudou_download_by_iid(iid):
    url = 'http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s'
    html = getHttpData(url % iid, headers={'User-Agent': UserAgent})
    data = simplejson.loads(html)

    key = data.keys()
    temp = data[key[-1]]

    vids = [t['k'] for t in temp]
    urls = []
    for vid in vids:
        html = getHttpData('http://cnc.v2.tudou.com/f?id=%d&jp=1' % vid,
                           headers={'User-Agent': UserAgent})
        y = re.compile('<f.+?>(http.+?)<\/f>').findall(html)
        y = y[0].replace('&amp;', '&')
        urls.append(y.strip())

    return urls


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def tudou_download_by_id(id):
    html = getHttpData('http://www.tudou.com/programs/view/%s/' % id,
                       headers={'User-Agent': UserAgent})

    iid = r1(r'iid\s*[:=]\s*(\S+)', html)
    tudou_download_by_iid(iid)


def buildParams(params):
    str = ''
    for item in params:
        str += '&%s=' % item + urllib.quote_plus(params[item])
    return str


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【土豆视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = HOST_URL + '/list/index_list.html'

    html = getHttpData(url, headers={'User-Agent': UserAgent})
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'menu'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        title = prog.text
        href = prog.a['href']
        href = httphead(href)
        nametype = href.split('/')[-1][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        elif nametype == 'ich':
            mode = 'videolist2'

        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=%s&mode=%s&name=%s' % (href, mode, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu1(params):
    # http://www.tudou.com/list/ach3a-2b-2c-2d-2e-2f1003g-2h-2i-2j-2k-2l-2m-2n1sort2.html
    # http://www.tudou.com/list/ach3a42b55c324d-2e-2f1003g-2h-2i-2j-2k-2l-2m-2n-2sort2.html
    #a42:地区
    #b55:类型
    #c324:状态
    #dxx:年代
    #exxx:付费
    #f1002:清晰度
    # &tags=&tags=....
    # sort1:最新 sort2: 人气
    name = params['name']
    url = params['url']
    urlpage = getHttpData(url, headers={'User-Agent': UserAgent})
    page = params.get('pageNo', '1')
    piece = url.split('/')[-1]
    tagId = re.compile('ch(\d+)').findall(piece)[0]

    list_api = 'http://www.tudou.com/s3portal/service/pianku/data.action'

    params = {'name': name,
              'pageSize': '30',
              'app': 'mainsitepc',
              'deviceType': '1',
              'tags': '',            # 地区类型...清晰度  , etc.
              'tagType': '3',
              'firstTagId': tagId,
              'areaCode': '',
              'initials': '',        # 首字母  2n2sort2
              'hotSingerId': '',
              'pageNo': page
             }
    strparam = buildParams(params)
    strparam = '?' + strparam[1:]
    html = getHttpData(list_api + strparam, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(html)
    items = jsdata['items']
    total = jsdata['total']

    li = xbmcgui.ListItem(BANNER_FMT % (name+'【第%s页】(分类过滤)' % page))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    tree = BeautifulSoup(urlpage, 'html.parser')
    soup = tree.find_all('select', {'id': 'selectOps'})
    field = soup[0].find_all('option')
    link = re.compile('var CONFIG.+?urls:(.+])').findall(urlpage)
    link = eval(link[0])
    for i in range(len(field)):
        title = field[i].text
        if field[i].has_attr('selected'):
            li = xbmcgui.ListItem(INDENT_FMT0 % title)
            currentPage = link[i]
        else:
            li = xbmcgui.ListItem(INDENT_FMT1 % title)

        href = HOST_URL + '/list/' + link[i]
        nametype = link[i][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        else:
            mode = 'videolist2'

        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=' + mode + '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    for item in items:
        title = item['title']
        href = item['playUrl']
        info = item['albumShortDesc']
        img = item['picUrl_200x112']
        pay = item['needMoney']
        info = item['updateInfo']
        if pay is True:
            info += '|付费'.decode('utf-8')
        albumId = item['albumId']
        aid = item['aid']
        li = xbmcgui.ListItem(title + TIMER_FMT % info,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href
        u += '&mode=albumlist&albumId=%d' % albumId
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(img)
        u += '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if currentPage[:3] == 'ach':
        mode = 'videolist1'
    else:
        mode = 'videolist2'
    if int(page) > 1:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist1&pageNo=%d' % (int(page)-1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if int(page) <= total // 30:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist1&pageNo=%d' % (int(page)+1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu2(params):
    name = params['name']
    url = params['url']
    urlpage = getHttpData(url, headers={'User-Agent': UserAgent})
    page = params.get('page', '1')
    piece = url.split('/')[-1]
    tagId = re.compile('ch(\d+)').findall(piece)[0]

    list_api = 'http://www.tudou.com/list/itemData.action'
    params = {'name': name,
              'pageSize': '30',
              'sort': '2',
              'tags': '',            # 地区类型...清晰度  , etc.
              'tagType': '1',
              'firstTagId': tagId,
              'areaCode': '',
              'initials': '',        # 首字母  2n2sort2
              'hotSingerId': '',
              'page': page
             }
    strparam = buildParams(params)
    strparam = '?' + strparam[1:]
    html = getHttpData(list_api + strparam, headers={'User-Agent': UserAgent})

    li = xbmcgui.ListItem(BANNER_FMT % (name+'【第%s页】(分类过滤)' % page))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    tree = BeautifulSoup(urlpage, 'html.parser')
    soup = tree.find_all('select', {'id': 'selectOps'})
    field = soup[0].find_all('option')
    link = re.compile('var CONFIG.+?urls:(.+])').findall(urlpage)
    link = eval(link[0])
    for i in range(len(field)):
        title = field[i].text
        if field[i].has_attr('selected'):
            li = xbmcgui.ListItem(INDENT_FMT0 % title)
            currentPage = link[i]
        else:
            li = xbmcgui.ListItem(INDENT_FMT1 % title)

        href = HOST_URL + '/list/' + link[i]
        nametype = link[i][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        else:
            mode = 'videolist2'
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=%s&title=%s' % (mode, urllib.quote_plus(title))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    jsdata = simplejson.loads(html)
    items = jsdata['data']

    for item in items:
        title = item['title']
        iid = item['itemId']
        img = item['bigPicUrl']
        time = item['totalTimeStr']
        code = item['code']
        li = xbmcgui.ListItem(title + TIMER_FMT % time,
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=albumlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(img)
        u += '&title=' + urllib.quote_plus(title)
        u += '&iid=%d&code=%s' % (iid, code)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if currentPage[:3] == 'ach':
        mode = 'videolist1'
    else:
        mode = 'videolist2'
    if int(page) > 1:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist2&page=%d' % (int(page)-1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if int(page) <= 2000:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist2&page=%d' % (int(page)+1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    return


def relatedAlbumList(params):
    aid = params.get('albumId')
    title = params.get('title')
    img = params.get('thumb', '')
    url = params.get('url')
    if url:
        html = getHttpData(url, headers={'User-Agent': UserAgent})
        iid = re.compile('iid: (\d+)').findall(html)
        vcode = re.compile('youkuCode: "(.+?)"').findall(html)
        u = sys.argv[0] + '?mode=playvideo&iid=%s&vcode=%s' % (iid[0], vcode[0])
        u += '&title=' + urllib.quote_plus(title)
        u += '&thumb=' + img
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    u = sys.argv[0] + '?mode=albumlist&albumId=%s' % aid
    u += '&title=' + title + '&thumb=' + img
    li = xbmcgui.ListItem(BANNER_FMT % title,
                          iconImage=img, thumbnailImage=img)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    album_api = 'http://www.tudou.com/crp/alist.action?a=%s'
    print '======================'
    print album_api,aid
    jspage = getHttpData(album_api % aid,
                         headers={'User-Agent': UserAgent},
                         decoded=False)

    jsdata = simplejson.loads(jspage)
    jsdata = jsdata['items']

    for item in jsdata:
        title = item['kw']
        info = item.get('comments')
        time = item['time']
        img = item['pic']
        vcode = item['vcode']
        iid = item['iid']
        u = sys.argv[0] + '?mode=playvideo'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&thumb=' + img
        u += '&vcode=%s&iid=%d' % (vcode, iid)
        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    rel_list = 'http://www.tudou.com/crp/getRelativeContent.action?a=%s'

    jspage = getHttpData(rel_list % aid, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(jspage)
    headings = jsdata['data']['catList']
    heading = [x['name'] for x in headings]
    title = '|'.join(heading).encode('utf-8')

    u = sys.argv[0] + '?mode=albumlist&albumId=%s' % aid
    u += '&title=' + urllib.quote_plus(title)
    li = xbmcgui.ListItem(BANNER_FMT % title)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    items = jsdata['data']['playAlbumInfoList']
    for item in items:
        aid = item['albumId']
        img = item['albumPicUrl']
        title = item['albumName']
        extra = item['update']
        info = item['albumShortDesc']
        li = xbmcgui.ListItem(title + '(' + extra + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=albumlist'
        u += '&title=%s&albumId=%d' % (title, aid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def relatedPlayList(params):
    iid = params.get('iid')
    title = params.get('title')
    img = params.get('thumb')
    code = params.get('code')
    vcode = params.get('vcode')
    if iid:
        u = sys.argv[0] + '?mode=playvideo&iid=%s' % iid
        if vcode:
            u += '&vcode=' + vcode
        u += '&title=' + urllib.quote_plus(title) + '&thumb=' + img
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

        rel_list = 'http://www.tudou.com/crp/getRelatedPlaylists.action?iid=%s'

        jspage = getHttpData(rel_list % iid, headers={'User-Agent': UserAgent})
        jsdata = simplejson.loads(jspage)
        items = jsdata['data']['pList']

        u = sys.argv[0] + '?mode=codelist&iid=%s' % iid
        u += '&title=相关视频'
        li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

        for item in items:
            title = item['name']
            img = item['picUrl']
            info = item['description']
            code = item['code']
            li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
            u = sys.argv[0] + '?mode=codelist'
            u += '&title=%s&code=%s' % (urllib.quote_plus(title), code)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

        code = items[0]['code']

    rel_list = 'http://www.tudou.com/crp/plist.action?lcode=%s'

    jspage = getHttpData(rel_list % code, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(jspage)
    items = jsdata['items']

    u = sys.argv[0] + '?mode=codelist&iid=%s' % iid
    u += '&title=主题视频'
    li = xbmcgui.ListItem(BANNER_FMT % '主题视频')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in items:
        title = item['kw']
        img = item['pic']
        time = item['time']
        iid = item['iid']
        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playvideo'
        u += '&title=%s&thumb=%s&iid=%d' % (urllib.quote_plus(title), img, iid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumList(params):
    aid = params.get('albumId')
    title = params.get('title', '')
    img = params.get('thumb', '')
    iid = params.get('iid')

    if aid:
        relatedAlbumList(params)
    elif iid:
        relatedPlayList(params)


def searchInTudou(params):
    if (__addon__.getSetting('keyboard') == '0'):
        keyboard = xbmc.Keyboard('', '请输入搜索内容')
    else:
        keyboard = ChineseKeyboard.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        p_url = 'http://so.tv.sohu.com/mts?chl=&tvType=-2&wd='
        url = p_url + urllib.quote_plus(keyword.decode('utf-8').encode('gbk'))
        params['url'] = url
        params['keyword'] = keyword
        params['page'] = '1'


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')
if mode is not None:
    del(params['mode'])

runlist = {
    None: 'mainMenu()',
    'videolist1': 'listSubMenu1(params)',
    'videolist2': 'listSubMenu2(params)',
    'albumlist': 'albumList(params)',
    'codelist': 'relatedPlayList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchInTudou(params)',
    'select': 'normalSelect(params)'
}

eval(runlist[mode])
