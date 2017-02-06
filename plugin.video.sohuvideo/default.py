# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, urlparse, re, sys, os, gzip, StringIO
from random import random
import cookielib, datetime, time
import ChineseKeyboard
import simplejson

# Plugin constants
__addonname__ = "搜狐视频(SoHu)"
__addonid__   = "plugin.video.sohuvideo"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__settings__  = xbmcaddon.Addon(id=__addonid__)
__profile__   = xbmc.translatePath(__settings__.getAddonInfo('profile'))
cookieFile    = __profile__ + 'cookies.sohu'

CHANNEL_LIST = {'电影'  : '100',
                '电视剧': '101',
                '动漫'  : '115',
                '综艺'  : '106',
                '纪录片': '107',
                '音乐'  : '121',
                '教育'  : '119',
                '新闻 ' : '122',
                '娱乐 ' : '112',
                '星尚 ' : '130'}
ORDER_LIST = [['7', '周播放最多'],
              ['5', '日播放最多'],
              ['1', '总播放最多'],
              ['3', '最新发布'],
              ['4', '评分最高']]

LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

##################################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
##################################################################################
def getHttpData(url):
    if url[0:5] != 'http:':
        url = 'http:' + url
    # setup proxy support
    proxy = __addon__.getSetting('http_proxy')
    type = 'http'
    if proxy != '':
        ptype = re.split(':', proxy)
        if len(ptype) < 3:
            # full path requires by Python 2.4
            proxy = type + '://' + proxy
        else:
            type = ptype[0]
        httpProxy = {type: proxy}
    else:
        httpProxy = {}
    proxy_support = urllib2.ProxyHandler(httpProxy)

    # setup cookie support
    cj = cookielib.MozillaCookieJar(cookieFile)
    if os.path.isfile(cookieFile):
        cj.load(ignore_discard=True, ignore_expires=True)
    else:
        if not os.path.isdir(os.path.dirname(cookieFile)):
            os.makedirs(os.path.dirname(cookieFile))

    # create opener for both proxy and cookie
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPCookieProcessor(cj))
    charset = ''
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = opener.open(req)
    except urllib2.HTTPError, e:
        httpdata = e.read()
    except urllib2.URLError, e:
        httpdata = "IO Timeout Error"
    else:
        httpdata = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            if httpdata[-1] == '\n':
                httpdata = httpdata[:-1]
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
        response.close()

    httpdata = re.sub('\r|\n|\t', '', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')
    return httpdata


##################################################################################
# Routine to extract url ID from array based on given selected filter
##################################################################################
def searchDict(dlist, idx):
    for i in range(0, len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''


##################################################################################
# Routine to fetch and build video filter list
# tuple to list conversion and strip spaces
# - 按类型  (Categories)
# - 按地区 (Countries/Areas)
# - 按年份 (Year)
# - etc
# 类别 p2_p3
# 风格 p2_p3
# 子类 p3_p4
# 地区 p3_p4
# 年份 p4_p5
# 篇幅 p5_p6
# 年龄 p6_p7
#
##################################################################################
def getcatList(listpage, title, page):
    c1 = '<dt>%s</dt>\s*<dd class="sort-tag">(.+?)</dd>' % (title)
    c2 = 'p%d(.*?)_p%d.+?>(.+?)</a>' % (page, page + 1)
    match = re.compile(c1, re.DOTALL).findall(listpage)
    l = re.compile(c2, re.DOTALL).findall(match[0])
    return l


def getList16(listpage):
    pflist = getcatList(listpage, '篇幅：', 5)
    nllist = getcatList(listpage, '年龄：', 6)
    return pflist, nllist


def getList24(listpage):
    match = re.compile('<dt>类别：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    lxlist = re.compile('p5(.*?)_p6.+?html">(.+?)</a>', re.DOTALL).findall(match[0])
    match = re.compile('<dt>语言：</dt>\s*<dd class="sort-tag">(.+?)</dd>', re.DOTALL).findall(listpage)
    yylist = re.compile('_p101_p11(.+?).html">(.+?)</a>', re.DOTALL).findall(match[0])
    if len(yylist) > 0:
        yylist.insert(0, ['', '全部'])
    arealist = getcatList(listpage, '地区：', 3)
    fglist = getcatList(listpage, '风格：', 2)
    return lxlist, yylist, arealist, fglist


##################################################################################
# Routine to fetch & build Sohu 网络 main menu
# - Video Search
# - 电视直播
# - video list as per [CHANNEL_LIST]
##################################################################################
def rootList():
    # force sohu to give cookie; must use cookie for some categories fast response else timeout
    #http://pv.sohu.com/suv/?t?=1342163482 447275_1920_1200?r?=
    ticks = int(time.time())
    url_cookie = 'http://pv.sohu.com/suv/?t?='+str(ticks)+'866725_1920_1080?r?='
    link = getHttpData(url_cookie)

    li = xbmcgui.ListItem('[COLOR F0F0F0F0] Sohu 搜库网:[/COLOR][COLOR FF00FF00]【请输入搜索内容】[/COLOR]')
    u = sys.argv[0]+"?mode=21"
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    name = '电视直播'
    li = xbmcgui.ListItem(name)
    u = sys.argv[0]+"?mode=10&name="+urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    for name in CHANNEL_LIST:
        if name == '星尚 ':
            order = '1'
        else:
            order = '7'
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(name) + \
            "&id="+urllib.quote_plus(CHANNEL_LIST[name]) + \
            "&page=1"+"&cat="+"&area="+"&year="+"&p5="+"&p6="+"&p11="+"&order="+order
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)
    xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
# Routine to fetch and build the video selection menu
# - selected page & filters (user selectable)
# - video items list
# - user selectable pages
# ########### url parameter decode ##############
# http://so.tv.sohu.com/list_p1100_p2_p3_p4_p5_p6_p7_p8_p9.html
# p1: 分类: 100=电影;电视剧=101;动漫=115;综艺=106 etc
# p2: 类型： 全部 爱情 动作 喜剧 科幻 战争 恐怖 风月 剧情 歌舞 动画 纪录
# p3: 产地： 全部 华语 好莱坞 欧洲 日本 韩国 其他
# p4: 年份： 全部 2012 2011
# p5: 篇幅(动漫 )：全部 电影 连续剧 预告片 其他
# p6: 年龄(动漫 )：全部 5岁以下 5岁-12岁 13岁-18岁 18岁以上
# p7: 相关程度: 5=日播放最多;7=周播放最多;1=总播放最多;3=最新发布;4=评分最高
# p8: 付费： 0=全部;2=免费;1=VIP;3=包月;4=点播
# p9: 状态: 2d2=全部;2d1=正片;2d3=非正片
# p10: page
# p11:
##################################################################################
def progList(name, page, cat, area, year, p5, p6, p11, order):
    url = 'http://so.tv.sohu.com/list_p1'+CHANNEL_LIST[name] + \
            '_p2'+cat+'_p3'+area+'_p4'+year+'_p5'+p5+'_p6'+p6+'_p7'+order
    if name in ('电影', '电视剧'):
        url += '_p82_p9_2d1'
    else:
        url += '_p8_p9'
    url += '_p10'+page+'_p11'+p11+'.html'

    currpage = int(page)
    link = getHttpData(url)
    match = re.compile('<div class="ssPages area">(.+?)</div>', re.DOTALL).findall(link)
    if not match:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '没有符合条件的视频')
    else:
        matchpages = re.compile('<a title="\d+" href="[^"]*">(\d+)</a>', re.DOTALL).findall(match[0])
        totalpages = int(matchpages[-1])
        if totalpages < currpage:
            totalpages = currpage
        match = re.compile('<div class="sort-type">(.+?)</div>', re.DOTALL).findall(link)
        if len(match):
            listpage = match[0]
        else:
            listpage = ''

        match = re.compile('<li>(.+?)</li>', re.DOTALL).findall(link)
        totalItems = len(match) + 1
        if currpage > 1:
            totalItems += 1
        if currpage < totalpages:
            totalItems += 1
        lxstr = ''
        if name != '音乐':
            if name == '教育':
                catlist = getcatList(listpage, '子类：', 3)
            else:
                catlist = getcatList(listpage, '类别：', 2)
            lxstr += '[COLOR FFFF0000]'
            if cat:
                lxstr += searchDict(catlist, cat)
            else:
                lxstr += '全部类型'
            lxstr += '[/COLOR]'

        if name in ('电影', '电视剧', '综艺'):
            lxstr += '/[COLOR FF00FF00]'
            arealist = getcatList(listpage, '地区：', 3)
            if area:
                lxstr += searchDict(arealist, area)
            else:
                lxstr += '全部地区'
            lxstr += '[/COLOR]'

        if name == '动漫':
            lxstr += '/[COLOR FFFFFF00]'
            pflist, nllist = getList16(listpage)
            if p5:
                lxstr += searchDict(pflist, p5)
            else:
                lxstr += '全部篇幅'
            lxstr += '[/COLOR]/[COLOR FF00FF00]'
            if p6:
                lxstr += searchDict(nllist, p6)
            else:
                lxstr += '全部年龄'
            lxstr += '[/COLOR]'

        if name == '音乐':
            lxstr += '[COLOR FFFF0000]'
            lxlist, yylist, arealist, fglist = getList24(listpage)
            if p5:
                lxstr += searchDict(lxlist, p5)
            else:
                lxstr += '全部类型'
            lxstr += '[/COLOR]/[COLOR FF00FF00]'
            if p11:
                lxstr += searchDict(yylist, p11)
            else:
                lxstr += '全部语言'
            lxstr += '[/COLOR]/[COLOR FFFF5555]'
            if area:
                lxstr += searchDict(arealist, area)
            else:
                lxstr += '全部地区'
            lxstr += '[/COLOR]/[COLOR FFFF00FF]'
            if cat:
                lxstr += searchDict(fglist, cat)
            else:
                lxstr += '全部风格'
            lxstr += '[/COLOR]'

        if name in ('电影', '电视剧', '动漫', '音乐'):
            lxstr += '/[COLOR FF5555FF]'
            yearlist = getcatList(listpage, '年份：', 4)
            if year == '':
                lxstr += '全部年份'
            elif year in ('80', '90'):
                lxstr += year+'年代'
            elif year == '100':
                lxstr += '更早年代'
            else:
                lxstr += year+'年'
            lxstr += '[/COLOR]'

        li = xbmcgui.ListItem(name+'（第'+str(currpage)+'/'+str(totalpages)+'页）【' + lxstr + '/[COLOR FF00FFFF]' + searchDict(ORDER_LIST,order) + '[/COLOR]】（按此选择）')
        u = sys.argv[0]+"?mode=4&name="+urllib.quote_plus(name)+ \
                "&id="+CHANNEL_LIST[name]+"&cat="+cat+"&area="+area+"&year="+year+"&p5="+p5+"&p6="+p6+"&p11="+p11+"&order="+"&listpage="+urllib.quote_plus(listpage)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)

        for i in range(0, len(match)):
            match1 = re.compile('<a href="([^"]+)" title="([^"]+)" target="_blank"', re.DOTALL).search(match[i])
            if match1:
                p_name = match1.group(2)
                p_url = match1.group(1)
            else:
                match1 = re.compile('<a title="([^"]+)" target="_blank" href="([^"]+)"', re.DOTALL).search(match[i])
                if match1:
                    p_name = match1.group(1)
                    p_url = match1.group(2)
                else:
                    match1 = re.compile('<a .*?title="([^"]+)"', re.DOTALL).search(match[i])
                    p_name = match1.group(1)
                    match1 = re.compile('<a .*?href="([^"]+)"', re.DOTALL).search(match[i])
                    p_url = match1.group(1)

            match1 = re.compile('<img.*?src="([^"]+)"', re.DOTALL).search(match[i])
            p_thumb = match1.group(1)
            p_rating = 0
            p_votes = ''
            p_director = ''
            p_genre = ''
            match1 = re.compile('<p class="lh-info">(.+?)</p>').search(match[i])
            if match1:
                p_plot = match1.group(1)
            else:
                p_plot = ''
            p_year = 0

            if name in ('电视剧', '动漫', '综艺', '纪录片', '教育'):
                p_dir = True
                mode = '2'
            else:
                p_dir = False
                mode = '3'

            match1 = re.compile('<span class="maskTx">(.+?)</span>').search(match[i])
            if match1:
                p_name1 = p_name + ' [' + match1.group(1) + ']'
            else:
                p_name1 = p_name
            if match[i].find('<span class="rl-phua"></span>') > 0:
                p_name1 += ' [片花]'
            elif match[i].find('<span class="rl-rep"></span>') > 0:
                p_name1 += ' [预告]'
            elif match[i].find('<span class="rl-fuf"></span>') > 0:
                p_name1 += ' [付费]'
            if match[i].find('<a title="超清" class="super">') > 0:
                p_name1 += ' [超清]'
                p_res = 2
            elif match[i].find('<a title="原画" class="origin">') > 0:
                p_name1 += ' [原画]'
                p_res = 1
            else:
                p_res = 0

            li = xbmcgui.ListItem(str(i + 1) + '. ' + p_name1, iconImage='', thumbnailImage=p_thumb)
            u = sys.argv[0]+"?mode="+mode+"&name="+urllib.quote_plus(p_name)+"&url="+urllib.quote_plus(p_url)+"&thumb="+urllib.quote_plus(p_thumb)+"&id="+urllib.quote_plus(str(i))
            li.setInfo(type="Video", infoLabels ={"Title": p_name, "Director": p_director, "Genre":p_genre, "Plot":p_plot, "Year":p_year, "Rating":p_rating, "Votes":p_votes})
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, p_dir, totalItems)

        # Fetch and build user selectable page number
        if matchpages:
            for num in matchpages:
                li = xbmcgui.ListItem("... 第" + num + "页")
                u = sys.argv[0]+"?mode=1&name="+urllib.quote_plus(name)+ \
                        "&id="+CHANNEL_LIST[name] + "&page="+str(num)+ \
                        "&cat="+cat+"&area="+area+"&year="+year+\
                        "&p5="+p5+"&p6="+p6+"&p11="+p11+"&order="+order
                xbmcplugin.addDirectoryItem(pluginhandle, u, li, True, totalItems)

        xbmcplugin.setContent(pluginhandle, 'movies')
        xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
# Routine to fetch and build the video series selection menu
# - for 电视剧  & 动漫
# - selected page & filters (user selectable)
# - Video series list
# - user selectable pages
##################################################################################
def seriesList(name, url, thumb):
    link = getHttpData(url)
    if url.find('.html') > 0:
        match0 = re.compile('var playlistId\s*=\s*"(.+?)";', re.DOTALL).findall(link)
        link = getHttpData('http://hot.vrs.sohu.com/vrs_videolist.action?playlist_id='+match0[0])
        match = re.compile('"videoImage":"(.+?)",.+?"videoUrl":"(.+?)".+?"videoOrder":"(.+?)",', re.DOTALL).findall(link)
        totalItems = len(match)

        for p_thumb, p_url, p_order in match:
            p_name = '%s第%s集' % (name, p_order)
            li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
            li.setInfo(type="Video", infoLabels={"Title": p_name, "episode": int(p_order)})
            u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(p_url)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)
    else:
        match0 = re.compile('var pid\s*=\s*(.+?);', re.DOTALL).findall(link)
        if len(match0) > 0:
            # print 'pid=' + match0[0]
            pid = match0[0].replace('"', '')
            match0 = re.compile('var vid\s*=\s*(.+?);', re.DOTALL).findall(link)
            vid = match0[0].replace('"', '')
            if vid == '0':
                dialog = xbmcgui.Dialog()
                ok = dialog.ok(__addonname__, '节目不能播放')
                return
            obtype = '2'
            link = getHttpData("http://search.vrs.sohu.com/avs_i"+vid+"_pr"+pid+"_o"+obtype+"_n_p1000_chltv.sohu.com.json")
            data = link.replace('var video_album_videos_result=','').decode('raw_unicode_escape')
            js = simplejson.loads(data)
            try:
                match = js['videos']
            except:
                xbmcgui.Dialog().ok(__addonname__, 'videos not found')
                return
            totalItems = len(match)
            for item in match:
                p_name = item['videoName'].encode('utf-8')
                p_url = item['videoUrl'].encode('utf-8')
                p_thumb = item['videoBigPic'].encode('utf-8')
                p_plot = item['videoDesc'].encode('utf-8')
                p_rating = item['videoScore']
                p_votes = int(item['videoVoters'])
                p_order = int(item['playOrder'])
                if 'videoPublishTime' in item:
                    p_time = item['videoPublishTime']
                    p_date = datetime.date.fromtimestamp(float(p_time)/1000).strftime('%d.%m.%Y')
                else:
                    p_date = ''
                li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
                li.setInfo(type="Video", infoLabels={"Title":p_name, "date":p_date, "episode":p_order, "plot":p_plot, "rating":p_rating, "votes":p_votes})
                u = sys.argv[0] + "?mode=3&name=" + urllib.quote_plus(p_name) + "&url=" + urllib.quote_plus(p_url)+ "&thumb=" + urllib.quote_plus(p_thumb)
                xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)
        else:
            match = re.compile('<a([^>]*)><IMG([^>]*)></a>',re.I).findall(link)
            thumbDict = {}
            for i in range(0, len(match)):
                p_url = re.compile('href="(.+?)"').findall(match[i][0])
                if len(p_url) > 0:
                    p_url = p_url[0]
                else:
                    p_url = match[i][0]
                p_thumb = re.compile('src="(.+?)"').findall(match[i][1])
                if len(p_thumb) > 0:
                    p_thumb = p_thumb[0]
                else:
                    p_thumb = match[i][1]
                thumbDict[p_url] = p_thumb
            #for img in thumbDict.items():
            url = 'http://so.tv.sohu.com/mts?c=2&wd=' + urllib.quote_plus(name.decode('utf-8').encode('gbk'))
            html = getHttpData(url)
            match = re.compile('class="serie-list(.+?)</div>').findall(html)
            if not match:
                return
            items = re.compile('<a([^>]*)>(.+?)</a>', re.I).findall(match[0])
            totalItems = len(items)
            for item in items:
                if item[1] == '展开>>':
                    continue
                href = re.compile('href="(.+?)"').findall(item[0])
                if len(href) > 0:
                    p_url = href[0]
                    urlKey = re.compile('u=(http.+?.shtml)').search(p_url)
                    if urlKey:
                        urlKey = urllib.unquote(urlKey.group(1))
                    else:
                        urlKey = p_url
                    # print urlKey
                    try:
                        p_thumb = thumbDict[urlKey]
                    except:
                        p_thumb = thumb
                    #title = re.compile('title="(.+?)"').findall(item)
                    #if len(title)>0:
                        #p_name = title[0]
                    p_name = name + '第' + item[1].strip() + '集'
                    li = xbmcgui.ListItem(p_name, iconImage=p_thumb, thumbnailImage=p_thumb)
                    u = sys.argv[0] + "?mode=3&name="+urllib.quote_plus(p_name)+\
                            "&id="+CHANNEL_LIST[name]+\
                            "&url="+urllib.quote_plus(p_url)+\
                            "&thumb="+urllib.quote_plus(p_thumb)
                    xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)

    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.endOfDirectory(pluginhandle)


# 类型选择对话
def setupList(list, title, origitem):
    if (len(list) > 0):
        l = [x[1] for x in list]
        dialog = xbmcgui.Dialog()
        sel = dialog.select(title, l)
        if sel != -1:
            if sel == 0:
                item = ''
            else:
                item = list[sel][0]
            return True, item  # item changed

    return False, origitem     # item not changed


##################################################################################
# Routine to update video list as per user selected filters
# - 按类型  (Categories)
# - 按地区 (Areas)
# - 按年份 (Year)
# - 排序方式 (Selection Order) etc
##################################################################################
def performChanges(name, cat, area, year, p5, p6, p11, order, listpage):
    change = False
    if name != '音乐':
        if name == '教育':
            catlist = getcatList(listpage, '子类：', 3)
        else:
            catlist = getcatList(listpage, '类别：', 2)
        change, cat = setupList(catlist, '类型', cat)

    if name in ('电影', '电视剧', '综艺'):
        arealist = getcatList(listpage, '地区：', 3)
        change, area = setupList(arealist, '地区', area)

    if name == '动漫':
        pflist, nllist = getList16(listpage)
        change, p5 = setupList(pflist, '篇幅', p5)
        change, p6 = setupList(nllist, '年龄', p6)

    if name == '音乐':
        lxlist, yylist, arealist, fglist = getList24(listpage)
        change, p5 = setupList(lxlist, '类型', p5)
        change, p11 = setupList(yylist, '语言', p11)
        change, area = setupList(arealist, '地区', area)
        change, cat = setupList(fglist, '风格', cat)

    if name in ('电影', '电视剧', '动漫', '音乐'):
        yearlist = getcatList(listpage, '年份：', 4)
        change, year = setupList(yearlist, '年份', year)

    change, order = setupList(ORDER_LIST, '排序方式', order)
    if change:
        progList(name, '1', cat, area, year, p5, p6, p11, order)


##################################################################################
# Routine to search Sohu site based on user given keyword for:
# http://so.tv.sohu.com/mts?chl=&tvType=-2&wd=love&whole=1&m=1&box=1&c=100&o=1&p=2
# c: 类型：''=全部 100=电影 101=电视剧 106=综艺 121=音乐 122=新闻 112=娱乐 0=其它
# o:排序方式： ''=相关程度 1=最多播放 3=最新发布
##################################################################################
def sohuSearchList(name, url, page):
    # construct url based on user selected item
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=' + page
    link = getHttpData(p_url)

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] (' + name + ')[/COLOR]【[COLOR FF00FF00]' + '请输入新搜索内容' + '[/COLOR]】')
    u = sys.argv[0] + "?mode=21&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url) + "&page=" + urllib.quote_plus(page)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    #########################################################################
    # Video listing for all found related episode title
    #########################################################################
    matchp = re.compile('<div class="ssItem cfix">(.+?)<div class="alike">').findall(link)
    totalItems = len(matchp)
    for i in range(0, totalItems):
        vlink = matchp[i]
        if vlink.find('<em class="pay"></em>') > 0:
            continue

        match1 = re.compile('href="(.+?)"').findall(vlink)
        p_url = match1[0]

        match1 = re.compile('title="(.+?)"').search(vlink)
        p_name = match1.group(1)

        match1 = re.compile('src="(.+?)"').search(vlink)
        p_thumb = match1.group(1)

        match1 = re.compile('<span class="maskTx">(.*?)</span>').search(vlink)
        if match1 and match1.group(1) != '':
            p_label = ' [' + match1.group(1) + ']'
        else:
            p_label = ''

        p_type = ''
        isTeleplay = False
        match1 = re.compile('<span class="label-red"><em>(.+?)</em></span>').search(vlink)
        if match1:
            p_type = match1.group(1)
        if p_type == '电视剧':
            isTeleplay = True
            mode = '2'
            p_type = '【[COLOR FF00FF00]电视剧[/COLOR]】'
        elif p_type == '电影':
            p_type = '【[COLOR FF00FF00]电影[/COLOR]】'
            mode = '3'
        else:
            p_type = ' ' + p_type
            mode = '3'

        p_list = str(i+1) + ': ' + p_name + p_type + p_label
        li = xbmcgui.ListItem(p_list, iconImage=p_thumb, thumbnailImage=p_thumb)
        u = sys.argv[0] + "?mode=" + mode + "&name=" + \
                urllib.quote_plus(p_name) + "&id=101" + \
                "&url=" + urllib.quote_plus(p_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, isTeleplay, totalItems)

    xbmcplugin.setContent(pluginhandle, 'movies')
    xbmcplugin.endOfDirectory(pluginhandle)


#################################################################################
# Get user input for Sohu site search
##################################################################################
def searchSohu():
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
        sohuSearchList(keyword, url, '1')


##################################################################################
# Sohu Video Link Decode Algorithm & Player
# Extract all the video list and start playing first found valid link
# User may press <SPACE> bar to select video resolution for playback
##################################################################################
def PlayVideo(name, url, thumb):
    level = int(__addon__.getSetting('resolution'))
    site = int(__addon__.getSetting('videosite'))

    link = getHttpData(url)
    match1 = re.compile('var vid="(.+?)";').search(link)
    if not match1:
        match1 = re.compile('<a href="(http://[^/]+/[0-9]+/[^\.]+.shtml)" target="?_blank"?><img').search(link)
        if match1:
            PlayVideo(name, match1.group(1), thumb)
        return
    p_vid = match1.group(1)
    if p_vid == '0':
        match1 = re.compile('data-vid="([^"]+)"').search(link)
        if not match1:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '节目暂不能播放')
            return
        p_vid = match1.group(1)
    if p_vid.find(',') > 0:
        p_vid = p_vid.split(',')[0]

    p_url = 'http://hot.vrs.sohu.com/vrs_flash.action?vid='+ p_vid
    link = getHttpData(p_url)
    match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?),').search(link)
    if not match:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '节目没找到')
        return
    ratelist = []
    if match.group(4) != '0':
        ratelist.append(['原画', 4])
    if match.group(3) != '0':
        ratelist.append(['超清', 3])
    if match.group(2) != '0':
        ratelist.append(['高清', 2])
    if match.group(1) != '0':
        ratelist.append(['流畅', 1])
    if level == 4:
        dialog = xbmcgui.Dialog()
        list = [x[0] for x in ratelist]
        if len(ratelist) == 1:
            rate = ratelist[0][1]
        else:
            sel = dialog.select('视频清晰度（低网速请选择低清晰度-流畅）', list)
            if sel == -1:
                return
            else:
                rate = ratelist[sel][1]
    else:
        rate = ratelist[0][1]
        if rate > level + 1:
            rate = level + 1

    hqvid = match.group(rate)
    if hqvid != str(p_vid):
        link = getHttpData('http://hot.vrs.sohu.com/vrs_flash.action?vid='+hqvid)

    info = simplejson.loads(link)
    host = info['allot']
    prot = info['prot']
    tvid = info['tvid']
    urls = []
    data = info['data']
    name = data['tvName'].encode('utf-8')
    size = sum(data['clipsBytes'])
    assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
    for new, clip, ck, in zip(data['su'], data['clipsURL'], data['ck']):
        clipURL = urlparse.urlparse(clip).path
        url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ ck+'&vid='+str(hqvid)+'&uid='+str(int(time.time()*1000))+'&t='+str(random())+'&rb=1'
        videourl = simplejson.loads(getHttpData(url))['url'].encode('utf-8')
        videourl = '%s|Range=' % (videourl)
        urls.append(videourl)

    stackurl = 'stack://' + ' , '.join(urls)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": name})
    xbmc.Player().play(stackurl, listitem)


##################################################################################
# Sohu 电视直播 Menu List
##################################################################################
def LiveChannel():
    link = getHttpData('http://tvimg.tv.itc.cn/live/stations.jsonp')
    match = re.compile('var par=({.+?});', re.DOTALL).search(link)
    if match:
        parsed_json = simplejson.loads(match.group(1))
        totalItems = len(parsed_json['STATIONS'])
        i = 0
        for item in parsed_json['STATIONS']:
            if (item['IsSohuSource'] != 1) or (item['TV_TYPE'] != 1):
                continue
            p_name = item['STATION_NAME'].encode('utf-8')
            p_thumb = item['STATION_PIC'].encode('utf-8')
            id = str(item['STATION_ID'])
            i += 1
            li = xbmcgui.ListItem(str(i) + '. ' + p_name, iconImage='', thumbnailImage=p_thumb)
            u = sys.argv[0] + "?mode=11&name=" + urllib.quote_plus(p_name) + \
                    "&id=" + urllib.quote_plus(id)+ "&thumb=" + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(pluginhandle, u, li, False, totalItems)

    xbmcplugin.setContent(pluginhandle, 'movies')
    xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
# Sohu 电视直播 Player
##################################################################################
def LivePlay(name, id, thumb):
    link = getHttpData(LIVEID_URL % (id))
    parsed_json = simplejson.loads(link)
    url = 'http://' + parsed_json['data']['clipsURL'][0].encode('utf-8')
    link = getHttpData(url)
    parsed_json = simplejson.loads(link)
    url = parsed_json['url'].encode('utf-8')
    li = xbmcgui.ListItem(name, iconImage='', thumbnailImage=thumb)
    xbmc.Player().play(url, li)


# main programs goes here #########################################
pluginhandle = int(sys.argv[1])

params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

name = params.get('name')
id = params.get('id', '')
cat = params.get('cat', '')
area = params.get('area', '')
year = params.get('year', '')
order = params.get('order', '')
page = params.get('page', '')
p5 = params.get('p5', '')
p6 = params.get('p6', '')
p11 = params.get('p11', '')
listpage = params.get('listpage', '')
url = params.get('url')
thumb = params.get('thumb')

mode = params.get('mode')
if mode is None:
    rootList()
elif mode == '1':
    progList(name, page, cat, area, year, p5, p6, p11, order)
elif mode == '2':
    seriesList(name, url, thumb)
elif mode == '3':
    PlayVideo(name, url, thumb)
elif mode == '4':
    performChanges(name, cat, area, year, p5, p6, p11, order, listpage)
elif mode == '10':
    LiveChannel()
elif mode == '11':
    LivePlay(name, id, thumb)
elif mode == '21':
    searchSohu()
elif mode == '22':
    sohuSearchList(name, url, page)
