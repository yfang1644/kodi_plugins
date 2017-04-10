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
import datetime
import time
from random import random
import cookielib
import simplejson
from bs4 import BeautifulSoup

########################################################################
# 搜狐视频 tv.sohu.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8')).decode("utf-8")
cookieFile = __profile__ + 'cookies.letv'

if (__addon__.getSetting('keyboard')=='0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'
HOST_URL = 'http://tv.sohu.com'
LIST_URL = 'http://so.tv.sohu.com'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'
RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}

CFRAGMAX = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500]


##################################################################################
# LeTv player class
##################################################################################
class LetvPlayer(xbmc.Player):
    def __init__(self):
        xbmc.Player.__init__(self)

    def play(self, name, thumb, v_urls=None):
        self.name = name
        self.thumb = thumb
        self.v_urls_size = 0
        self.curpos = 0
        self.is_active = True
        self.load_url_sync = False
        self.xbmc_player_stop = False
        self.title = name
        self.mCheck = True
        self.LOVS = 0

        self.v_urls = v_urls
        if (v_urls):    # single video file playback
            self.curpos = int(__addon__.getSetting('video_fragmentstart')) * 10
            self.v_urls_size = len(v_urls)
        else:    # ugc playlist playback
            self.curpos = int(name.split('.')[0]) - 1
            # Get the number of video items in PlayList for ugc playback
            self.playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            self.psize = self.playlist.size()

        self.videoplaycont = __addon__.getSetting('video_vplaycont')
        self.maxfp = CFRAGMAX[int(__addon__.getSetting('video_cfragmentmax'))]

        # Start filling first buffer video and start playback
        self.geturl()

    def geturl(self):
        if (self.v_urls and (self.curpos < self.v_urls_size)):
            # Use double buffering for smooth playback
            x = (self.curpos / self.maxfp) % 2
            self.videourl = __profile__ + 'vfile-' + str(x) + '.ts'
            fs = open(self.videourl, 'wb')

            endIndex = min((self.curpos + self.maxfp), self.v_urls_size)
            self.title = "%s - 第(%s~%s)/%s节" % (self.name, str(self.curpos+1), str(endIndex), str(self.v_urls_size))
            # print "### Preparing: " + self.title
            self.listitem = xbmcgui.ListItem(self.title, thumbnailImage=self.thumb)
            self.listitem.setInfo(type="Video", infoLabels={"Title":self.title})

            for i in range(self.curpos, endIndex):
                # Stop further video loading and terminate if user stop playback
                if (self.xbmc_player_stop or pDialog.iscanceled()):
                    self.videourl = None
                    i = self.v_urls_size
                    break

                if (not self.isPlayingVideo()):
                    pDialog.create('视频缓冲', '请稍候。下载视频文件 ....')
                    pDialog.update(((i - self.curpos) * 100 / self.maxfp), line2="### " + self.title)
                else:
                    pDialog.close()

                v_url = self.v_urls[i]
                bfile = getHttpData(v_url, True, True)
                # give another trial if playback is active and bfile is invalid
                if ((len(bfile) < 30) and self.isPlayingVideo()):
                    bfile = getHttpData(v_url, True, True)
                fs.write(bfile)

                # Start playback after fetching 4th video files, restart every 4 fetches if playback aborted unless stop by user
                if (not self.isPlayingVideo() and (i < self.v_urls_size) and (((i - self.curpos) % 4) == 3)):
                    pDialog.close()
                    # Must stop sync loading to avoid overwritten current video when onPlayerStarted
                    self.load_url_sync = False
                    xbmc.Player.play(self, self.videourl, self.listitem)
                    # give some time to xmbc to upate its player status before continue
                    xbmc.sleep(100)
                    # Only reset fragment start after successful playback
                    __addon__.setSetting('video_fragmentstart', '0')

            fs.close()
            # print "### Last video file download fragment: " + str(i)
            # set self.curpos to the next loading video index
            self.curpos = i + 1

            # Last of video segment loaded, enable play once only
            if (self.curpos == self.v_urls_size):
                self.LOVS = 1
            else:    # reset
                self.LOVS = 0

            # Start next video segment loading if sync loading not enable
            if (not self.load_url_sync and (self.curpos < self.v_urls_size)):
                # Reset to sync loading on subsequent video segment
                self.load_url_sync = True
                self.playrun()

        # ugc auto playback
        elif ((self.v_urls is None) and (self.curpos < self.psize)):
            if (self.mCheck and not self.isPlayingVideo()):
                pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')

            # find next not play item in ugc playlist
            for idx in range(self.curpos, self.psize):
                p_item = self.playlist.__getitem__(idx)
                p_url = p_item.getfilename(idx)
                # p_url auto replaced with self.videourl by xbmc after played. To refresh, back and re-enter
                if "http:" in p_url:
                    p_list = p_item.getdescription(idx)
                    self.listitem = p_item  # pass all li items including the embedded thumb image
                    self.listitem.setInfo(type="Video", infoLabels={"Title":p_list})
                    self.curpos = idx
                    break

            x = self.curpos % 2
            self.videourl = __profile__ + 'vfile-' + str(x) + '.ts'
            fs = open(self.videourl, 'wb')

            v_urls = decrypt_url(p_url, self.mCheck)
            self.v_urls_size = len(v_urls)
            self.title = "UGC list @ %s (size = %s): %s" % (str(self.curpos), str(self.v_urls_size), p_list)
            # print "### Preparing: " + self.title

            for i, v_url in enumerate(v_urls):
                if (self.xbmc_player_stop or pDialog.iscanceled()):
                    self.videourl = None
                    i = self.v_urls_size
                    break

                if (not self.isPlayingVideo()):
                    pDialog.create('视频缓冲', '请稍候。下载视频文件 ....')
                    pDialog.update((i * 100 / self.v_urls_size), line2=self.title)
                else:
                    pDialog.close()

                bfile = getHttpData(v_url, True, True)
                fs.write(bfile)

                # Start playback after fetching 4th video files, restart every 4 fetches if playback aborted unless stop by user
                if (not self.isPlayingVideo() and (i < self.v_urls_size) and ((i % 4) == 3)):
                    pDialog.close()
                    # Must stop sync loading to avoid overwritten current video when onPlayerStarted
                    self.load_url_sync = False
                    xbmc.Player.play(self, self.videourl, self.listitem)
                    # give some time to xmbc to upate its player status before continue
                    xbmc.sleep(100)
            fs.close()
            # print "### Last video file download total fragment: %s ==> %s" % (str(i), self.title)
            # set self.curpos to the next loading ugc index
            self.curpos += 1

            # Last of video segment loaded, enable play once only
            if (self.curpos == self.psize):
                self.LOVS = 1
            else:    # reset
                self.LOVS = 0

            # Start next video segment loading if sync loading not enable
            if (not self.load_url_sync and (self.curpos < self.psize)):
                # Do not display dialog on subsequent UGC list loading
                self.mCheck = False

                # Reset to sync loading on subsequent ugc item
                self.load_url_sync = True
                self.playrun()

        # close dialog on all mode when fetching end
        pDialog.close()

    def playrun(self):
        if (self.videourl and not self.isPlayingVideo()):
            # print "### Player resume: %s \n### %s" % (self.title, self.videourl)
            pDialog.close()
            # Next video segment loading must wait until player started to avoid race condition
            self.load_url_sync = True
            xbmc.Player.play(self, self.videourl, self.listitem)
            xbmc.sleep(100)
        elif ((self.curpos < self.v_urls_size) or self.videoplaycont):
           # print "### Async fetch next video segment @ " + str(self.curpos)
           self.geturl()

    def onPlayBackStarted(self):
        # may display next title to playback due to async
        # print "### onPlayBackStarted Callback: " + self.title
        pDialog.close()
        if (self.load_url_sync):
            if ((self.curpos < self.v_urls_size) or self.videoplaycont):
                # print "### Sync fetch next video segment @ " + str(self.curpos)
                self.geturl()
        xbmc.Player.onPlayBackStarted(self)

    def onPlayBackSeek(self, time, seekOffset):
        # print "### Player seek forward: %s / %s" % (str(time), str(seekOffset))
        xbmc.Player.onPlayBackSeek(self, time, seekOffset)

    def onPlayBackSeekChapter(self, chapter):
        # no effect, valid on playlist playback by xmbc
        self.curpos += 1
        # print "### Player seek next chapter: " + str(self.curpos)
        xbmc.Player.onPlayBackSeek(self, chapter)

    def onPlayBackEnded(self):
        # Do not restart resume playback if video aborted due to starve network data
        if (self.videourl and self.load_url_sync):
        # if (self.videourl):
            # print "### onPlayBackEnded callback: Continue next video playback !!! " + str(self.LOVS)
            if (self.LOVS < 2):
                self.playrun()
            else:   # reset
                self.LOVS = 0
            # set flag to play last video segment once only
            if (self.LOVS == 1):
                self.LOVS += 1
        else:
            # print "### onPlayBackEnded callback: Ended-Deleted !!!"
            ## self.delTsFile(10)
            xbmc.Player.onPlayBackEnded(self)

    def onPlayBackStopped(self):
        # print "### onPlayBackStopped callback - Ending playback!!!"
        self.is_active = False
        self.xbmc_player_stop = True

    def delTsFile(self, end_index):
        for k in range(end_index):
            tsfile = __profile__ + 'vfile-' + str(k) + '.ts'
            if os.path.isfile(tsfile):
                try:
                    os.remove(tsfile)
                except:
                    pass


############################################################################
# Sohu Video Link Decode Algorithm & Player
# Extract all the video list and start playing first found valid link
# User may press <SPACE> bar to select video resolution for playback
############################################################################
def PlayVideo(params):
    name = params.get('name', '')
    url = params['url']
    thumb = params['thumb']
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


def httphead(url):
    http = url
    if len(url) < 2:
        return url
    if http[0:2] == '//':
        http = 'http:' + http
    elif http[0] == '/':
        http = LIST_URL + http

    return http


############################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
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

    name = '电视直播'
    li = xbmcgui.ListItem(name)
    u = sys.argv[0] + '?url=' + 'http://tvimg.tv.itc.cn/live/stations.jsonp'
    u += '&mode=livechannel&name=' + urllib.quote_plus(name)

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
    li = xbmcgui.ListItem(name+'【第%d页】(分类过滤)' % (page))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    hover = tree.find_all('div', {'class': 'list-hover'})
    thumb = tree.find_all('div', {'class': 'st-pic'})
    if len(thumb) == 0:
        thumb = tree.find_all('div', {'class': 'ret_pic'})

    for i in range(0, len(thumb)):
        href = thumb[i].a.get('href')
        href = httphead(href)
        img = thumb[i].img.get('src')
        img = httphead(img)
        try:
            title = hover[i].a.text
        except:
            title = thumb[i].img.get('alt')
        if len(title) == 0:
            title = thumb[i].a.get('title', '')
        try:
            info = hover[i].find('p', {'class': 'lh-info'}).text
        except:
            info = ''
        li = xbmcgui.ListItem(title,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        if name in ('电视剧', '动漫', '综艺', '纪录片', '教育'):
            mode = 'episodelist'
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


def episodesList(params):
    url = params['url']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    title = params.get('title', '')
    img = params.get('thumb', '')
    u = sys.argv[0]
    li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('ul', {'class': 'list listA cfix'})
    for part in soup:
        drama = part.find_all('li')
        for item in drama:
            img = httphead(item.img['src'])
            title = item.a['title']
            href = httphead(item.a['href'])
            li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            li.setInfo(type='Video', infoLabels={'Title': title})
            u = sys.argv[0] + '?url=' + href
            u += '&mode=playvideo&name=%s&thumb=%s' % (title, img)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Menu List
############################################################################
def LiveChannel(params):
    url = params['url']
    link = getHttpData(url)
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
            p_thumb == httphead(p_thumb)
            li = xbmcgui.ListItem(str(i) + '. ' + p_name,
                                  iconImage='', thumbnailImage=p_thumb)
            u = sys.argv[0] + '?id=' + id
            u += '&mode=liveplay&name=' + urllib.quote_plus(p_name)
            u += '&thumb=' + urllib.quote_plus(p_thumb)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


############################################################################
# Sohu 电视直播 Player
############################################################################
def LivePlay(params):
    id = params['id']
    name = params['name']
    thumb = params['thumb']
    link = getHttpData(LIVEID_URL % id)
    parsed_json = simplejson.loads(link.decode('utf-8'))
    url = 'http://' + parsed_json['data']['clipsURL'][0].encode('utf-8')
    link = getHttpData(url)
    parsed_json = simplejson.loads(link.decode('utf-8'))
    url = parsed_json['url'].encode('utf-8')
    li = xbmcgui.ListItem(name, iconImage='', thumbnailImage=thumb)
    xbmc.Player().play(url, li)


############################################################################
# Routine to search Sohu site based on user given keyword for:
# http://so.tv.sohu.com/mts?chl=&tvType=-2&wd=love&whole=1&m=1&box=1&c=100&o=1&p=2
# c: 类型：''=全部 100=电影 101=电视剧 106=综艺 121=音乐 122=新闻 112=娱乐 0=其它
# o:排序方式： ''=相关程度 1=最多播放 3=最新发布
############################################################################
def sohuSearchList(params):
    url = params['url']
    name = params.get('name', '')
    page = params['page']
    # construct url based on user selected item
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=' + page
    link = getHttpData(p_url)

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] (' + name + ')[/COLOR]【[COLOR FF00FF00]' + '请输入新搜索内容' + '[/COLOR]】')

    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=search&name=' + urllib.quote_plus(name) + '&page=' + urllib.quote_plus(page)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    #########################################################################
    # Video listing for all found related episode title
    tree = BeautifulSoup(link, 'html.parser')
    soup = tree.find_all('div', {'class': 'ssItem cfix'})
    
    #########################################################################
    matchp = re.compile('<div class="ssItem cfix">(.+?)<div class="alike">').findall(link)
    totalItems = len(matchp)
    for i in range(0, totalItems):
        vlink = matchp[i]
        if vlink.find('<em class="pay"></em>') > 0:
            continue

        match1 = re.compile('href="(.+?)"').findall(vlink)
        p_url = httphead(match1[0])

        match1 = re.compile('title="(.+?)"').search(vlink)
        p_name = match1.group(1)

        match1 = re.compile('src="(.+?)"').search(vlink)
        p_thumb = httphead(match1.group(1))

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
            mode = 'episodelist'
            p_type = '【[COLOR FF00FF00]电视剧[/COLOR]】'
        elif p_type == '电影':
            p_type = '【[COLOR FF00FF00]电影[/COLOR]】'
            mode = 'playvideo'
        else:
            p_type = ' ' + p_type
            mode = 'playvideo'

        p_list = str(i+1) + ': ' + p_name + p_type + p_label
        li = xbmcgui.ListItem(p_list, iconImage=p_thumb, thumbnailImage=p_thumb)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(p_url)
        u += '&mode=' + mode + '&name=' + urllib.quote_plus(p_name)
        u += '&id=101&thumb=' + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isTeleplay)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


###########################################################################
# Get user input for Sohu site search
############################################################################
def searchSohu(params):
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
        sohuSearchList(params)


# main programs goes here #########################################
xplayer = LetvPlayer()
mplaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
dialog = xbmcgui.Dialog()
pDialog = xbmcgui.DialogProgress()

params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')
if mode is not None:
    del(params['mode'])

runlist = {
    None: 'mainMenu()',
    'livechannel': 'LiveChannel(params)',
    'liveplay': 'LivePlay(params)',
    'videolist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchSohu(params)',
    'select': 'normalSelect(params)'
}

eval(runlist[mode])
