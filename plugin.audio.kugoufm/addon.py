#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
import time

BANNER_PAGE = '[COLOR gold]%s[/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

userAgent = 'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10'
HOST_URL = 'http://m.kugou.com'
headers = {'User-Agent': userAgent, 'Referer': HOST_URL}

def getHttpData(u, query):
    import urllib2
    import json
    from urllib import urlencode

    url = '%s/app/i/%s?%s' % (HOST_URL, u, urlencode(query))
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    return json.loads(httpdata)

def getSingerPic(title, size=200):
    import re
    # 根据歌手获得相应的信息
    singerList = re.findall('(【.*?】)?(.*?)-', title)
    if singerList:
        query = {'singerName': singerList[0][1],
                 'size': size,
                 'd': time.time()*1000}
        singerUrl = 'getSingerHead_new.php'
        singerJson = getHttpData(singerUrl, query)
        return singerJson.get('url', '')
    return ''


def getSongInfo(hashId):
    #根据hash 获得mp3的相应信息
    query = {'hash': hashId, 'cmd': 'playInfo'}
    songUrl = 'getSongInfo.php'
    songJson =  getHttpData(songUrl, query)
    return songJson['url']


#http://m.kugou.com/app/i/fmSongs.php?fmid=891&size=30
def getSongs(fmid, t=None, size=30):
    #只选取前80首歌(可以查询的歌曲相当的多！！！)  返回的是相应的json
    listUrl = 'fmSongs.php'
    offset = {"time": int(t if t else time.time())}
    query = {'fmid': str(fmid), 'offset': str(offset),'size': size}
    listJson = getHttpData(listUrl, query)
    return listJson['data'][0]['songs']


#http://m.kugou.com/app/i/fmList.php?pageindex=1&pagesize=30
def getFmList(page, pagesize=30):
    #获得酷狗Fm列表 json
    query = {'pageindex': page, 'pagesize': pagesize}
    url = 'fmList.php'
    reqJson = getHttpData(url, query)
    return reqJson


# 获得相应电台的歌曲的列表
@plugin.route('/getPlayList/<fmid>')
def getPlayList(fmid):
    plugin.set_content('music')
    t = int(time.time())
    songs = getSongs(fmid, t)
    # 判断songs是否存在
    if not songs: return []
    items = [{
        'label': song['name'],
        'path': getSongInfo(song['hash']),
        'is_playable': True,
        'info': {'title': song['name'], 'duration': song['time']/1000}
    } for song in songs]

    return items

@plugin.route('/')
def index(page=1):
    currpage = int(page)
    pagesize = 30
    lists = getFmList(page, pagesize)
    totalPages = (lists['recordcount']-1)//pagesize + 1
    items = []
    for i in lists['data']:
        items.append({
            'label': i['fmname'],
            'path': url_for('getPlayList', fmid=i['fmid']),
            'thumbnail': 'http://imge.kugou.com/fmlogo/145/%s' % i['imgurl'],
            'icon': 'http://imge.kugou.com/fmlogo/145/%s' % i['imgurl'],
            'info': {'title': i['fmname']}
        })

    # 设置分页
    if currpage > 1:
        linkpage = currpage - 1
        items.append({
            'label': '上一页 【[COLOR FF00FF00]%s[/COLOR]/[COLOR FFFF0000]%s[/COLOR]】'%(linkpage,totalPages),
            'path': url_for('index',page=linkpage)
        })
    if currpage < totalPages:
        linkpage = currpage + 1
        items.append({
            'label': '下一页 【[COLOR FF00FF00]%s[/COLOR]/[COLOR FFFF0000]%s[/COLOR]】'%(linkpage,totalPages),
            'path': url_for('index',page=linkpage)
        })
    return items

if __name__ == '__main__':
    plugin.run()
