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
import cookielib
import simplejson
from bs4 import BeautifulSoup
from youku import getaddress_by_vid, get_vid_from_url
from youku import get_content as getHttpData

########################################################################
# 优酷 www.youku.com
########################################################################

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__addonicon__ = os.path.join(__addon__.getAddonInfo('path'), 'icon.png')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))

if (__addon__.getSetting('keyboard')=='0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
#UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

LIST_URL = 'http://list.youku.com'

BANNER_FMT = '[COLOR FFDEB887][%s][/COLOR]'
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
    url = params['url']
    title = params.get('title', '')
    thumb = params.get('thumb')
    level = int(__addon__.getSetting('resolution'))

    vcode = get_vid_from_url(url)

    if vcode:
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
    else:
        xbmcgui.Dialog().ok(__addonname__, '未匹配到VID')
        return


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


def buildParams(params):
    str = ''
    for item in params:
        str += '&%s=' % item + urllib.quote_plus(params[item])
    return str


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF00FF00] 【优酷视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = getHttpData(LIST_URL, headers={'User-Agent': UserAgent})
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'yk-filter'})

    grp = soup[0].find_all('li')
    for prog in grp[1:]:
        try:
            href = prog.a['href']
        except:
            break
        name = prog.text
        href = httphead(href)

        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listSubMenu(params):
    name = params['name']
    url = params['url']
    filter = params.get('filter', '')

    li = xbmcgui.ListItem(BANNER_FMT % (name+'(分类过滤 %s)' % filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = getHttpData(url, headers={'User-Agent': UserAgent})
    tree = BeautifulSoup(html, 'html.parser')
    # 分页
    soup = tree.find_all('ul', {'class': 'yk-pages'})
    pages = soup[0].find_all('li')
    for page in pages:
        try:
            href = page.a['href']
        except:
            continue
        title = page.text
        href = httphead(href)
        li = xbmcgui.ListItem(BANNER_FMT % title)
        u = sys.argv[0] + '?url=' + href
        u += '&mode=videolist'
        u += '&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # 剧目清单
    #items = soup[0].find_all('div', {'class': 'p-thumb'})
    items = tree.find_all('div', {'class': 'p-thumb'})
    for item in items:
        title = item.a['title']
        href = httphead(item.a['href'])
        img = httphead(item.img['src'])
        pay = item.find('span', {'class': 'vip-free'})
        if pay:
            pay = '[COLOR FFFF00FF]' + pay.text + '[/COLOR]'
        else:
            pay = ''
        li = xbmcgui.ListItem(title + '(' + pay + ')',
                              iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&name=' + urllib.quote_plus(name)
        u += '&mode=episodelist&title=' + title
        u += '&thumb=' + urllib.quote_plus(img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def normalSelect(params):
    url = params.get('url')
    name = params.get('name')
    filter = params.get('filter', '')

    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'item'})

    dialog = xbmcgui.Dialog()
    color = '[COLOR FF00FF00]%s[/COLOR]'
    for iclass in soup[1:]:
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
        sel = dialog.select(iclass.label.text, list)

        if sel < 0:
            continue
        filter += '|' + iclass.label.text + '(' + si[sel].text + ')'
        if sel == mark:
            continue

    listSubMenu(params)


def episodesList(params):
    url = params['url']
    html = getHttpData(url, headers={'User-Agent': UserAgent})
    tree = BeautifulSoup(html, 'html.parser')

    # 主题视频
    #soup = tree.find_all('div', {'class': 'lists'})
    items = tree.find_all('div', {'class': 'program'})
    if len(items) < 1:
        PlayVideo(params)
        return

    for item in items:
        title = item['title']
        href = httphead(item.a['href'])
        img = item.img['src']
        t = item.find('span', {'class': 'c-time'})
        time = t.text
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playvideo'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&thumb=' + img
        li = xbmcgui.ListItem(title + '(' + time + ')',
                              iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
    u = sys.argv[0] + '?url=' + url
    u += '&mode=episodelist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    # 相关视频
    soup = tree.find_all('div', {'class': 'textlists'})
    items = soup[0].find_all('li')
    for item in items:
        title = item['title']
        href = httphead(item.a['href'])
        u = sys.argv[0] + '?url=' + href
        u += '&mode=playvideo'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def searchInYouku(params):
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
    'videolist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'playvideo': 'PlayVideo(params)',
    'search': 'searchInYouku(params)',
    'select': 'normalSelect(params)'
}

eval(runlist[mode])
