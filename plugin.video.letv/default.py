# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import sys
import os
import gzip
import StringIO
import os.path
import time
import random
import socket
import cookielib
import base64
import simplejson
from bs4 import BeautifulSoup

########################################################################
# 乐视网(LeTv) by cmeng
########################################################################
# Version 1.5.9 2016-05-25 (cmeng)
# Implement all possible fixes to handle slow network response (starve network data)
# Add video server selection option
# Stop last video from repeating playback
# Improve user UI feedback on slow network data fetching actual status (background)

# See changelog.txt for previous history
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

HOST_URL = 'https://www.le.com'
LIST_URL = 'http://list.le.com'
ALBULM_URL = 'http://d.api.m.le.com/play/getAllVideoList?id=%s&platform=pc'
ALBULM_URL = 'http://d.api.m.le.com/card/dynamic?vid=%s&platform=pc'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'
RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}
VIDEO_LIST = ['电影', '电视剧', '动漫', '综艺']
UGC_LIST = ['体育', '娱乐', '音乐', '风尚', '纪录片',
            '财经', '汽车', '旅游', '亲子', '热点']

SERIES_LIST = ['电视剧', '动漫']
MOVIE_LIST = ['电影', '综艺']
COLOR_LIST = ['[COLOR FFFF0000]', '[COLOR FF00FF00]', '[COLOR FFFFFF00]', '[COLOR FF00FFFF]', '[COLOR FFFF00FF]']

FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'

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


##################################################################################
# LeTV Video Link Decode Algorithm
# Extract all the video list and start playing first found valid link
# http://www.letv.com/ptv/vplay/1967644.html
##################################################################################
def calcTimeKey(t):
    ror = lambda val, r_bits, : ((val & (2 ** 32 - 1)) >> r_bits % 32) | (val << (32 - (r_bits % 32)) & (2 ** 32 - 1))
    return ror(ror(t, 773625421 % 13) ^ 773625421, 773625421 % 17)


# # --- decrypt m3u8 data --------- ##
def m3u8decode(data):
    version = data[0:5]
    if version.lower() == b'vc_01':
        # get real m3u8
        loc2 = bytearray(data[5:])
        length = len(loc2)
        loc4 = [0] * (2 * length)
        for i in range(length):
            loc4[2 * i] = loc2[i] >> 4
            loc4[2 * i + 1] = loc2[i] & 15
        loc6 = loc4[len(loc4) - 11:] + loc4[:len(loc4) - 11]
        loc7 = [0] * length
        for i in range(length):
            loc7[i] = (loc6[2 * i] << 4) + loc6[2 * i + 1]
        return ''.join([chr(i) for i in loc7])
    else:
        # directly return
        return data


#  ------ video links decrypt ---------------------- ##
def decrypt_url(url, mCheck=True):
    videoRes = int(__addon__.getSetting('video_resolution'))
    serverIndex = int(__addon__.getSetting('video_server')) - 1
    vparamap = {0: '1300', 1: '720p', 2: '1080p'}

    t_url = 'http://api.letv.com/mms/out/video/playJson?id={}&platid=1&splatid=101&format=1&tkey={}&domain=www.letv.com'
    t_url2 = '&ctv=pc&m3v=1&termid=1&format=1&hwtype=un&ostype=Linux&tag=letv&sign=letv&expect=3&tn={}&pay=0&iscpn=f9051&rateid={}'

    try:
        vid = re.compile('/vplay/(\d+).html').findall(url)[0]
        j_url = t_url.format(vid, calcTimeKey(int(time.time())))
        link = getHttpData(j_url)
        info = simplejson.loads(link)
        playurl = info['playurl']
    except:
        return ''

    if (mCheck):
        pDialog.update(30)
    stream_id = None
    support_stream_id = info["playurl"]["dispatch"].keys()
#     print("Current Video Supports:")
#     for i in support_stream_id:
#         print("\t--format",i,"<URL>")
    if "1080p" in support_stream_id:
        stream_id = '1080p'
    elif "720p" in support_stream_id:
        stream_id = '720p'
    else:
        stream_id = sorted(support_stream_id, key=lambda i: int(i[1:]))[-1]

    # pick a random domain or user selected to minimize overloading single server
    if (serverIndex == -1):
        index = random.randint(0, len(playurl['domain']) - 1)
    else:
        index = serverIndex % len(playurl['domain'])
    domain = playurl['domain'][index]
    # print "### Video Server Selection: %i %i = %s" % (serverIndex, index, playurl['domain'])

    vodRes = playurl['dispatch']
    vod = None
    while (vod is None) and (videoRes >= 0):
        vRes = vparamap.get(videoRes, 0)
        try:
            vod = vodRes.get(vRes)[0]
        except:
            pass
        videoRes -= 1
    if vod is None:
        try:
            vod = playurl['dispatch']['1000'][0]
        except KeyError:
            vod = playurl['dispatch']['350'][0]
        except:
            return ''

    url = domain + vod
    url += t_url2.format(random.random(), vRes)
    ext = vodRes[stream_id][1].split('.')[-1]

    r2 = getHttpData(url)
    if (mCheck):
        pDialog.update(60, line2="### 服务器  [ %i ]" % (index + 1))

    # try:
    info2 = simplejson.loads(r2)

    # need to decrypt m3u8 (encoded) - may hang here
    m3u8 = getHttpData(info2["location"], False, True)
    if (m3u8 is None):
        return None

    if (mCheck):
        pDialog.update(90)
    m3u8_list = m3u8decode(m3u8)
    with open(__m3u8__, "wb") as m3u8File:
        m3u8File.write(m3u8_list)
    m3u8File.close()

    # urls contains array of v_url video links for playback
    urls = re.findall(r'^[^#][^\r]*', m3u8_list, re.MULTILINE)
    return urls


############################################################################
def playVideoLetv(params):
    videom3u8 = __addon__.getSetting('video_m3u8')
    pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    pDialog.update(0)

    vid = params.get('vid')
    if vid:    # pack vid address (cheating)
        url = 'http://www.google.com/vplay/%s.html' % vid
    else:
        url = params['url']
    name = params['name']
    thumb = params['thumb']
    v_urls = decrypt_url(url)
    pDialog.close()

    if len(v_urls):
        if videom3u8 == 'true':
            listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
            listitem.setInfo(type="Video", infoLabels={"Title":name})
            xbmc.Player().play(__m3u8__, listitem)
        else:
            xplayer.play(name, thumb, v_urls)

            # need xmbc.sleep to make xbmc callback working properly
            while xplayer.is_active:
                xbmc.sleep(100)
            pDialog.close()
    else:
        # if '解析失败' in link: (license constraint etc)
        dialog.ok(__addonname__, '未匹配到视频文件')


##################################################################################
# Continuous Player start playback from user selected video
# User backspace to previous menu will not work - playlist = last selected
##################################################################################
def playVideoUgc(name, url, thumb):
    videom3u8 = __addon__.getSetting('video_m3u8')
    if videom3u8 == 'true':
        pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
        pDialog.update(0)
        v_urls = decrypt_url(url)
        pDialog.close()
        listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
        listitem.setInfo(type="Video", infoLabels={"Title": name})
        xbmc.Player().play(__m3u8__, listitem)
    else:
        xplayer.play(name, thumb)

        # need xmbc.sleep(100) to make xbmc callback working properly
        while xplayer.is_active:
            xbmc.sleep(100)
        pDialog.close()


##################################################################################
# Routine to fetech url site data using Mozilla browser
# - deletc '\r|\n|\t' for easy re.compile
# - do not delete ' ' i.e. <space> as some url include spaces
# - unicode with 'replace' option to avoid exception on some url
# - translate to utf8
##################################################################################
def getHttpData(url, binary=False, mCheck=False):
    print "getHttpData: " + url
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
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    # req.add_header('cookie', 'PHPSESSID=ruebtvftj69ervhpt24n1b86i3')

    for k in range(3):  # give 3 trails to fetch url data
        if (mCheck and pDialog.iscanceled()):  # exit if cancelled by user
            return None

        try:
            response = opener.open(req)
        except urllib2.HTTPError, e:
            httpdata = e.read()
        except urllib2.URLError, e:
            httpdata = "IO Timeout Error"
        except socket.timeout, e:
            httpdata = "IO Timeout Error"
        else:
            httpdata = response.read()
            response.close()
            # Retry if exception: {"exception":{....
            if not "exception" in httpdata:
                cj.save(cookieFile, ignore_discard=True, ignore_expires=True)
                # for cookie in cj:
                #     print('%s --> %s'%(cookie.name,cookie.value))
                break

    if (not binary):
        httpdata = re.sub('\r|\n|\t', '', httpdata)
        match = re.compile('<meta.+?charset=["]*(.+?)"').findall(httpdata)
        if len(match):
            charset = match[0].lower()
            if (charset != 'utf-8') and (charset != 'utf8'):
                httpdata = unicode(httpdata, charset, 'replace').encode('utf-8')

    return httpdata


def buildParams(params):
    str = ''
    for item in params:
            str += '&%s=' % item + urllib.quote_plus(params[item])
    return str



def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【乐视网 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = LIST_URL + '/listn/c2_t-1_a-1_y-1_s1_md_o51_d1_p.html'
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'channel_list'})

    grp = soup[0].find_all('a')
    for prog in grp:
        title = prog.text
        href = LIST_URL + prog['href']
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=%s&mode=videolist&name=%s' % (href, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    url = params['url']
    name = params.get('name')
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    #  sort mode
    soup = tree.find_all('div', {'class': 'sort_navy'})
    soup = soup[0].find_all('a')
    url = url
    li = xbmcgui.ListItem(BANNER_FMT % '排序方式')
    u = sys.argv[0] + '?url=' + url
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
    for grp in soup:
        title = grp.text
        order = grp['data-order']
        href = re.sub('md_o\d+', 'md_'+order, url)
        if order in url:
            title = INDENT_FMT1 % title
        else:
            title = INDENT_FMT0 % title
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href + '&mode=videolist'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    #  filter by types
    soup = tree.find_all('ul', {'class': 'label_list'})
    filter = soup[0].find_all('dl')

    title = u'[COLOR FFDEB887]分类过滤[/COLOR]|'
    for item in filter:
        typelist = item.h2.text.replace(' ', '')
        curr = item.find('b', {'class': 'curr'})
        try:
            type = curr.text
        except:
            type = ''
        title += typelist + '(' + type + ')' + '|'

    li = xbmcgui.ListItem(title)
    u = sys.argv[0] + '?url=' + url + '&mode=filter&name=' + urllib.quote_plus(name)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('dl', {'class': 'dl_list'})
    for prog in soup:
        img = prog.img['src']
        href = prog.a['href']
        title = prog.a['title']
        special = prog.i.text + '|' + prog.span.text

        li = xbmcgui.ListItem(title + '(' + special + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        if name in ['体育']:
            mode = 'sports'
        else:
            mode = 'episodelist'
        u = sys.argv[0] + '?url=' + href
        u += '&mode=' + mode + '&name=' + urllib.quote_plus(name)
        u += '&title=%s&thumb=%s' % (title, img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    page = re.compile('p(\d+?).html').findall(url)
    if len(page) < 1:
        page = ['1']
    page = int(page[0])
    if page > 1:
        title = BANNER_FMT % '上一页'
        aurl = re.sub('p\d*.html', 'p%d.html' % (page-1), url)
        u = sys.argv[0] + '?url=%s&mode=videolist' % aurl
        u += '&name=' + urllib.quote_plus(name)
        liz = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    if page < 200:
        title = BANNER_FMT % '下一页'
        aurl = re.sub('p\d*.html', 'p%d.html' % (page+1), url)
        u = sys.argv[0] + '?url=%s&mode=videolist' % aurl
        u += '&name=' + urllib.quote_plus(name)
        liz = xbmcgui.ListItem(title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    del(params['url'])
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'label_list'})

    filter = soup[0].find_all('dl')

    dialog = xbmcgui.Dialog()

    urlsplit = url.split('/')
    urltype = re.compile('\w{1}.+?_').findall(urlsplit[-1])
    marktype = []
    for item in filter:
        title = item.h2.text.replace(' ', '')
        si = item.find_all('a')
        sel = dialog.select(title, [x.text for x in si])

        if sel >= 0:
            selurl = si[sel]['href'].split('/')
            seltype = re.compile('\w{1}.+?_').findall(selurl[-1])
            for i in seltype:
                if i not in urltype:
                    marktype.append(i)

    u1 = urlsplit[-1]
    for type in marktype:
        u1 = re.sub(type[0] + '.+?_', type, u1)
    urlsplit[-1] = u1
    url = '/'.join(urlsplit)
    params['url'] = url


def educationSelect(params):
    url = params.get('url')
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'label_list first_condition'})

    title = soup[0].h2.text
    items = soup[0].find_all('a', {'class': 'j-tab'})
    list1 = [x.b.text for x in items]

    dialog = xbmcgui.Dialog()
    sel = dialog.select(title, list1)

    if sel < 0:
        return

    soup = tree.find_all('ul', {'class': 'label_list second_condition'})
    items = soup[0].find_all('li', {'class': 'list-body j_con%d' % sel})
    items = items[0].find_all('a')
    list2 = [x.b.text for x in items]
    href = [x['href'] for x in items]
    sel = dialog.select(list1[sel], list2)
    if sel >= 0:
        params['url'] = LIST_URL + href[sel]


def changeList(params):
    name = params['name']
    if name == '教育':
        educationSelect(params)
    else:
        normalSelect(params)
    listSubMenu(params)


def album2series(url):
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'list active'})
    return soup[0].a['href']


def episodesList(params):
    url = params['url']
    name = params['name']
    if name in ['电视剧', '自制']:
        url = album2series(url)

    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    print '============================', html

    match = re.compile("video: {0,}{.+?vid': {0,}'(\d+)'").findall(html)
    if len(match) < 1:
        match = re.compile('video: {0,}{.+?vid: {0,}"(\d+)"').findall(html)
    if len(match) < 1:
        match = re.compile('video: {0,}{.+?vid: {0,}(\d+)').findall(html)
        match[0] = str(match[0])

    print match[0]
    html = getHttpData(ALBULM_URL % (match[0]))
    jsdata = simplejson.loads(html)

    album = jsdata['data']['episode']['videolist']
    for series in album:
        title = series['title']
        pic = series['pic']
        info = series['subTitle']
        vid = series['vid']
        li = xbmcgui.ListItem(title, iconImage=pic, thumbnailImage=pic)
        li.setInfo(type='Video',
                   infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + url + '&vid=%d' % vid
        u += '&mode=playvideo&name=%s&thumb=%s' % (title, pic)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    try:
        album = jsdata['data']['otherlist']['videolist']
    except:
        album = []
    if len(album) > 0:
        for series in album:
            title = series['title']
            pic = series['pic']
            info = series['subTitle']
            vid = series['vid']
            li = xbmcgui.ListItem(title, iconImage=pic, thumbnailImage=pic)
            li.setInfo(type='Video',
                       infoLabels={'Title': title, 'Plot': info})
            u = sys.argv[0] + '?url=' + url + '&vid=%d' % vid
            u += '&mode=playvideo&name=%s&thumb=%s' % (title, pic)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    try:
        album = jsdata['data']['periodpoint']
    except:
        album = []
    if len(album) > 0:
        for series in album:
            title = series['title']
            pic = series['pic']
            info = series['subTitle']
            vid = series['vid']
            li = xbmcgui.ListItem(title, iconImage=pic, thumbnailImage=pic)
            li.setInfo(type='Video',
                       infoLabels={'Title': title, 'Plot': info})
            u = sys.argv[0] + '?url=' + url + '&vid=%d' % vid
            u += '&mode=playvideo&name=%s&thumb=%s' % (title, pic)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    '''
    match = re.compile("pageid: 'www_play'").search(html)
    if match is not None:    # play movie
        playVideoLetv(params)
        return

    soup = tree.find_all('div', {'class': 'list active'})
    for list in soup:
        part = list.find_all('dl')
        for item in part:
            img = item.img.get('data-src')
            if not img:
                img = item.img.get('src')

            info = item.find('p', {'class', 'p1'})
            href = info.a['href']
            title = info.a.text
            info = item.find('p', {'class', 'p2'})
            try:
                info = info.text
            except:
                info = ''
            li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            li.setInfo(type='Video',
                       infoLabels={'Title': title, 'Plot': info})
            u = sys.argv[0] + '?url=' + href
            u += '&mode=playvideo&name=%s&thumb=%s' % (title, img)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    '''
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def sportsList(params):
    url = params['url']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    match = re.compile("pageid: 'www_play'").search(html)
    if match is not None:    # play movie
        playVideoLetv(params)
        return

    soup = tree.find_all('li', {'class': 'video-item'})
    for list in soup:
        vid = list['data-id']
        img = list.img['data-original']
        title = list.p['title']
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?vid=' + vid
        u += '&mode=playvideo&name=%s&thumb=%s' % (title, img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


##################################################################################
# Routine to search LeTV site based on user given keyword for:
##################################################################################
def searchLeTV():
    result = ''

    keyboard = Apps('', '请输入搜索内容')
    # keyboard.setHiddenInput(hidden)
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        letvSearchList(keyword, '1')
    else:
        return

    p_url = 'http://so.le.com/s?hl=1&dt=2&ph=420001&from=pcjs&ps=30&wd=%s'
    p_url = p_url % (urllib.quote(name))
    link = getHttpData(p_url)

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索: 第' + page + '页[/COLOR][COLOR FFFFFF00] (' + name + ')[/COLOR]【[COLOR FF00FF00]' + '点此输入新搜索内容' + '[/COLOR]】')
    u = sys.argv[0] + "?mode=31&name=" + urllib.quote_plus(name) + "&page=" + page
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if link is None:
        li = xbmcgui.ListItem('  抱歉，没有找到[COLOR FFFF0000] ' + name + ' [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    # fetch and build the video series episode list
    content = simplejson.loads(link)
    vlist = content['data_list']
    totalItems = len(vlist)
    for i in range(0, totalItems):
        vid = str(vlist[i]['vid'])
        v_url = 'http://www.letv.com/ptv/vplay/%s.html' % vid
        p_title = vlist[i]['name'].encode('utf-8')

        try:
            p_thumb = vlist[i]['images']['150*200']
        except KeyError:
            p_thumb = vlist[i]['images']['160*120']
        except:
            pass

        p_categoryName = vlist[i]['categoryName']
        if (p_categoryName != None):
            p_list = p_name = str(i + 1) + '. [COLOR FF00FFFF][' + p_categoryName.encode('utf-8') + '][/COLOR] ' + p_title + ' '
        else:
            p_list = p_name = str(i + 1) + '. ' + p_title + ' '

        try:
            p_rating = float(vlist[i]['rating'])
            if (p_rating != None and p_rating > 0.01):
                p_rating = "%0.1f" % p_rating
                p_list += '[COLOR FFFF00FF][' + p_rating + '][/COLOR]'
        except:
            pass

        p_dx = int(vlist[i]['duration'])
        if (p_dx is not None):
            p_duration = "[%02d:%02d]" % (int(p_dx / 60), (p_dx % 60))
            p_list += '[COLOR FFFFFF00]' + p_duration + '[/COLOR]'

        p_artists = vlist[i]['actor']
        if ((p_artists is not None) and len(p_artists)):
            p_artist = ""
            p_list += '['
            for key in p_artists:
                p_artist += p_artists[key].encode('utf-8') + ' '
            p_list += p_artist[:-1] + ']'

        li = xbmcgui.ListItem(p_list, iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + "?mode=10" + "&name=" + urllib.quote_plus(p_list) + "&url=" + urllib.quote_plus(v_url) + "&thumb=" + urllib.quote_plus(p_thumb)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False, totalItems)

    # Fetch and build page selection menu
    p_itemCount = content['video_count']
    pages = getPages(p_itemCount, page)

    for page in pages:
        li = xbmcgui.ListItem("... 第" + str(page) + "页")
        u = sys.argv[0] + "?mode=32" + "&name=" + urllib.quote_plus(name) + "&page=" + str(page)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


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
    'videolist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'sports': 'sportsList(params)',
    'playvideo': 'playVideoLetv(params)',
    'search': 'searchLeTV(params)',
    'filter': 'changeList(params)'
}

eval(runlist[mode])
