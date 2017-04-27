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
import cookielib
import simplejson
from bs4 import BeautifulSoup
from youku import getaddress_by_vid
from youku import get_content as getHttpData

########################################################################
# 土豆 www.tudou.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8')).decode("utf-8")
cookieFile = __profile__ + 'cookies.tudou'

if (__addon__.getSetting('keyboard')=='0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
#UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

HOST_URL = 'http://www.tudou.com'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
TIMER_FMT = '[COLOR FF8040C0](%s)[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]      %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]      %s[/COLOR]'
CFRAGMAX = [10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500]


###########################################################################
# LeTv player class
###########################################################################
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
            self.listitem.setInfo(type="Video", infoLabels={"Title": self.title})

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
                bfile = getHttpData(v_url,
                                    headers={'User-Agent': UserAgent},
                                    decoded=True,
                                    binary=True
                                   )
                # give another trial if playback is active and bfile is invalid
                if ((len(bfile) < 30) and self.isPlayingVideo()):
                    bfile = getHttpData(v_url,
                                        headers={'User-Agent': UserAgent},
                                        decoded=True,
                                        binary=True
                                       )
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
def PlayVideo(params):
    title = params.get('title', '')
    thumb = params.get('thumb')
    level = int(__addon__.getSetting('resolution'))

    vcode = params.get('vcode')
    iid = params.get('iid')

    print '------{}---{}-----'.format(vcode, iid)
    if vcode and vcode[-2:] == '==':
        urls = getaddress_by_vid(vcode, stream_id=level)
        print urls
        ulen = len(urls)
        if ulen > 0:
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            for i in range(ulen):
                name = title + '(%d/%d)' % (i + 1, ulen)
                listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
                listitem.setInfo(type="Video", infoLabels={"Title": name})
                playlist.add(urls[i], listitem)

            xbmc.Player().play(playlist)
    elif iid:
        urls = tudou_download_by_iid(iid)
        ulen = len(urls)
        if ulen > 0:
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            for i in range(ulen):
                name = title + '(%d/%d)' % (i + 1, ulen)
                listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
                listitem.setInfo(type="Video", infoLabels={"Title": name})
                playlist.add(urls[i], listitem)

            xbmc.Player().play(playlist)
        pass
        pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
        urls = tudou_download_by_iid(iid)
        pDialog.close()
        if len(urls) > 0:
            xplayer.play(title, thumb, urls)

            # need xmbc.sleep to make xbmc callback working properly
            while xplayer.is_active:
                xbmc.sleep(100)
    else:
        xbmcgui.Dialog().ok(__addonname__, '未匹配到VID')
        return


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


def tudou_download_by_iid(iid):
    url = 'http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s'
    html = getHttpData(url % iid, headers={'User-Agent': UserAgent})
    data = simplejson.loads(html)

    key = data.keys()
    print '==================',key,iid
    temp = data[key[0]]

    vids = [t['k'] for t in temp]
    urls = []
    for vid in vids:
        html = getHttpData('http://cnc.v2.tudou.com/f?id=%d&jp=1' % vid,
                           headers={'User-Agent': UserAgent})
        y = re.compile('<f.+?>(http.+?)<\/f>').findall(html)
        if len(y) < 1:
            break
        y = y[0].replace('&amp;', '&')
        urls.append(y.strip())
    print urls
    return urls


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def tudou_download_by_id(id):
    html = getHttpData('http://www.tudou.com/programs/view/%s/' % id,
                       headers={'User-Agent': UserAgent})

    iid = r1(r'iid\s*[:=]\s*(\S+)', html)
    tudou_download_by_iid(iid)


def buildParams(params):
    str = ''
    for item in params:
        str += '&%s=' % item + urllib.quote_plus(params[item])
    return str


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【土豆视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    url = HOST_URL + '/list/index_list.html'

    html = getHttpData(url, headers={'User-Agent': UserAgent})
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('ul', {'class': 'menu'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        title = prog.text
        href = prog.a['href']
        href = httphead(href)
        nametype = href.split('/')[-1][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        elif nametype == 'ich':
            mode = 'videolist2'

        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=%s&mode=%s&name=%s' % (href, mode, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def findTags(string):
    group = re.compile('(a|b|c|d|e|f|g|h|i|j|k|l|m|n)(\d+)').findall(string)
    return dict(group)


def mergeTags(tags):
    str = ''
    for x in tags:
        str += '&tags=' + tags[x]
    return str


def listSubMenu1(params):
    # http://www.tudou.com/list/ach3a-2b-2c-2d-2e-2f1003g-2h-2i-2j-2k-2l-2m-2n1sort2.html
    # http://www.tudou.com/list/ach3a42b55c324d-2e-2f1003g-2h-2i-2j-2k-2l-2m-2n-2sort2.html
    # a42:地区
    # b55:类型
    # c324:状态
    # dxx:年代
    # exxx:付费
    # f1002:清晰度
    # &tags=&tags=....
    # sort1:最新 sort2: 人气
    name = params['name']
    url = params['url']
    filter = params.get('filter', '')
    urlpage = getHttpData(url, headers={'User-Agent': UserAgent})
    page = params.get('pageNo', '1')
    piece = url.split('/')[-1]
    tagId = re.compile('ch(\d+)').findall(piece)[0]
    tags = findTags(piece)

    if tags.get('n'):
        AtoZ = chr(int(tags['n']) + 64)
        del(tags['n'])
    else:
        AtoZ = ''

    params = {'name': name,
              'pageSize': '30',
              'app': 'mainsitepc',
              'deviceType': '1',
              'tagType': '3',
              'firstTagId': tagId,
              'areaCode': '',
              'initials': AtoZ,        # 首字母  nXXsort2
              'hotSingerId': '',
              'pageNo': page
             }
             # 'tags': '',            # 地区类型...清晰度  , etc.
    strparam = buildParams(params)
    strparam = '?' + strparam[1:] + mergeTags(tags)

    list_api = 'http://www.tudou.com/s3portal/service/pianku/data.action'
    html = getHttpData(list_api + strparam, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(html)
    items = jsdata['items']
    total = jsdata['total']

    li = xbmcgui.ListItem(BANNER_FMT % (name+'(第%s页|分类过滤)' % page + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    tree = BeautifulSoup(urlpage, 'html.parser')
    soup = tree.find_all('select', {'id': 'selectOps'})
    field = soup[0].find_all('option')
    link = re.compile('var CONFIG.+?urls:(.+])').findall(urlpage)
    link = eval(link[0])
    for i in range(len(field)):
        title = field[i].text
        if field[i].has_attr('selected'):
            li = xbmcgui.ListItem(INDENT_FMT0 % title)
            currentPage = link[i]
        else:
            li = xbmcgui.ListItem(INDENT_FMT1 % title)

        href = HOST_URL + '/list/' + link[i]
        nametype = link[i][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        else:
            mode = 'videolist2'

        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=' + mode + '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    for item in items:
        title = item['title']
        href = item['playUrl']
        info = item['albumShortDesc']
        img = item['picUrl_200x112']
        pay = item['needMoney']
        info = item['updateInfo']
        if pay is True:
            info += '|付费'.decode('utf-8')
        albumId = item['albumId']
        aid = item['aid']
        li = xbmcgui.ListItem(title + TIMER_FMT % info,
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href
        u += '&mode=albumlist&albumId=%d' % albumId
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(img)
        u += '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if currentPage[:3] == 'ach':
        mode = 'videolist1'
    else:
        mode = 'videolist2'
    if int(page) > 1:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist1&pageNo=%d' % (int(page)-1)
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if int(page) <= total // 30:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist1&pageNo=%d' % (int(page)+1)
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu2(params):
    name = params['name']
    url = params['url']
    filter = params.get('filter', '')
    urlpage = getHttpData(url, headers={'User-Agent': UserAgent})
    page = params.get('page', '1')
    piece = url.split('/')[-1]
    tagId = re.compile('ch(\d+)').findall(piece)[0]
    tags = findTags(piece)

    if tags.get('n'):
        AtoZ = chr(int(tags['n']) + 64)
        del(tags['n'])
    else:
        AtoZ = ''

    params = {'name': name,
              'pageSize': '30',
              'sort': '2',
              'tagType': '1',
              'firstTagId': tagId,
              'areaCode': '',
              'initials': AtoZ,        # 首字母  2n2sort2
              'hotSingerId': '',
              'page': page
             }
             #  'tags': '',            # 地区类型...清晰度  , etc.
    strparam = buildParams(params)
    strparam = '?' + strparam[1:] + mergeTags(tags)

    list_api = 'http://www.tudou.com/list/itemData.action'
    html = getHttpData(list_api + strparam, headers={'User-Agent': UserAgent})

    li = xbmcgui.ListItem(BANNER_FMT % (name+'(第%s页|分类过滤)' % page + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    tree = BeautifulSoup(urlpage, 'html.parser')
    soup = tree.find_all('select', {'id': 'selectOps'})
    field = soup[0].find_all('option')
    link = re.compile('var CONFIG.+?urls:(.+])').findall(urlpage)
    link = eval(link[0])
    for i in range(len(field)):
        title = field[i].text
        if field[i].has_attr('selected'):
            li = xbmcgui.ListItem(INDENT_FMT0 % title)
            currentPage = link[i]
        else:
            li = xbmcgui.ListItem(INDENT_FMT1 % title)

        href = HOST_URL + '/list/' + link[i]
        nametype = link[i][:3]
        if nametype == 'ach':
            mode = 'videolist1'
        else:
            mode = 'videolist2'
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=%s&title=%s' % (mode, title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    jsdata = simplejson.loads(html)
    items = jsdata['data']

    for item in items:
        title = item['title']
        iid = item['itemId']
        img = item['bigPicUrl']
        time = item['totalTimeStr']
        href = HOST_URL + '/programs/view/%s/' % item['code']
        li = xbmcgui.ListItem(title + TIMER_FMT % time,
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=albumlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + img + '&url=' + href
        u += '&title=' + title
        u += '&iid=%d' % (iid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if currentPage[:3] == 'ach':
        mode = 'videolist1'
    else:
        mode = 'videolist2'
    if int(page) > 1:
        li = xbmcgui.ListItem(BANNER_FMT % '上一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist2&page=%d' % (int(page)-1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if int(page) <= 2000:
        li = xbmcgui.ListItem(BANNER_FMT % '下一页')
        u = sys.argv[0] + '?url=' + url
        u += '&mode=videolist2&page=%d' % (int(page)+1)
        u += '&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    name = params.get('name')
    surl = url.split('/')
    purl = surl[-1]
    if len(purl) < 10:
        purl = purl[:-5] + 'a-2b-2c-2d-2e-2f-2g-2h-2i-2j-2k-2l-2m-2n-2sort2.html'
    filter = params.get('filter', '')

    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'category_item fix'})

    dialog = xbmcgui.Dialog()
    color = '[COLOR FF00FF00]%s[/COLOR]'
    for iclass in soup:
        si = iclass.find_all('li')
        list = []
        i = 0
        for subitem in si:
            title = subitem.text
            if subitem.get('class'):
                title = color % title
                mark = i
            list.append(title)
            i += 1
        sel = dialog.select(iclass.h3.text, list)

        if sel < 0:
            continue
        filter += '|' + iclass.h3.text + '(' + si[sel].text + ')'
        if sel == mark:
            continue

        seurl = si[sel].a['href'].split('/')[-1]
        p = re.compile('(a|b|c|d|e|f|g|h|i|j|k|l|m|n)(\d+)').findall(seurl[3:])
        for x in p:
            purl = re.sub(x[0] + '\d+', x[0] + x[1], purl)
            purl = re.sub(x[0] + '\-2', x[0] + x[1], purl)

    surl[-1] = purl
    params['url'] = '/'.join(surl)
    params['filter'] = filter.encode('utf-8')

    if purl[0] == 'a':
        listSubMenu1(params)
    else:
        listSubMenu2(params)


def relatedAlbumList(params):
    aid = params.get('albumId')
    title = params.get('title')
    img = params.get('thumb', '')
    url = params.get('url')
    if url:
        html = getHttpData(url, headers={'User-Agent': UserAgent})
        iid = re.compile('iid: (\d+)').findall(html)
        vcode = re.compile('youkuCode: "(.+?)"').findall(html)
        u = sys.argv[0] + '?mode=playvideo&iid=%s&vcode=%s' % (iid[0], vcode[0])
        u += '&title=' + urllib.quote_plus(title)
        u += '&thumb=' + img

    else:
        u = sys.argv[0] + '?mode=albumlist&albumId=%s' % aid
        u += '&title=' + title + '&thumb=' + img

    li = xbmcgui.ListItem(BANNER_FMT % title,
                          iconImage=img, thumbnailImage=img)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    album_api = 'http://www.tudou.com/crp/alist.action?a=%s'
    jspage = getHttpData(album_api % aid,
                         headers={'User-Agent': UserAgent},
                         decoded=False)

    jsdata = simplejson.loads(jspage)
    jsdata = jsdata['items']

    for item in jsdata:
        title = item['kw']
        info = item.get('comments')
        time = item['time']
        img = item['pic']
        vcode = item['vcode']
        iid = item['iid']
        u = sys.argv[0] + '?mode=playvideo'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&thumb=' + img
        u += '&vcode=%s&iid=%d' % (vcode, iid)
        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    rel_list = 'http://www.tudou.com/crp/getRelativeContent.action?a=%s'

    jspage = getHttpData(rel_list % aid, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(jspage)
    headings = jsdata['data']['catList']
    heading = [x['name'] for x in headings]
    title = '|'.join(heading).encode('utf-8')

    u = sys.argv[0] + '?mode=albumlist&albumId=%s' % aid
    u += '&title=' + urllib.quote_plus(title)
    li = xbmcgui.ListItem(BANNER_FMT % title)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    items = jsdata['data']['playAlbumInfoList']
    for item in items:
        aid = item['albumId']
        img = item['albumPicUrl']
        title = item['albumName']
        extra = item['update']
        info = item['albumShortDesc']
        li = xbmcgui.ListItem(title + '(' + extra + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=albumlist'
        u += '&title=%s&albumId=%d' % (title, aid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def relatedPlayList(params):
    url = params.get('url')
    title = params.get('title')
    img = params.get('thumb')
    iid = [params.get('iid')]
    if url:
        html = getHttpData(url, headers={'User-Agent': UserAgent})
        iid = re.compile('iid: (\d+)').findall(html)
        vcode = re.compile('youkuCode: "(.+?)"').findall(html)

        u = sys.argv[0] + '?mode=playvideo&thumb=' + img
        if iid:
            u += '&iid=' + iid[0]
        if vcode:
            u += '&vcode=' + vcode[0]
        u += '&title=' + urllib.quote_plus(title)
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    rel_list = 'http://www.tudou.com/crp/getRelatedPlaylists.action?iid=%s'

    jspage = getHttpData(rel_list % iid[0], headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(jspage)
    items = jsdata['data']['pList']

    u = sys.argv[0] + '?mode=codelist&iid=%s' % iid[0]
    u += '&title=' + '相关视频'.decode('utf-8')
    li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in items:
        title = item['name']
        img = item['picUrl']
        info = item['description']
        code = item['code']
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=codelist'
        u += '&title=%s&code=%s' % (title, code)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    code = items[0]['code']

    rel_list = 'http://www.tudou.com/crp/plist.action?lcode=%s'

    jspage = getHttpData(rel_list % code, headers={'User-Agent': UserAgent})
    jsdata = simplejson.loads(jspage)
    items = jsdata['items']

    u = sys.argv[0] + '?mode=codelist&iid=%s' % iid
    u += '&title=' + '主题视频'.decode('utf-8')
    li = xbmcgui.ListItem(BANNER_FMT % '主题视频')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in items:
        title = item['kw']
        img = item['pic']
        time = item['time']
        iid = item['iid']
        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playvideo'
        u += '&title=%s&thumb=%s&iid=%d' % (title, img, iid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def albumList(params):
    aid = params.get('albumId')
    title = params.get('title', '')
    img = params.get('thumb', '')
    iid = params.get('iid')

    if aid:
        relatedAlbumList(params)
    elif iid:
        relatedPlayList(params)


def searchInTudou(params):
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


# main programs goes here #########################################
xplayer = LetvPlayer()
pDialog = xbmcgui.DialogProgress()
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')
if mode is not None:
    del(params['mode'])

runlist = {
    None: 'mainMenu()',
    'videolist1': 'listSubMenu1(params)',
    'videolist2': 'listSubMenu2(params)',
    'albumlist': 'albumList(params)',
    'codelist': 'relatedPlayList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchInTudou(params)',
    'select': 'normalSelect(params)'
}

eval(runlist[mode])
