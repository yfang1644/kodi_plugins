#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin
from xbmcgui import Dialog, ListItem
import xbmc
import xbmcaddon
from urlparse import parse_qsl
from urllib import urlencode
from json import loads
from common import get_html
from yinyuetai import video_from_vid

##########################################################################
# 音悦台MV
##########################################################################

__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')


def playVideo(params):
    playmode = __addon__.getSetting('video_vplaycont')
    videoId = params.get('videoId')

    playlistA = xbmc.PlayList(1)
    playlist = xbmc.PlayList(0)
    playlist.clear()

    v_pos = int(videoId.split('.')[0])
    psize = playlistA.size()

    for x in range(v_pos, psize):
        p_item = playlistA.__getitem__(x)
        vid = p_item.getfilename(x)
        p_list = p_item.getdescription(x)
        li = p_item
        li.setInfo(type='Music', infoLabels={'Title': p_list})
        v_url = video_from_vid(vid)

        playlist.add(v_url, li)
        if x == v_pos:
            xbmc.Player(0).play(playlist)
        if playmode == 'false':
            break

mvapi = 'http://mvapi.yinyuetai.com/mvchannel/so?'
catapi = 'http://mvapi.yinyuetai.com/cata/get-cata?cataId=%s'

def setFilters(params):
# a=ML
    AREA_LIST = {'全部': '', '内地':'ML', '港台':'HT', '欧美':'US',
             '韩国': 'KR', '日本':'JP', '二次元':'ACG','其他': 'Other'}
# p=Boy
    PERSONS = {'全部': '', '男艺人': 'Boy', '女艺人': 'Girl',
           '乐队组合': 'Combo', '其他': 'Other'}

# c=hd, shd..., 画质
    dialog = Dialog()

    title = u'艺人地区'
    keyword = AREA_LIST.keys()
    sel = dialog.select(title, keyword)
    if sel >= 0:
        area = AREA_LIST[keyword[sel]]

    title = u'艺人类别'
    keyword = PERSONS.keys()
    sel = dialog.select(title, keyword)
    if sel >= 0:
        person = PERSONS[keyword[sel]]
    params['person'] = person
    params['area'] = area
    mainList(params)


def videoList(params):
    sid = params.get('sid', '')
    tid = params.get('tid', '')
    person = params.get('person', '')
    area = params.get('area', '')

    page = int(params.get('page', 1))
    req = {
        'sid': sid,
        'tid': tid,
        'a': area,
        'p': person,
        'c': '',
        's': '',
        'pageSize': 20,
        'page': page
    }
    
    data = urlencode(req)
    html = get_html(mvapi + data)
    results = loads(html)
    totalpage = int(results['pageInfo']['pageCount'])
    results = results['result']

    if page > 1:
        li = ListItem('上一页')
        params['page'] = page - 1
        params['mode'] = 'videolist'
        u = sys.argv[0] + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    playlist = xbmc.PlayList(1)
    playlist.clear()

    for (j, item) in enumerate(results):
        title = item['title']
        videoId = str(item['videoId'])
        thumb = item['image']
        d = item['duration']
        duration = 0
        for t in d.split(':'):
            duration = duration*60 + int(t)

        info = {
            'Title': title,
            'plot': item['description'],
            'duration': duration
        }
        li = ListItem(title, thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels=info)
        params['mode'] = 'playvideo'
        params['videoId'] = '%d.%s' % (j, videoId)
        u = sys.argv[0] + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)
        playlist.add(videoId, li)

    if page < totalpage:
        li = ListItem('下一页')
        params['page'] = page + 1
        params['mode'] = 'videolist'
        u = sys.argv[0] + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    xbmcplugin.setContent(pluginhandle, 'movies')
    xbmcplugin.endOfDirectory(pluginhandle)


def mainList(params):
    person = params.get('person')
    area = params.get('area')
    
    li = ListItem('[选择地区/类别]')
    params['mode'] = 'filter'
    u = sys.argv[0] + '?' + urlencode(params)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    sid = params.get('sid')
    html = get_html(catapi % sid)
    catas = loads(html)['catas']
    catas.insert(0, {'cataName': u'全部', 'cataId': -1})
    for item in catas:
        name = item['cataName'].encode('utf-8')
        li = ListItem(name)
        tid = item['cataId']
        if int(tid) > 0:
            tid = str(tid).encode('utf-8')
        else:
            tid = ''

        params['tid'] = tid
        params['sid'] = sid
        params['mode'] = 'videolist'
        u = sys.argv[0] + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    xbmcplugin.endOfDirectory(pluginhandle)


def rootMenu(params):
    items = [
        ('全部', ''),
        ('音乐视频', '3'),
        ('现场/live','4'),
        ('娱乐视频', '9'),
        ('舞蹈', '5'),
        ('演奏', '6'),
        ('ACG', '7'),
        ('戏剧', '8')]

    for (name, sid) in items:
        li = ListItem(name)
        if len(sid) == 0:
            mode = 'videolist'
        else:
            mode = 'mainlist'
        u = sys.argv[0] + '?mode={}&sid={}'.format(mode, sid) 
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    xbmcplugin.endOfDirectory(pluginhandle)


#  main program goes here #
pluginhandle = int(sys.argv[1])
params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'rootMenu(params)',
    'mainlist': 'mainList(params)',
    'videolist': 'videoList(params)',
    'playvideo': 'playVideo(params)',
    'filter': 'setFilters(params)'
}

exec(runlist[mode])
