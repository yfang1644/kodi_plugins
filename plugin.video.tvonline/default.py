#!/usr/bin/python
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
import time
import simplejson

########################################################################
# 南京电视台 www.nbs.cn
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8')).decode("utf-8")


UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'

# collected from http://www.haoqu.net/3
CHANNELS_LE = {973: '河南政法频道',
            974: '河南国际频道',
            975: '上海第一财经',
            976: '上海星尚频道',
            977: '东方娱乐频道',
            978: '上海新闻频道',
            979: '江西都市频道',
            980: '江西经济生活频道',
            981: '江西影视娱乐频道',
            982: '江西少儿家庭频道',
            983: '江西电影频道',
            984: '广东珠江频道',
            985: '广东新闻频道',
            986: '嘉佳卡通卫视',
            987: '南方经济教科频道',
            988: '南方卫视',
            989: '南方影视',
            990: '南方少儿频道',
            991: '南方综艺',
            992: '江苏城市频道',
            993: '江苏综艺频道',
            994: '江苏影视频道',
            995: '江苏体育休闲频道',
            996: '江苏国际频道',
            997: '深圳财经生活',
            998: '深圳电视剧频道',
            999: '深圳都市频道',
            1000: '合肥生活频道',
            1001: '深圳少儿频道',
            1002: '合肥财经频道',
            1003: '深圳娱乐频道',
            1004: '深圳体育健康频道',
            1005: '合肥法制频道',
            1006: '合肥文体频道',
            1007: '郑州法制频道',
            1008: '郑州文体频道',
            1009: '郑州综合频道',
            1010: '郑州时尚频道',
            1011: '郑州电视剧频道',
            1012: '郭德纲'
           }

CHANNELS_SZ = {
    '苏州新闻综合': 'http://pull.8686c.com/sztv1/sbs1hd/playlist.m3u8',
    '苏州社会经济': 'http://livetv.2500city.com/live/sbs2hd/index.m3u8',
    '苏州文化生活': 'http://livetv.2500city.com/live/sbs3hd/index.m3u8',
    '苏州生活资讯': 'http://livetv.2500city.com/live/sbs5hd/index.m3u8'}

def getHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()
        if response.headers.get('content-encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    except:
        print 'GetHttpData Error: %s' % url
        return ''

    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    charset = ''
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')

    return httpdata


############################################################################
def PlayVideoNJTV(params):
    id = params['id']
    title = params['title']
    timeUrl = 'http://live-api.xwei.tv/api/getUnixTimestamp'
    html = getHttpData(timeUrl)
    timestamp = simplejson.loads(html)['time']
    t = float(timestamp)
    timestamp = int(t)

    bitrateUrl = 'http://live-api.xwei.tv/api/getCDNByChannelId/' + id
    html = getHttpData(bitrateUrl)
    jsdata = simplejson.loads(html)
    rate = jsdata['streams'].keys()
    if (__addon__.getSetting('resolution') == '0'):
        rate = rate[0]
    else:
        rate = rate[-1]
    channel = jsdata['channel_name']
    playurl = 'http://live.xwei.tv/channels/njtv/%s/flv:%s/live?%d'
    li = xbmcgui.ListItem(title)
    xbmc.Player().play(playurl % (channel, rate, timestamp), li)


############################################################################
def PlayVideoSZTV(params):
    url = params['url']
    title = params['title']
    li = xbmcgui.ListItem(title)
    xbmc.Player().play(url, li)


############################################################################
def PlayVideoLeTV(params):
    '''
    http://minisite.letv.com/tuiguang/index.shtml?islive=1&channelId=989&typeFrom=letv_live_360live&ark=100&cid=4&wmode=opaque
    '''
    id = params['id']
    title = params['title']
    info_api = 'http://player.pc.letv.com/player/startup_by_channel_id/1001/%s?host=letv.com'
    html = getHttpData(info_api % id)
    jsdata = simplejson.loads(html)['streams']

    if (__addon__.getSetting('resolution') == '0'):
        url = jsdata[0]
    else:
        url = jsdata[-1]

    url = url['streamUrl'] + '&format=1&expect=2&termid=1&platid=10&playid=1&sign=live_web&splatid=1001&p1=1&p2=10&uuid=D59417D1350531DC01E06CCF104E3A193004D0D4_0&vkit=20170302&station=' + id

    html = getHttpData(url)
    jsdata = simplejson.loads(html)
    playurl = jsdata['location']
    li = xbmcgui.ListItem(title)
    xbmc.Player().play(playurl, li)


def PlayVideoPPTV(params):
    url = params['url']
    title = params['title']
    thumb = params['thumb']

    quality = int(__addon__.getSetting('resolution'))
    import resources.lib.pptv as pptv
    if quality > 0:
        quality = -1           # point to last item
    urls = pptv.GetPPTVVideoURL(url, quality, __m3u8__)
    li = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
    xbmc.Player().play(__m3u8__, li)


def getProgramList(channelId):
    '''
    timeUrl = 'http://live-api.xwei.tv/api/getUnixTimestamp'
    html = getHttpData(timeUrl)
    timestamp = simplejson.loads(html)['time']
    t = float(timestamp)
    timestamp = int(t/1000)
    '''
    epgAPI = 'http://live-api.xwei.tv/api/getEPGByChannelTime/%s/0/%d'
    info = ''
    try:
        html = getHttpData(epgAPI % (channelId, int(time.time())))
        results = simplejson.loads(html)['result'][0]

        for prog in results:
            start = time.localtime(prog['start_time'])
            end = time.localtime(prog['end_time'])
            name = prog['name']
            name = name.replace(' ', '')
            info += '%02d:%02d--' % (start[3], start[4])
            info += '%02d:%02d    ' % (end[3], end[4])
            info += name + '\n'
    except:
        pass

    return info


def listNJTV(title):
    li = xbmcgui.ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    channelAPI = 'http://live-api.xwei.tv/api/getChannels'
    html = getHttpData(channelAPI)

    results = simplejson.loads(html)['result']
    for channel in results:
        title = channel['display_name']
        channelId = channel['id']
        info = getProgramList(channelId)
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=playnjtv&id=%s&title=%s' % (channelId, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listLETV(title):
    li = xbmcgui.ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://player.pc.letv.com/player/startup_by_channel_id/1001/%s?host=letv.com'

    for id in range(973, 1013):
        html = getHttpData(info_api % id)
        jsdata = simplejson.loads(html)
        title = jsdata['channelName']
        logos = jsdata['defaultLogo']
        img = logos.items()[0][1]

        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playletv&id=%d&title=%s' % (id, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listSZTV(title):
    li = xbmcgui.ListItem(BANNER_FMT % title)
    # http://tv.cutv.com/
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://liveapp.cutv.com/crossdomain/timeshiftinglive/getTSLAllChannelList/first/sztv'

    for channel in CHANNELS_SZ:
        title = channel
        url = CHANNELS_SZ[channel]
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?mode=playsztv&title=' + title
        u += '&url=' + url
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listPPTV(title):
    li = xbmcgui.ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://top.pptv.com/section?type=8&sort=hot7&from=web&version=1.0.0&format=jsonp&cataIds=164%2C156&length=80&cb=live&plt=web'
    info_api = 'http://top.pptv.com/section?type=8&sort=hot7&length=90&cb=live'

    html = getHttpData(info_api)
    match1 = re.compile('\((.+)\)').findall(html)
    jsdata = simplejson.loads(match1[0])
    jsdata = jsdata['videoList'][0]['videos']

    vids = [str(x['id']) for x in jsdata]
    prog_api = 'http://v.pptv.com/api/live/tvProgramList/%s?from=web&version=1.0.0&format=jsonp&cb=pplive_callback_1'
    html = getHttpData(prog_api % (','.join(vids)))
    match1 = re.compile('\((.+)\)').findall(html)
    prog_info = simplejson.loads(match1[0])

    jl = len(jsdata)

    for i in range(jl):
        title = jsdata[i]['title']
        img = jsdata[i]['cover']
        icon = jsdata[i]['shot']
        url = jsdata[i]['playlink']
        id = str(jsdata[i]['id'])
        thumb = prog_info[id]['icon']

        lists = prog_info[id]['list']
        info = ''
        for x in lists:
            info = info + x['playTime'] + ' ' + x['title'] + '\n'

        li = xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=thumb)
        li.setInfo(type='Video',
                   infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=playpptv&title=' + title
        u += '&url=' + url + '&thumb=' + thumb
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
#files, songs, artists, albums, movies, tvshows, episodes, musicvideos


def mainMenu():
    listPPTV('PPTV')
    listNJTV('南京电视台')
    listLETV('乐视直播')
    listSZTV('苏州')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'playnjtv': 'PlayVideoNJTV(params)',
    'playletv': 'PlayVideoLeTV(params)',
    'playsztv': 'PlayVideoSZTV(params)',
    'playpptv': 'PlayVideoPPTV(params)',
}

eval(runlist[mode])
