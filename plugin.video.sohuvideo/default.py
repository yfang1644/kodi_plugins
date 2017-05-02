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
from random import random
import cookielib
import datetime
import time
import simplejson
from bs4 import BeautifulSoup

########################################################################
# 搜狐视频 tv.sohu.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cookieFile    = __profile__ + 'cookies.sohu'

if (__addon__.getSetting('keyboard') == '0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'
HOST_URL = 'http://tv.sohu.com'
LIST_URL = 'http://so.tv.sohu.com'
PROGRAM_URL = 'http://poll.hd.sohu.com/live/stat/menu-segment.jsonp?num=8&sid=%d'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'


############################################################################
# Sohu Video Link Decode Algorithm & Player
# Extract all the video list and start playing first found valid link
# User may press <SPACE> bar to select video resolution for playback
############################################################################
def get_vid_from_url(url):
    link = getHttpData(url)

    match1 = re.compile("var vid\s*=\s*'(.+?)';").search(link)
    if not match1:
        match1 = re.compile('<a href="(http://[^/]+/[0-9]+/[^\.]+.shtml)" target="?_blank"?><img').search(link)
        if match1:
            params['url'] = match1.group(1)
            PlayVideo(params)
        return
    p_vid = match1.group(1)
    if p_vid == '0':
        match1 = re.compile('data-vid="([^"]+)"').search(link)
        if not match1:
            return None
        p_vid = match1.group(1)
    if p_vid.find(',') > 0:
        p_vid = p_vid.split(',')[0]
    return p_vid


def PlayVideo(params):
    p_vid = params.get('vid')
    if p_vid is None:
        p_vid = get_vid_from_url(params['url'])
        if p_vid is None:
            xbmcgui.Dialog().ok(__addonname__, '节目暂不能播放')
            return

    thumb = params.get('thumb', '')
    level = int(__addon__.getSetting('resolution'))
    site = int(__addon__.getSetting('videosite'))

    v_api1 = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s'
    v_api2 = 'http://my.tv.sohu.com/play/videonew.do?vid=%s&referer=http://my.tv.sohu.com'
    v_api = v_api1
    link = getHttpData(v_api % p_vid)
    match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?),').search(link)
    if not match:
        v_api = v_api2
        link = getHttpData(v_api % p_vid)
        match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?),').search(link)
        if not match:
            xbmcgui.Dialog().ok(__addonname__, '节目没找到')
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
    if hqvid != str(p_vid) and v_api == v_api1:
        link = getHttpData(v_api % hqvid)
    else:
        hqvid = p_vid

    info = simplejson.loads(link)
    host = info['allot']
    prot = info['prot']
    tvid = info['tvid']
    urls = []
    data = info['data']
    title = data['tvName'].encode('utf-8')
    # size = sum(data['clipsBytes'])
    assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
    for new, clip, ck, in zip(data['su'], data['clipsURL'], data['ck']):
        clipURL = urlparse.urlparse(clip).path
        url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ ck+'&vid='+str(hqvid)+'&rb=1'
        videourl = simplejson.loads(getHttpData(url))['url'].encode('utf-8')
        videourl = '%s|Range=' % (videourl)
        urls.append(videourl)

    stackurl = 'stack://' + ' , '.join(urls)
    listitem = xbmcgui.ListItem(title, thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={"Title": title})
    xbmc.Player().play(stackurl, listitem)


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


############################################################################
# Routine to fetech url site data using Mozilla browser
# - delete '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
############################################################################
def getHttpData(url):
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
        if response.headers.get('content-encoding') == 'gzip':
            if httpdata[-1] == '\n':
                httpdata = httpdata[:-1]
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
        response.close()

    httpdata = re.sub('\r|\n|\t', ' ', httpdata)
    match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
    if len(match):
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')
    return httpdata


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【搜狐视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    name = u'电视直播'
    li = xbmcgui.ListItem(name)
    u = sys.argv[0] + '?url=' + 'http://tvimg.tv.itc.cn/live/stations.jsonp'
    u += '&mode=livechannel&name=' + name

    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = '/list_p1_p2_p3_p4_p5_p6_p7_p8_p9_p10_p11_p12_p13.html'
    html = getHttpData(LIST_URL + url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'sort-nav cfix'})

    grp = soup[0].find_all('a')
    for prog in grp[1:]:
        title = prog.text.strip(' ')
        href = prog['href']
        href = httphead(href)
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=%s&mode=videolist&name=%s' % (href, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    url = params['url']
    name = params.get('name')
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')
    p10 = lurl[10]
    page = int(p10[3:]) if len(p10) > 3 else 1
    li = xbmcgui.ListItem(BANNER_FMT % (name+'【第%d页】(分类过滤)' % (page)))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    items = tree.find_all('ul', {'class': 'st-list'})
    items = items[0].find_all('li')
    for item in items:
        pic = item.find('div', {'class': 'st-pic'})
        href = pic.a.get('href')
        href = httphead(href)
        img = pic.img.get('src')
        img = httphead(img)
        try:
            hover = item.find('div', {'class': 'list-hover'})
            title = hover.a.text
        except:
            title = pic.img.get('alt')
        if len(title) == 0:
            title = pic.a.get('title', '')

        try:
            info = item.find('p', {'class': 'lh-info'}).text
        except:
            info = ''

        try:
            mask = item.find('span', {'class': 'maskTx'}).text
        except:
            mask = ''
        extra = '[COLOR FF8080FF]'
        auth = item.find('span', {'class': 'rl-hyuan'})
        if auth:
            extra += u'会员 '
        auth = item.find('span', {'class': 'rl-dbo'})
        if auth:
            extra += u'独播'
        extra += '[/COLOR]'

        li = xbmcgui.ListItem(title + ' ' + mask + ' ' + extra,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        if name in ('电视剧', '动漫', '综艺', '娱乐', '纪录片', '明星', '体育'):
            mode = 'episodelist1'
        elif name in ('搞笑', '游戏', '新闻', '做饭', '科技', '学习考试', '自媒体'):
            mode = 'episodelist2'
        else:
            mode = 'playvideo'
        u = sys.argv[0] + '?url=' + href
        u += '&mode=' + mode
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(img)
        u += '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    u = sys.argv[0] + '?url=' + href
    li = xbmcgui.ListItem(INDENT_FMT0 % ('分页'))
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    pages = tree.find_all('div', {'class': 'ssPages area'})
    pages = pages[0].find_all('a')
    for page in pages:
        title = page['title'].encode('utf-8')
        href = httphead(page['href'])
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('dl', {'class': 'cfix'})

    dialog = xbmcgui.Dialog()

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')

    for item in filter:
        title = item.dt.text
        si = item.find_all('a')
        list = []
        for x in si:
            if x.get('class') == ['aon']:
                list.append('[COLOR FFF0F000]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel]['href'].split('/')
        selurl = re.compile('(.+?).html').findall(selurl[-1])
        selurl = selurl[0].split('_')
        for i in range(1, 14):
            if selurl[i] != 'p%d' % i:
                lurl[i] = selurl[i]

    surl[-1] = '_'.join(lurl) + '.html'
    url = '/'.join(surl)
    params['url'] = url
    listSubMenu(params)


def episodesList1(params):
    name = params['name']
    title0 = params.get('title', '')
    url = params['url']
    link = getHttpData(url)
    tree = BeautifulSoup(link, 'html.parser')

    listapi = 'http://hot.vrs.sohu.com/vrs_videolist.action?'
    if url.find('.html') > 0:
        match0 = re.compile('var playlistId\s*=\s*"(.+?)";', re.DOTALL).findall(link)

        link = getHttpData(listapi + 'playlist_id=' + match0[0])
        match = re.compile('"videoImage":"(.+?)",.+?"videoUrl":"(.+?)".+?"videoId":(.+?),.+?"videoOrder":"(.+?)",', re.DOTALL).findall(link)
        totalItems = len(match)

        for p_thumb, p_url, p_vid, p_order in match:
            p_name = '%s第%s集' % (title0, p_order)
            li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
            li.setInfo(type="Video",
                       infoLabels={"Title": p_name, "episode": int(p_order)})
            u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url) + '&mode=playvideo'
            u += '&name=' + name + '&title=' + urllib.quote_plus(p_name)
            u += '&thumb=' + urllib.quote_plus(p_thumb)
            u += '&vid=' + p_vid
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
    else:
        match0 = re.compile('var pid\s*=\s*(.+?);', re.DOTALL).findall(link)
        if len(match0) > 0:
            # print 'pid=' + match0[0]
            pid = match0[0].replace('"', '')
            match0 = re.compile('var vid\s*=\s*(.+?);', re.DOTALL).findall(link)
            vid = match0[0].replace('"', '')
            if vid == '0':
                dialog = xbmcgui.Dialog()
                ok = dialog.ok(__addonname__, '当前节目暂不能播放')

            obtype = '2'
            s_api = 'http://search.vrs.sohu.com/v?id=%s&pid=%s&pageNum=1&pageSize='
            s_api = 'http://search.vrs.sohu.com/avs_i%s_pr%s_o2_n_p1000_chltv.sohu.com.json'
            link = getHttpData(s_api % (vid, pid))
            link = link[link.find('=')+1:]
            data = link.decode('raw_unicode_escape')
            match = simplejson.loads(data)['videos']
            totalItems = len(match)
            for item in match:
                p_name = item['videoName'].encode('utf-8')
                p_url = item['videoUrl'].encode('utf-8')
                p_thumb = item['videoBigPic'].encode('utf-8')
                p_plot = item['videoDesc'].encode('utf-8')
                p_rating = item['videoScore']
                p_votes = int(item['videoVoters'])
                p_vid = item['vid']
                p_order = int(item['playOrder'])
                try:
                    p_time = item['videoPublishTime']
                    p_date = datetime.date.fromtimestamp(float(p_time)/1000).strftime('%d.%m.%Y')
                except:
                    p_date = ''
                li = xbmcgui.ListItem(p_name,
                                      iconImage='', thumbnailImage=p_thumb)
                li.setInfo(type="Video",
                           infoLabels={"Title": p_name,
                                       "date": p_date,
                                       "episode": p_order,
                                       "plot": p_plot,
                                       "rating": p_rating,
                                       "votes": p_votes})
                u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url)
                u += '&mode=playvideo&name=' + name
                u += '&title=' + p_name
                u += '&thumb=' + p_thumb + '&vid=%d' % p_vid
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)
        else:
            match = re.compile('<a([^>]*)><IMG([^>]*)></a>', re.I).findall(link)
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
            if match:
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
                        p_thumb = thumbDict.get(urlKey, thumb)
                        #title = re.compile('title="(.+?)"').findall(item)
                        #if len(title)>0:
                            #p_name = title[0]
                        p_name = title0 + '第' + item[1].strip() + '集'
                        li = xbmcgui.ListItem(p_name,
                                              iconImage=p_thumb, thumbnailImage=p_thumb)
                        u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url)
                        u += '&mode=playvideo&name=' + name
                        u += '&title=' + urllib.quote_plus(p_name)
                        u += '&thumb=' + urllib.quote_plus(p_thumb)
                        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup1 = tree.find_all('ul', {'class': 'list listA cfix'})
    soup2 = tree.find_all('ul', {'class': 'list list-120 cfix'})

    if len(soup1) > 1:
        for part in soup1[1:]:
            drama = part.find_all('li')
            for item in drama:
                img = httphead(item.img['src'])
                try:
                    title = item.strong.a['title']
                except:
                    title = item.a.text
                href = httphead(item.a['href'])
                li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                li.setInfo(type='Video', infoLabels={'Title': title})
                u = sys.argv[0] + '?url=' + href + '&mode=playvideo'
                u += '&name=' + urllib.quote_plus(name) + '&thumb=' + img
                u += '&title=' + title
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    if len(soup2) > 0:
        for part in soup2:
            drama = part.find_all('li')

            for item in drama:
                img = httphead(item.img['src'])
                try:
                    title = item.strong.a['title']
                except:
                    title = item.a.text
                href = httphead(item.a['href'])
                li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
                li.setInfo(type='Video', infoLabels={'Title': title})
                u = sys.argv[0] + '?url=' + href + '&mode=episodelist1'
                u += '&name=' + urllib.quote_plus(name) + '&thumb=' + img
                u += '&title=' + title
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
    #xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList2(params):
    name = params['name']
    title0 = params.get('title', '')
    url = params['url']
    link = getHttpData(url)
    tree = BeautifulSoup(link, 'html.parser')

    listapi = 'http://my.tv.sohu.com/play/getvideolist.do?playlistid=%s&pagesize=30&order=1'

    match0 = re.compile("playlistId\s*=\s*'(.+?)';", re.DOTALL).findall(link)

    link = getHttpData(listapi % match0[0])
    jsdata = simplejson.loads(link)['videos']

    for item in jsdata:
        p_name = item['subName'].encode('utf-8')
        p_thumb = item['largePicUrl'].encode('utf-8')
        p_url = item['pageUrl'].encode('utf-8')
        length = item['playLength']
        p_date = item['publishTime'].encode('utf-8')
        p_order = int(item['order'])
        vid = item['vid']
        li = xbmcgui.ListItem(p_name, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url)
        u += '&mode=playvideo&name=' + name
        u += '&title=' + urllib.quote_plus(p_name)
        u += '&thumb=' + urllib.quote_plus(p_thumb)
        u += '&vid=%d' % vid
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Menu List
############################################################################
def LiveChannel(params):
    url = params['url']
    name = params['name']
    link = getHttpData(url)
    link = link[link.find('=')+1: link.find(';channelList')]

    jsdata = simplejson.loads(link)
    stations = jsdata['STATIONS']

    for item in stations:
        title = item['STATION_NAME'].encode('utf-8')
        p_thumb = item['STATION_PIC']
        id = item['STATION_ID']
        p_thumb = httphead(p_thumb)
        if item['IsSohuSource'] == 1:
            disp_title = INDENT_FMT0 % title
        else:
            disp_title = INDENT_FMT1 % title
        u = sys.argv[0] + '?mode=liveplay&id=%d' % id
        u += '&name=' + name + '&title=' + title

        u += '&thumb=' + urllib.quote_plus(p_thumb)
        html = getHttpData(PROGRAM_URL % id)

        schedule = ''
        try:
            program = simplejson.loads(html)
        except:
            continue
        try:
            program = program['attachment'][0]['MENU_LIST']
        except:
            continue
        for s in program:
            schedule += '%s   %s\n' % (s['START_TIME'], s['NAME'])
        li = xbmcgui.ListItem(disp_title,
                              iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type='Video', infoLabels={'Title': disp_title, 'Plot': schedule})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Player
############################################################################
def LivePlay(params):
    id = params['id']
    channel = params['title']
    thumb = params['thumb']
    link = getHttpData(LIVEID_URL % id)
    parsed_json = simplejson.loads(link.decode('utf-8'))
    url = httphead(parsed_json['data']['hls'].encode('utf-8'))

    # link = getHttpData(url)
    # parsed_json = simplejson.loads(link.decode('utf-8'))
    # url = parsed_json['url'].encode('utf-8')
    li = xbmcgui.ListItem(channel, iconImage='', thumbnailImage=thumb)
    xbmc.Player().play(url, li)


###########################################################################
# Get user input for Sohu site search
############################################################################
def searchSohu(params):
    keyboard = Apps('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    p_url = 'http://so.tv.sohu.com/mts?chl=&tvType=-2&wd='
    url = p_url + urllib.quote_plus(keyword)

    # construct url based on user selected item
    page = 1
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=%d' % page
    link = getHttpData(p_url)

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索:' + keyword + '[/COLOR]')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    #########################################################################
    # Video listing for all found related episode title
    tree = BeautifulSoup(link, 'html.parser')
    soup = tree.find_all('div', {'class': 'ssItem cfix'})

    #########################################################################
    for page in soup[0]:
        try:
            p_url = httphead(page.a['href'])
        except:
            continue
        p_name = page.a['title'].encode('utf-8')
        img = httphead(page.img['src'])
        infop = page.find('p', {'class': 'des'})
        try:
            info = infop.text
        except:
            info = ''
        li = xbmcgui.ListItem(p_name, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': p_name, 'Plot': info})
        u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url)
        u += '&mode=episodelist&title=' + urllib.quote_plus(p_name)
        u += '&thumb=' + urllib.quote_plus(img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
        album = page.find_all('a', {'class': 'ts'})
        for series in album:
            title = series['title']
            href = httphead(series['href'])
            li = xbmcgui.ListItem(title)
            u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
            u += '&mode=playvideo&title=' + urllib.quote_plus(title)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'livechannel': 'LiveChannel(params)',
    'liveplay': 'LivePlay(params)',
    'videolist': 'listSubMenu(params)',
    'episodelist1': 'episodesList1(params)',
    'episodelist2': 'episodesList2(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchSohu(params)',
    'select': 'normalSelect(params)'
}

eval(runlist[mode])
