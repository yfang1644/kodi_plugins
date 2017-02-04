# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, sys, os, gzip, StringIO
from random import random, randint
from math import floor
import hashlib
import time
import simplejson

# Plugin constants
__addonname__ = "奇艺视频(QIYI)"
__addonid__   = "plugin.video.qiyi"
__addon__     = xbmcaddon.Addon(id=__addonid__)

CHANNEL_LIST = {'电影': '1',
                '电视剧': '2',
                '纪录片': '3',
                '动漫': '4',
                '音乐': '5',
                '综艺': '6',
                '娱乐': '7',
                '旅游': '9',
                '片花': '10',
                '教育': '12',
                '时尚': '13'}
ORDER_LIST = [['4', '更新时间'],
              ['11', '热门']]
PAYTYPE_LIST = [['', '全部影片'],
                ['0', '免费影片'],
                ['1', '会员免费'],
                ['2', '付费点播']]
UserAgent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'


def GetHttpData(url):
    charset = ''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req)
        headers = response.info()
        httpdata = response.read()
        if response.headers.get('Content-Encoding', None) == 'gzip':
            if httpdata[-1] == '\n':    # some windows zip files have extra '0a'
                httpdata = httpdata[:-1]
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
    httpdata = re.sub('\r|\n|\t', '', httpdata)
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')
    return httpdata


def searchDict(dlist, idx):
    for i in range(0, len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''


def getcatList(listpage, name, cat):
    # 类型(电影,纪录片,动漫,娱乐,旅游), 分类(电视剧,综艺,片花), 流派(音乐), 一级分类(教育), 行业(时尚)
    match = re.compile('<h3>(类型|分类|流派|一级分类|行业)：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    if name in ('纪录片', '旅游'):
        pattern = '/(\d*)-[^>]+>(.*?)</a>'
    elif name in ('音乐', '片花'):
        pattern = '/\d*-\d*-\d*-(\d*)-[^>]+>(.*?)</a>'
    elif name == '教育':
        pattern = '/\d*-\d*-(\d*)-[^>]+>(.*?)</a>'
    elif name == '时尚':
        pattern = '/\d*-\d*-\d*-\d*-(\d*)-[^>]+>(.*?)</a>'
    else:
        pattern = '/\d*-(\d*)-[^>]+>(.*?)</a>'

    catlist = re.compile('/www/' + CHANNEL_LIST[name] + pattern).findall(match[0][1])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0][1])
    if match1:
        catlist.append((cat, match1.group(1)))
    return catlist


def getareaList(listpage, name, area):
    match = re.compile('<h3>地区：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    if name == '娱乐':
        arealist = re.compile('/www/' + CHANNEL_LIST[name] + '/\d*-\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    elif name in ('旅游', '片花'):
        arealist = re.compile('/www/' + CHANNEL_LIST[name] + '/\d*-(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    else:
        arealist = re.compile('/www/' + CHANNEL_LIST[name] + '/(\d*)-[^>]+>(.*?)</a>').findall(match[0])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0])
    if match1:
        arealist.append((area, match1.group(1)))
    return arealist


def getyearList(listpage, name, year):
    match = re.compile('<h3>我的年代：</h3>(.*?)</ul>', re.DOTALL).findall(listpage)
    yearlist = re.compile('/www/' + CHANNEL_LIST[name] + '/\d*-\d*---------\d*-([\d_]*)-[^>]+>(.*?)</a>').findall(match[0])
    match1 = re.compile('<a href="#">(.*?)</a>').search(match[0])
    if match1:
        yearlist.append((year, match1.group(1)))
    return yearlist


#         id   c1   c2   c3   c4   c5     c11  c12   c14
# 电影     1 area  cat                paytype year order
# 电视剧   2 area  cat                paytype year order
# 纪录片   3  cat                     paytype      order
# 动漫     4 area  cat  ver  age      paytype      order
# 音乐     5 area lang       cat  grp paytype      order
# 综艺     6 area  cat                paytype      order
# 娱乐     7       cat area           paytype      order
# 旅游     9  cat area                paytype      order
# 片花    10      area       cat      paytype      order
# 教育    12            cat           paytype      order
# 时尚    13                      cat paytype      order
def progList(name, page, cat, area, year, order, paytype):
    c1 = ''
    c2 = ''
    c3 = ''
    c4 = ''
    if name == '娱乐':
        c3 = area
    elif name in ('旅游', '片花'):
        c2 = area
    elif name != '纪录片':
        c1 = area
    if name in ('纪录片', '旅游'):
        c1 = cat
    elif name in ('音乐', '片花'):
        c4 = cat
    elif name == '教育':
        c3 = cat
    elif name == '时尚':
        c5 = cat
    else:
        c2 = cat
    url = 'http://list.iqiyi.com/www/' + CHANNEL_LIST[name]+ '/' + c1 + '-' + c2 + \
          '-' + c3 + '-' + c4 + '-------' + paytype + \
          '-' + year + '--' + order + '-' + page + '-1-iqiyi--.html'
    currpage = int(page)
    link = GetHttpData(url)
    match1 = re.compile('data-key="([0-9]+)"').findall(link)
    if len(match1) == 0:
        totalpages = 1
    else:
        totalpages = int(match1[len(match1) - 1])
    match = re.compile('<!-- 分类 -->(.+?)<!-- 分类 end-->', re.DOTALL).findall(link)
    if match:
        listpage = match[0]
    else:
        listpage = ''
    match = re.compile('<div class="wrapper-piclist"(.+?)<!-- 页码 开始 -->', re.DOTALL).findall(link)
    if match:
        match = re.compile('<li[^>]*>(.+?)</li>', re.DOTALL).findall(match[0])
    totalItems = len(match) + 1
    if currpage > 1:
        totalItems += 1
    if currpage < totalpages:
        totalItems += 1

    if cat == '':
        catstr = '全部类型'
    else:
        catlist = getcatList(listpage, name, cat)
        catstr = searchDict(catlist, cat)
    selstr = '[COLOR FFFF0000]' + catstr + '[/COLOR]'

    if name not in ('纪录片', '教育', '时尚'):
        if area == '':
            areastr = '全部地区'
        else:
            arealist = getareaList(listpage, name, area)
            areastr = searchDict(arealist, area)
        selstr += '/[COLOR FF00FF00]' + areastr + '[/COLOR]'
    if name in ('电影', '电视剧'):
        if year == '':
            yearstr = '全部年份'
        else:
            yearlist = getyearList(listpage, name, year)
            yearstr = searchDict(yearlist, year)
        selstr += '/[COLOR FFFFFF00]' + yearstr + '[/COLOR]'

    selstr += '/[COLOR FF00FFFF]' + searchDict(ORDER_LIST, order) + '[/COLOR]'
    selstr += '/[COLOR FFFF00FF]' + searchDict(PAYTYPE_LIST, paytype) + '[/COLOR]'
    li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【'+selstr+'】（按此选择）')
    u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name) + \
        "&id="+urllib.quote_plus(CHANNEL_LIST[name]) + \
        "&cat="+urllib.quote_plus(cat) + \
        "&area="+urllib.quote_plus(area) + \
        "&year="+urllib.quote_plus(year) + \
        "&order="+order + \
        "&paytype="+urllib.quote_plus(paytype) + \
        "&page="+urllib.quote_plus(listpage)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)
    for i in range(0, len(match)):
        p_name = re.compile('alt="(.+?)"').findall(match[i])[0]
        p_thumb = re.compile('src\s*=\s*"(.+?)"').findall(match[i])[0]
        #p_id  = re.compile('data-qidanadd-albumid="(\d+)"').search(match[i]).group(1)
        p_id = re.compile('href="([^"]*)"').search(match[i]).group(1)

        try:
            p_episode = re.compile('data-qidanadd-episode="(\d)"').search(match[i]).group(1) == '1'
        except:
            p_episode = False
        match1 = re.compile('<span class="icon-vInfo">([^<]+)</span>').search(match[i])
        if match1:
            msg = match1.group(1).strip()
            p_name1 = p_name + '（' + msg + '）'
            if (msg.find('更新至') == 0) or (msg.find('共') == 0):
                p_episode = True
        else:
            p_name1 = p_name

        if p_episode:
            mode = '2'
            isdir = True
            p_id = re.compile('data-qidanadd-albumid="(\d+)"').search(match[i]).group(1)
        else:
            mode = '3'
            isdir = False
        match1 = re.compile('<p class="dafen2">\s*<strong class="fRed"><span>(\d*)</span>([\.\d]*)</strong><span>分</span>\s*</p>').search(match[i])
        if match1:
            p_rating = float(match1.group(1)+match1.group(2))
        else:
            p_rating = 0
        match1 = re.compile('<span>导演：</span>(.+?)</p>', re.DOTALL).search(match[i])
        if match1:
            p_director = ' / '.join(re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1)))
        else:
            p_director = ''
        match1 = re.compile('<em>主演:</em>(.+?)</div>', re.DOTALL).search(match[i])
        if match1:
            p_cast = re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1))
        else:
            p_cast = []
        match1 = re.compile('<span>类型：</span>(.+?)</p>', re.DOTALL).search(match[i])
        if match1:
            p_genre = ' / '.join(re.compile('<a [^>]+>([^<]*)</a>').findall(match1.group(1)))
        else:
            p_genre = ''
        match1 = re.compile('<p class="s1">\s*<span>([^<]*)</span>\s*</p>').search(match[i])
        if match1:
            p_plot = match1.group(1)
        else:
            p_plot = ''
        li = xbmcgui.ListItem(str(i + 1) + '.' + p_name1, iconImage='', thumbnailImage=p_thumb)
        li.setArt({'poster': p_thumb})
        u = sys.argv[0]+"?mode="+mode+"&name="+urllib.quote_plus(p_name)+"&id="+urllib.quote_plus(p_id)+"&thumb="+urllib.quote_plus(p_thumb)
        li.setInfo(type="Video", infoLabels={"Title": p_name,
                                             "Director": p_director,
                                             "Genre": p_genre,
                                             "Plot": p_plot,
                                             "Cast": p_cast,
                                             "Rating": p_rating})
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, isdir, totalItems)
        print urllib.quote_plus(p_id)

    if currpage > 1:
        li = xbmcgui.ListItem('上一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name) + \
            "&id="+urllib.quote_plus(CHANNEL_LIST[name]) + \
            "&cat="+urllib.quote_plus(cat) + \
            "&area="+urllib.quote_plus(area) + \
            "&year="+urllib.quote_plus(year) + \
            "&order="+order + \
            "&page="+urllib.quote_plus(str(currpage-1)) + \
            "&paytype="+paytype
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)
    if currpage < totalpages:
        li = xbmcgui.ListItem('下一页')
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name) + \
            "&id="+urllib.quote_plus(CHANNEL_LIST[name]) + \
            "&cat="+urllib.quote_plus(cat) + \
            "&area="+urllib.quote_plus(area) + \
            "&year="+urllib.quote_plus(year) + \
            "&order="+order + \
            "&page="+urllib.quote_plus(str(currpage+1)) + \
            "&paytype="+paytype
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)

    xbmcplugin.setContent(pluginhandle, 'movies')
    xbmcplugin.endOfDirectory(pluginhandle)


def seriesList(name, id, thumb, page):
    url = 'http://cache.video.qiyi.com/a/%s' % (id)
    link = GetHttpData(url)
    data = link[link.find('=')+1:]
    json_response = simplejson.loads(data)
    if json_response['data']['tvYear']:
        p_year = int(json_response['data']['tvYear'])
    else:
        p_year = 0
    p_director = ' / '.join(json_response['data']['directors']).encode('utf-8')
    p_cast = [x.encode('utf-8') for x in json_response['data']['mainActors']]
    p_plot = json_response['data']['tvDesc'].encode('utf-8')

    albumType = json_response['data']['albumType']
    sourceId = json_response['data']['sourceId']
    if albumType in (1, 6, 9, 12, 13) and sourceId != 0:
        url = 'http://cache.video.qiyi.com/jp/sdvlst/%d/%d/?categoryId=%d&sourceId=%d' % (albumType, sourceId, albumType, sourceId)
        link = GetHttpData(url)
        data = link[link.find('=')+1:]
        json_response = simplejson.loads(data)
        totalItems = len(json_response['data'])
        for item in json_response['data']:
            tvId = str(item['tvId'])
            videoId = item['vid'].encode('utf-8')
            p_id = '%s,%s' % (tvId, videoId)
            p_thumb = item['aPicUrl'].encode('utf-8')
            p_name = item['videoName'].encode('utf-8')
            p_name = '%s %s' % (p_name, item['tvYear'].encode('utf-8'))
            li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
            li.setInfo(type="Video", infoLabels={"Title": p_name,
                                                 "Director": p_director,
                                                 "Cast": p_cast,
                                                 "Plot": p_plot,
                                                 "Year": p_year})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(p_id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)
    else:
        url = 'http://cache.video.qiyi.com/avlist/%s/%s/' % (id, page)
        link = GetHttpData(url)
        data = link[link.find('=')+1:]
        json_response = simplejson.loads(data)
        totalItems = len(json_response['data']['vlist']) + 1
        totalpages = json_response['data']['pgt']
        currpage = int(page)
        if currpage > 1:
            totalItems += 1
        if currpage < totalpages:
            totalItems += 1
        li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）')
        u = sys.argv[0]+"?mode=99"
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)

        for item in json_response['data']['vlist']:
            tvId = str(item['id'])
            videoId = item['vid'].encode('utf-8')
            p_id = '%s,%s' % (tvId, videoId)
            p_thumb = item['vpic'].encode('utf-8')
            p_name = item['vn'].encode('utf-8')
            if item['vt']:
                p_name = '%s %s' % (p_name, item['vt'].encode('utf-8'))
            li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
            li.setArt({'poster': thumb})
            li.setInfo(type="Video", infoLabels={"Title": p_name,
                                                 "Director": p_director,
                                                 "Cast": p_cast,
                                                 "Plot": p_plot,
                                                 "Year": p_year})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&id=" + urllib.quote_plus(p_id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)

        if currpage > 1:
            li = xbmcgui.ListItem('上一页')
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&thumb="+urllib.quote_plus(thumb)+"&page="+urllib.quote_plus(str(currpage-1))
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)
        if currpage < totalpages:
            li = xbmcgui.ListItem('下一页')
            u = sys.argv[0]+"?mode=2&name="+urllib.quote_plus(name)+"&id="+urllib.quote_plus(id)+"&thumb="+urllib.quote_plus(thumb)+"&page="+urllib.quote_plus(str(currpage+1))
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)

    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)


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
    return simplejson.loads(GetHttpData(vmsreq))


def PlayVideo(name, id, thumb):
    id = id.split(',')
    if len(id) == 1:
        try:
            if ("http:" in id[0]):
                link = GetHttpData(id[0])
                tvId = re.compile('data-player-tvid="(.+?)"', re.DOTALL).findall(link)[0]
                videoId = re.compile('data-player-videoid="(.+?)"', re.DOTALL).findall(link)[0]
            else:
                url = 'http://cache.video.qiyi.com/avlist/%s/' % (id[0])
                link = GetHttpData(url)
                data = link[link.find('=')+1:]
                json_response = simplejson.loads(data)
                tvId = str(json_response['data']['vlist'][0]['id'])
                videoId = json_response['data']['vlist'][0]['vid'].encode('utf-8')
        except:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '未能获取视频地址')
            return
    else:
        tvId = id[0]
        videoId = id[1]

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

    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    xbmc.Player().play(video_links, listitem)


def performChanges(name, listpage, cat, area, year, order, paytype):
    change = False
    catlist = getcatList(listpage, name, cat)
    dialog = xbmcgui.Dialog()
    if len(catlist) > 0:
        list = [x[1] for x in catlist]
        sel = dialog.select('类型', list)
        if sel != -1:
            cat = catlist[sel][0]
            change = True
    if name not in ('纪录片', '教育', '时尚'):
        arealist = getareaList(listpage, name, area)
        if len(arealist) > 0:
            list = [x[1] for x in arealist]
            sel = dialog.select('地区', list)
            if sel != -1:
                area = arealist[sel][0]
                change = True
    if name in ('电影', '电视剧'):
        yearlist = getyearList(listpage, name, year)
        if len(yearlist) > 0:
            list = [x[1] for x in yearlist]
            sel = dialog.select('年份', list)
            if sel != -1:
                year = yearlist[sel][0]
                change = True
    list = [x[1] for x in ORDER_LIST]
    sel = dialog.select('排序方式', list)
    if sel != -1:
        order = ORDER_LIST[sel][0]
        change = True
    if change:
        progList(name, '1', cat, area, year, order, paytype)

#  main program begins here #########
pluginhandle = int(sys.argv[1])
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

thumb = params.get('thumb')
url = params.get('url')
page = params.get('page', '1')
cat = params.get('cat', '')
id = params.get('id')
name = params.get('name')
area = params.get('area', '')
year = params.get('year', '')
order = params.get('order', '3')
paytype = params.get('paytype', '0')
mode = params.get('mode')

if mode is None:
    for name in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name) + \
            "&id="+urllib.quote_plus(CHANNEL_LIST[name]) + \
            "&cat="+urllib.quote_plus("") + \
            "&area="+urllib.quote_plus("") + \
            "&year="+urllib.quote_plus("") + \
            "&order="+urllib.quote_plus("11") + \
            "&page="+urllib.quote_plus("1") + \
            "&paytype="+urllib.quote_plus("0")
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)
    xbmcplugin.endOfDirectory(pluginhandle)

elif mode == '1':
    progList(name, page, cat, area, year, order, paytype)
elif mode == '2':
    seriesList(name, id, thumb, page)
elif mode == '3':
    PlayVideo(name, id, thumb)
elif mode == '4':
    performChanges(name, page, cat, area, year, order, paytype)
