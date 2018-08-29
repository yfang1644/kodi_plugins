#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import ListItem
import xbmcplugin
import xbmcaddon
import urllib2
import urlparse
import re
import sys
import os
from common import get_html
import time
import json

########################################################################
# 南京电视台 www.nbs.cn
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__cwd__       = __addon__.getAddonInfo('path')
__addonname__ = __addon__.getAddonInfo('name')
__m3u8__      = __cwd__ + '/temp.m3u8'


UserAgent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

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


############################################################################
def PlayVideoNJTV(params):
    id = params['id']
    title = params['title']
    timeUrl = 'http://live-api.xwei.tv/api/getUnixTimestamp'
    html = get_html(timeUrl)
    timestamp = json.loads(html)['time']
    t = float(timestamp)
    timestamp = int(t)

    bitrateUrl = 'http://live-api.xwei.tv/api/getCDNByChannelId/' + id
    html = get_html(bitrateUrl)
    jsdata = json.loads(html)
    rate = jsdata['streams'].keys()
    if (__addon__.getSetting('resolution') == '0'):
        rate = rate[0]
    else:
        rate = rate[-1]
    channel = jsdata['channel_name']
    playurl = 'http://live.xwei.tv/channels/njtv/%s/flv:%s/live?%d'
    li = ListItem(title)
    xbmc.Player().play(playurl % (channel, rate, timestamp), li)


############################################################################
def PlayVideoSZTV(params):
    url = params['url']
    title = params['title']
    li = ListItem(title)
    xbmc.Player().play(url, li)


############################################################################
def PlayVideoLeTV(params):
    '''
    http://minisite.letv.com/tuiguang/index.shtml?islive=1&channelId=989&typeFrom=letv_live_360live&ark=100&cid=4&wmode=opaque
    '''
    id = params['id']
    title = params['title']
    info_api = 'http://player.pc.letv.com/player/startup_by_channel_id/1001/%s?host=letv.com'
    html = get_html(info_api % id)
    jsdata = json.loads(html)['streams']

    if (__addon__.getSetting('resolution') == '0'):
        url = jsdata[0]
    else:
        url = jsdata[-1]

    url = url['streamUrl'] + '&format=1&expect=2&termid=1&platid=10&playid=1&sign=live_web&splatid=1001&p1=1&p2=10&uuid=D59417D1350531DC01E06CCF104E3A193004D0D4_0&vkit=20170302&station=' + id

    html = get_html(url)
    jsdata = json.loads(html)
    playurl = jsdata['location']
    li = ListItem(title)
    xbmc.Player().play(playurl, li)


def getHttp(url):
    resp = urllib2.urlopen(url, timeout=2)
    data = resp.read()
    data = data.decode('utf-8')
    resp.close()

    branch = re.compile('(http.+//.+)\n').findall(data)

    try:
        data = branch[0]
    except:
        return url
    if data.find('m3u8') >= 0:
        return data
    else:
        return url


def PlayVideoPPTV(params):
    url = params['url']
    title = params['title']
    thumb = params['thumb']

    quality = int(__addon__.getSetting('resolution'))
    if quality > 0:
        quality = -1           # point to last item

    html = get_html(url)

    playcfg = re.compile('var webcfg\s*=\s*({.+?);\n').findall(html)
    if playcfg:
        jsplay = json.loads(playcfg[0])
    else:
        return []

    ipadurl = jsplay['player']['playList'][0]['ipadurl']
    ctx = jsplay['player']['ctx']
    ipadurl += '?' + ctx

    #ipadurl = getHttp(ipadurl)
    li = ListItem(title, iconImage=thumb, thumbnailImage=thumb)
    xbmc.Player().play(ipadurl, li)


def getProgramList(channelId):
    '''
    timeUrl = 'http://live-api.xwei.tv/api/getUnixTimestamp'
    html = get_html(timeUrl)
    timestamp = json.loads(html)['time']
    t = float(timestamp)
    timestamp = int(t/1000)
    '''
    epgAPI = 'http://live-api.xwei.tv/api/getEPGByChannelTime/%s/0/%d'
    info = ''
    try:
        html = get_html(epgAPI % (channelId, int(time.time())))
        results = json.loads(html)['result'][0]

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
    li = ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    channelAPI = 'http://live-api.xwei.tv/api/getChannels'
    html = get_html(channelAPI)

    results = json.loads(html)['result']
    for channel in results:
        title = channel['display_name']
        channelId = channel['id']
        info = getProgramList(channelId)
        li = ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=playnjtv&id=%s&title=%s' % (channelId, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listLETV(title):
    li = ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://player.pc.letv.com/player/startup_by_channel_id/1001/%s?host=letv.com'

    for id in range(973, 1013):
        html = get_html(info_api % id)
        jsdata = json.loads(html)
        title = jsdata['channelName']
        logos = jsdata['defaultLogo']
        img = logos.items()[0][1]

        li = ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playletv&id=%d&title=%s' % (id, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listSZTV(title):
    li = ListItem(BANNER_FMT % title)
    # http://tv.cutv.com/
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://liveapp.cutv.com/crossdomain/timeshiftinglive/getTSLAllChannelList/first/sztv'

    for channel in CHANNELS_SZ:
        title = channel
        url = CHANNELS_SZ[channel]
        li = ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?mode=playsztv&title=' + title
        u += '&url=' + url
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)


def listPPTV(title):
    li = ListItem(BANNER_FMT % title)
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    info_api = 'http://top.pptv.com/section?type=8&sort=hot7&from=web&version=1.0.0&format=jsonp&cataIds=164%2C156&length=80&cb=live&plt=web'
    info_api = 'http://top.pptv.com/section?type=8&sort=hot7&length=90&cb=live'

    html = get_html(info_api)
    match1 = re.compile('\((.+)\)').findall(html)
    jsdata = json.loads(match1[0])
    jsdata = jsdata['videoList'][0]['videos']

    vids = [str(x['id']) for x in jsdata]
    prog_api = 'http://v.pptv.com/api/live/tvProgramList/%s?from=web&version=1.0.0&format=jsonp&cb=pplive_callback'
    html = get_html(prog_api % (','.join(vids)))
    print(html)
    match1 = re.compile('\((.+)\)').findall(html)
    prog_info = json.loads(match1[0])

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

        li = ListItem(title, iconImage=icon, thumbnailImage=thumb)
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
params = dict(urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'playnjtv': 'PlayVideoNJTV(params)',
    'playletv': 'PlayVideoLeTV(params)',
    'playsztv': 'PlayVideoSZTV(params)',
    'playpptv': 'PlayVideoPPTV(params)',
}

exec(runlist[mode])
