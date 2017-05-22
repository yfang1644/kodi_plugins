#/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import gzip
from random import randrange
import StringIO
from bs4 import BeautifulSoup
import simplejson
from resources.lib.common import get_html

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')
__m3u8__      = __cwd__ + '/temp.m3u8'

sitelist = {
    'le.com': 'letv',
    'letv.com': 'letv',
    'youku.com': 'youku',
    'qiyi.com': 'iqiyi',
    'sohu.com': 'sohu',
    'qq.com': 'qq',
    'fun.tv': 'funshion',
    'pptv.com': 'pptv',
    'tudou.com': 'tudou',
    'cctv.com': 'cntv',
    'cntv.cn': 'cntv',
    'mgtv.com': 'mgtv'
}

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
BANNER_FMT2 = '[COLOR FFDE0087]%s[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'


def mainMenu():
    MAINLIST = [
        (u'电视剧', 'http://dianshiju.cctv.com/list/all/index.shtml', 'dramalist'),
        (u'电影', 'http://dianyingku.cctv.com/list/index.shtml', 'movielist'),
        (u'动画片', 'http://donghua.cctv.com/list/all/', 'dramalist'),
        (u'纪录片', 'http://jishi.cntv.cn/doc/list/zm/index.shtml', 'dramalist')
    ]
    for channel in range(0, 4):
        title = MAINLIST[channel][0]
        href = MAINLIST[channel][1]
        mode = MAINLIST[channel][2]
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=' + mode + '&&name=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def changeList(params):

    typelist = ['全部', '爱情', '传记', '动画', '动作',
                '儿童', '犯罪', '风情', '歌舞', '古装',
                '纪录', '惊悚', '警匪', '剧情', '科幻',
                '励志', '历史', '伦理', '冒险', '魔幻',
                '其他', '微电影', '文艺', '武侠', '喜剧',
                '戏曲', '悬疑', '音乐', '灾难', '战争', '老电影']
    arealist = ['全部', '内地', '台湾', '香港', '澳大利亚', '德国',
                '俄罗斯', '法国', '韩国', '加拿大', '马来西亚',
                '美国', '日本', '泰国', '西班牙', '新加坡', '意大利',
                '印度', '英国', '其他', '欧美']
    yearlist = ['全部', '2015', '2014', '2013',
                '2012', '2011', '2010', '00年代', '更早']
    yeartype = ['0', '2015', '2014', '2013', '2012',
                '2011', '2010', '00s', 'gz']

    url = params['url']
    name = params['name']

    dialog = xbmcgui.Dialog()
    filter = ''
    sel = dialog.select('类型', typelist)
    if sel >= 0:
        params['type'] = str(sel)
        filter += '类型' + typelist[sel]

    sel = dialog.select('地区', arealist)
    if sel >= 0:
        params['area'] = str(sel)
        filter += '地区' + arealist[sel]

    sel = dialog.select('年份', yearlist)
    if sel >= 0:
        params['year'] = yeartype[sel]
        filter += '年份' + yearlist[sel]

    params['filter'] = filter
    movieList(params)


def dramaList(params):
    url = params['url']
    name = params['name']
    filter = params.get('filter', '')
    page = params.get('page', '0')
    filter = filter.encode('utf-8')

    li = xbmcgui.ListItem(BANNER_FMT % (name + '[分类过滤]' + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    soup = tree.find_all('ul', {'id': 'ul_fenye'})
    total_soup = len(soup)
    total_page = total_soup // 8

    page = int(page)
    items = soup[8*page]
    for i in range(1, 8):
        items.append(soup[8*page + i])

    items = items.find_all('li')
    for item in items:
        image = item.find('div', {'class': 'image'})
        thumb = image.img['data']
        href = image.a['href']
        text = item.find('div', {'class': 'text'})
        title = text.a.text
        info = text.p['title']

        li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&mode=serieslist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(thumb)
        u += '&title=' + title

        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # pagelist
    if page > 0:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
        u += '&mode=dramalist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&page=%d' % (page - 1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if page < total_page:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
        u += '&mode=dramalist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&page=%d' % (page + 1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def movieList(params):
    url = params['url']
    name = params['name']
    page = params.get('page', '1')
    type = params.get('type', '1')
    area = params.get('area', '0')
    year = params.get('year', '0')
    filter = params.get('filter', '')

    li = xbmcgui.ListItem(BANNER_FMT % (name + '[分类过滤]' + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    #http://api.cntv.cn/Movies/getMoviesByTAY?controller=movies&action=getMoviesByTAY&type=30&area=11&pagesize=30&order=pk'
    mv_api = 'http://api.cntv.cn/Movies/getMoviesByTAY?'  # TAY=type/area/year
    action = 'controller=movies&action=getMoviesByTAY'
    if area != '0':
        action += '&area=' + area
    if year != '0':
        action += '&year=' + year
    filter = '&type=%s&p=%s&pagesize=30&order=pk'

    html = get_html(mv_api + action + filter % (type, page))
    html = html.encode('utf-8')
    jsdata = simplejson.loads(html)

    items = jsdata['data']
    for item in items:
        title = item['name'].encode('utf-8')
        p_thumb = item['localimgurl'].encode('utf-8')
        mid = item['mid'].encode('utf-8')

        li = xbmcgui.ListItem(title, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=playmid' + '&url=' + url
        u += '&name=' + urllib.quote_plus(name) + '&mid=' + mid
        u += '&thumb=' + p_thumb + '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    totalnum = int(jsdata['totalnum'])
    totalpage = int(jsdata['totalpage'])
    page = int(page)

    if page > 1:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?mode=movielist&url=' + url
        u += '&name=' + urllib.quote_plus(name)
        if area != '0':
            u += '&area=' + area
        if year != '0':
            u += '&year=' + year
        u += '&type=' + type + '&page=%d' % (page - 1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if page < totalpage:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?mode=movielist&url=' + url
        u += '&name=' + urllib.quote_plus(name)
        if area != '0':
            u += '&area=' + area
        if year != '0':
            u += '&year=' + year
        u += '&type=' + type + '&page=%d' % (page + 1)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def list_by_sid(params):
    sid = params['sid']
    api = 'http://tv.cntv.cn/api/video/getvideo/vsid_'
    html = get_html(api + sid)
    jsdata = simplejson.loads(html)
    items = jsdata['video']

    for item in items:
        title = item['t']
        p_url = item['url']
        p_thumb = item['img']
        time = item['len']

        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=p_thumb, thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=playvideo&url=' + p_url
        u += '&title=' + title
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def list_by_jsondata(data):
    jsdata = eval(data[0])
    print jsdata
    if isinstance(jsdata, dict):
        jsdata = [jsdata]
    lj = len(jsdata)
    for i in range(lj):
        title = jsdata[i]['title']
        p_url = jsdata[i]['url']
        p_thumb = jsdata[i]['img']
        desc = jsdata[i].get('brief', '')

        li = xbmcgui.ListItem(title,
                              iconImage=p_thumb, thumbnailImage=p_thumb)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': desc})

        u = sys.argv[0] + '?mode=playvideo&url=' + p_url
        u += '&title=' + title
        u += '&thumb=' + p_thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def seriesList(params):
    url = params['url']
    name = params['name']
    html = get_html(url)

    html = re.sub('\t|\r|\n', ' ', html)

    sid = re.compile('var vsid="(.+?)";').findall(html)
    data1 = re.compile('var jsonData1=\[({.+?})\];').findall(html)
    data2 = re.compile('var jsonData2=\[({.+?})\];').findall(html)
    if len(sid) > 0:
        params['sid'] = sid[0]
        list_by_sid(params)

    if len(data1) > 0:
        list_by_jsondata(data1)
    if len(data2) > 0:
        list_by_jsondata(data2)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playVideo_local(params):
    title = params['title']
    thumb = params['thumb']
    url = params['url']
    PlayVideo(url, title, thumb)


def playVideo_by_mid(params):
    mid = params['mid']
    print '--------------------------',mid
    url = params['url']
    api = 'http://api.cntv.cn/dianyingku/movies/getMovieById?mid='
    html = get_html(api + mid)
    jsdata = simplejson.loads(html)

    play = jsdata['play']
    jl = len(play)
    siteFound = False

    for site in sitelist:
        for i in range(jl):
            playurl = play[i]['playurl']
            if site in playurl:
                siteFound = True
                break
        if siteFound:
            break
    if siteFound:
        title = params['title']
        thumb = params['thumb']
        PlayVideo(playurl, title, thumb)
    else:
        xbmcgui.Dialog().ok(__addonname__, '视频地址未解析')


def PlayVideo(playurl, title, thumb):
    videoRes = int(__addon__.getSetting('resolution'))

    if ('le.com' in playurl) or ('letv.com' in playurl):
        import resources.lib.letv as letv
        video = letv.LeTV()
        videourl = video.video_from_url(playurl,
                                        level=videoRes,
                                        m3u8=__m3u8__)
        li = xbmcgui.ListItem(title, thumbnailImage=thumb)
        li.setInfo(type="Video", infoLabels={"Title": title})
        xbmc.Player().play(__m3u8__, li)
        return

    if 'sohu.com' in playurl:
        import resources.lib.sohu as sohu
        video = sohu.Sohu()
        videourl = video.video_from_url(playurl, level=videoRes)

    if 'qq.com' in playurl:
        import resources.lib.qq as qq
        video = qq.QQ()
        videourl = video.video_from_url(playurl, level=videoRes)

    if 'qiyi.com' in playurl:
        import resources.lib.iqiyi as iqiyi
        video = iqiyi.IQiyi()
        videourl = video.video_from_url(playurl, level=videoRes)

        li = xbmcgui.ListItem(title, thumbnailImage=thumb)
        li.setInfo(type="Video", infoLabels={"Title": title})
        xbmc.Player().play(videourl, li)
        return

    if 'fun.tv' in playurl:
        import resources.lib.funshion as funshion
        video = funshion.Funshion()
        videourl = video.video_from_url(playurl, level=videoRes)

    if 'youku.com' in playurl:
        import resources.lib.youku as youku
        video = youku.Youku()
        videourl = video.video_from_url(playurl, level=videoRes)

    if ('cntv.cn' in playurl) or ('cctv.com' in playurl):
        import resources.lib.cntv as cntv
        video = cntv.CNTV()
        videourl = video.video_from_url(playurl, level=videoRes)

    if 'pptv.com' in playurl:
        import resources.lib.pptv as pptv
        video = pptv.PPTV()
        videourl = video.video_from_url(playurl, level=videoRes)

    ulen = len(videourl)

    if ulen > 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for i in range(0, ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            li = xbmcgui.ListItem(name, thumbnailImage=thumb)
            li.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(videourl[i], li)

        xbmc.Player().play(playlist)


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'dramalist': 'dramaList(params)',
    'movielist': 'movieList(params)',
    'documentlist': 'documentList(params)',
    'serieslist': 'seriesList(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo_local(params)',
    'playmid': 'playVideo_by_mid(params)'
}

eval(runlist[mode])
#http://api.cntv.cn/dianyingku/movies/searchTypeFw
