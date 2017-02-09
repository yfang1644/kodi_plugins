# -*- coding: utf-8 -*-

#v1.0.0 2009/11/08 by robinttt, initial release
#v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import urllib
import urllib2
import os
import re
import sys
import gzip
import StringIO #playvideo
import hashlib, time
from bs4 import BeautifulSoup
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon


UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'
URL_BASE = 'http://yinyue.kuwo.cn'
INDENT_STR = '    '
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'


#
# Web process engine
#
def getUrlTree(url, data=None):
    if data and not isinstance(data, str):
        # 2-item tuple or param dict, assume utf-8
        data = urllib.urlencode(data)
    req = urllib2.Request(url, data, {'User-Agent': UserAgent})
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        # BeautifulSoup handles encoding, thus skip transcoding here.

    tree = BeautifulSoup(httpdata, "html.parser")
    return tree


def make_param(query, url=None):
    if url is None:
        url = sys.argv[0]
    param = "%s?%s" % (url, urllib.urlencode(query))
    return param


def addDir(name, url, mode, iconimage='DefaultFolder.png', context={}, folder=True, total=0):
    if url.startswith('/'):
        url = URL_BASE + url

    param = {"url": url, "mode": mode}
    param.update(context)
    u = make_param(param)

    item = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=item, isFolder=folder, totalItems=total)


context_params = {}


def driller(tree, lCont):
    # global item
    global context_params
    if not isinstance(lCont, list):
        lCont = [lCont]

    for cont in lCont:
        result = None
        context_params = cont.get('context', {})
        items = tree.find_all(*cont['tag'])
        # print("to find:", cont)
        for item in items:
            # print('found')
            if cont.get('vect'):
                try:
                    result = cont['vect'](item)
                except:
                    pass
            if result != 'DRILLER_NO_DEEPER':
                if cont.get('child', None):
                    driller(item, cont['child'])


def processWebPage(tagHandler):
    global tree
    url = params['url']
    post = params.get('urlpost', None)
    tree = getUrlTree(url, post)
    driller(tree, tagHandler)
    xbmcplugin.endOfDirectory(pluginhandle, True)

#
# Media player
#
def get_content_by_tag(tree, tag):
    f = tree.find(tag)
    if f and f.contents:
        return f.contents[0].encode('utf-8')
    else:
        return ''


def PlayMusic():
    mids = params['url']

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    mids = mids.split('/')
    for mid in mids:
        if mid == '':
            continue
        tree = getUrlTree('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_'+mid)
        title = get_content_by_tag(tree, 'name')
        # kuwo has names like "song name(抢听版)", causing lyrics look up failure
        true_title = title.split('(')[0].rstrip()
        artist = get_content_by_tag(tree, 'artist')
        iconimage = get_content_by_tag(tree, 'artist_pic240')

        # prefer AAC or WMA, somehow it starts or loads faster than the mp3 link,
        # change AAC to the first download.  edit by runner6502@gamil.com
        path = get_content_by_tag(tree, 'aacpath')
        dl = get_content_by_tag(tree, 'aacdl')
        if not (path and dl):
            path = get_content_by_tag(tree, 'path')
            dl = get_content_by_tag(tree, 'wmadl')
            if not (path and dl):
                path = get_content_by_tag(tree, 'mp3path')
                dl = get_content_by_tag(tree, 'mp3dl')

        if path and dl:
            timestamp = ("%x" % int(time.time()))[:8]
            hashstr = hashlib.md5("kuwo_web@1906/resource/%s%s" % (path, timestamp)).hexdigest()
            url = 'http://%s/%s/%s/resource/%s' % (dl, hashstr, timestamp, path)

            listitem = xbmcgui.ListItem(title, iconImage=iconimage, thumbnailImage=iconimage)
            listitem.setInfo(type="Music", infoLabels={"Title": true_title, "Artist": artist})
            playlist.add(url, listitem)

        xbmc.Player().play(playlist)


def addH1Banner(item):
    name = item.h1.text.encode('utf-8')
    # Burlywood color
    if name:
        name = BANNER_FMT % name
        addDir(name, '', 'pass', '', folder=False)


#
# Kuwo tag handlers
#
def extractName(item):
    if not item:
        return ''
    name = ''
    span_name = item.find('span')
    if span_name:
        name = span_name.contents[0]
    elif item.has_attr('title'):
        name = item['title']
    elif item.contents:
        content = item.contents[0]
        if 'String' in str(type(content)):
            #BeautifulSoup NavigableString
            name = content
        else:
            try:
                name = content['title']
            except:
                pass
    return name.encode('utf-8')


def extractHref(item):
    if item and item.has_attr('href'):
        return item['href'].encode('utf-8')
    return ''


def extractImg(item):
    if item:
        for k in ['lazy_src', 'sr', 'src', 'init_src']:
            if item.has_attr(k):
                return item[k].encode('utf-8')
    return ''


def extractImgSearch(item, name=''):
    iconimage = extractImg(item.find('img'))
    if (not iconimage) and name:
        attrs = {'title': unicode(name, 'utf-8')}
        iconimage = extractImg(item.findChild('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findPreviousSibling('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findParent().findPreviousSibling('img', attrs))
    return iconimage


#
# XBMC plugin
#
def addLink(title, artist, url, mode, iconimage='', total=0, video=False):
    u = make_param({'url': url, 'mode': mode})
    displayname = artist + ' - ' + title if artist else title
    displayname = INDENT_STR + displayname
    itemType = 'Video' if video else 'Music'

    item = xbmcgui.ListItem(displayname, iconImage=iconimage, thumbnailImage=iconimage)
    item.setInfo(type=itemType, infoLabels={'Title': title, 'Artist': artist})
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=item, isFolder=False, totalItems=total)



# 分类
def addHotMusic(item):
    l = re.findall('"musiclist":(\[.+\]),"rids"', item.text)
    if not l:
        return
    l = eval(l[0])
    mids = "/".join([d['musicrid'] for d in l])
    disp_title = params.get('playall_title', '播放全部歌曲')
    iconimg = params.get('playall_icon', '')
    addDir(disp_title, mids, 'PlayMusic()', iconimg, folder=False)
    for d in l:
        title = d['name']
        artist = d['artist']
        mid = d['musicrid']
        addLink(title, artist, mid, 'PlayMusic()', '')


def addHotMusicList(item):
    ''' playlist item '''
    url = extractHref(item.a)
    name = extractName(item.a)
    iconimg = extractImg(item.a.img)
    playall_title = '播放【%s】所含曲目' % name
    context = {'playall_title': playall_title, 'playall_icon': iconimg}
    addDir(INDENT_STR + name, url, 'processWebPage(hotMusic)', iconimg, context=context)


def addHotList(item):
    ''' playlist item '''
    url = extractHref(item.a)
    name = extractName(item.a)
    iconimg = extractImg(item.a.img)
    context = {'playall_title': '', 'playall_icon': iconimg}
    if name in hotSubList:
        addDir(name, url, 'processWebPage(hotList)', iconimg, context=context)
    else:
        addDir(INDENT_STR + name, url, 'processWebPage(hotMusicListPage)', iconimg, context=context)


hotMusic = {'tag': ('script', {}), 'vect': addHotMusic}
hotMusicList = {'tag': ('li', {}), 'vect': addHotMusicList}
hotMusicListPage = {'tag': ('ul', {'class': 'singer_list clearfix'}), 'child': hotMusicList}
hotList = {'tag': ('li', {}), 'vect': addHotList}
hotPage = {'tag': ('div', {'class': 'hotlist'}), 'vect': addH1Banner, 'child': hotList}
hotSubList = {'评书', '有声读物', '歌手'}


pluginhandle = int(sys.argv[1])
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))
mode = params.get('mode')

if mode is None:
    url = 'http://yinyue.kuwo.cn/category.htm'
    u = sys.argv[0] + '?&mode=hotPage' + '&url=%s' % (url)

    params['url'] = url
    processWebPage(hotPage)

else:
    exec(mode)
