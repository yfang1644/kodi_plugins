# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import sys
import gzip
import StringIO
from random import randrange
from bs4 import BeautifulSoup
import simplejson

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'

HOST_URL = 'http://www.fun.tv'

# get wrong IP from some local IP
unusableIP = ("121.32.237.24",
              "121.32.237.42",
              "222.84.164.2",
              "122.228.57.21")

# followings are usable
usableIP = ("112.25.81.203",
            "111.63.135.120",
            "122.72.64.198",
            "183.203.12.197",
            "223.82.247.101",
            "222.35.249.3")


########################################################################
# 风行视频(Funshion)"
########################################################################
# v1.1.1 2015.12.04 (taxigps)
# - Update video list fetching for site change
# - Add requires of simplejson

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))

RES_LIST = [['tv', '低清'],
            ['dvd', '标清'],
            ['high-dvd', '高清'],
            ['super_dvd', '超清']]

LANG_LIST = [['chi','国语'], ['arm','粤语'], ['und','原声']]


########################################################################
def log(txt):
    pass
#    message = '%s: %s' % (__addonname__, txt)
#    xbmc.log(msg=message, level=xbmc.LOGDEBUG)


def replaceServer(url):
    server = __addon__.getSetting('pickserver')
    if server == 'true':
        return url

    ip = re.compile('http://(\d+\.\d+\.\d+\.\d+)').findall(url)
    if ip[0] not in usableIP:    # replace a usable IP
        i_url = randrange(len(usableIP))
        return re.sub('http://(\d+\.\d+\.\d+\.\d+)',
                      'http://%s'%(usableIP[i_url]), url)
    else:
        return url


def httphead(url):
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


########################################################################
def getHttpData(url):
    log("%s::url - %s" % (sys._getframe().f_code.co_name, url))
    headers = {'User-Agent': UserAgent}

    req = urllib2.Request(url, headers=headers)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        log("%s (%d) [%s]" % (
               sys.exc_info()[2].tb_frame.f_code.co_name,
               sys.exc_info()[2].tb_lineno,
               sys.exc_info()[1]
               ))
        return ''

    httpdata = re.sub('\t|\n|\r', ' ', httpdata)
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if match:
        charset = match[0]
    else:
        match = re.compile('<meta charset="(.+?)"').findall(httpdata)
        if match:
            charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')

    return httpdata


########################################################################
def searchDict(dlist, idx):
    for i in range(0, len(dlist)):
        if dlist[i][0] == idx:
            return dlist[i][1]
    return ''


def mergeUrl(purl, curl):
    for x in curl:
        if len(x) < 2:
            continue
        hx = x[:2]
        for i in range(len(purl)):
            if purl[i].find(hx) >= 0:
                purl[i] = x
                break
        if x not in purl:
            purl.insert(0, x)

    return purl


##################################################################################
# Routine to update video list as per user selected filtrs
##################################################################################
def updateListSEL(params):
    url = params['url']
    surl = url.split('/')
    purl = surl[-2].split('.')

    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'ls-nav-bar'})

    dialog = xbmcgui.Dialog()

    filter = ''
    for iclass in soup[1:]:
        si = iclass.find_all('li')
        list = []
        for subitem in si:
            if 'bar-current' in subitem['class']:
                title = '[COLOR FFFF00FF]' + subitem.a.text + '[/COLOR]'
            else:
                title = subitem.a.text
            list.append(title)

        try:
            caption = iclass.label.text
        except:
            caption = u'排序'
        sel = dialog.select(caption, list)
        if sel >= 0:
            filter += '|[COLOR FFF00080]' + caption + '[/COLOR](' + si[sel].text + ')'
            curl = si[sel].a['href'].split('/')
            curl = curl[-2].split('.')
            purl = mergeUrl(purl, curl)

    surl[-2] = '.'.join(purl)
    params['url'] = '/'.join(surl)
    params['filtrs'] = filter

    mainList(params)


def playList(params):
    url = params['url']
    name = params['name']
    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    lists = tree.find_all('a', {'class': 'vd-list-item'})

    if len(lists) < 1:
        return

    u = sys.argv[0] + '?mode=albumlist&url=' + url
    li = xbmcgui.ListItem(BANNER_FMT % '播放列表')
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)

    for item in lists:
        href = httphead(item['href'])
        p_name = item['title']
        p_thumb = item.img.get('src')
        if p_thumb is None:
            p_thumb = item.img.get('_lazysrc')
        if p_thumb is None:
            p_thumb = ''
        t = item.find('i', {'class': 'vtime'})
        time = t.text
        vid = item['data-vid']
        li = xbmcgui.ListItem(p_name + '(' + time + ')',
                              iconImage='', thumbnailImage=p_thumb)
        u = sys.argv[0] + '?mode=movielist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&title=' + p_name
        u += '&thumb=' + p_thumb
        u += '&url=' + href + '&vid=' + vid
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)


def relatedList(params):
    vid = params['vid']
    name = params['name']
    url = params['url']
    # rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/media?isajax=1'
    rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/video?isajax=1'
    link = getHttpData(rel_api % vid)
    tree = BeautifulSoup(link, 'html.parser')

    items = tree.find_all('div', {'class': 'mod-vd-i'})
    if len(items) < 1:
        return

    u = sys.argv[0] + '?mode=albumlist&url=' + url
    li = xbmcgui.ListItem(BANNER_FMT % '相关推荐')
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)

    for item in items:
        pic = item.find('div', {'class': 'pic'})
        inf = item.find('div', {'class': 'info'})
        try:
            href = inf.a['href']
        except:
            continue
        href = httphead(href)
        p_id = pic.a['data-cid']
        p_thumb = httphead(pic.img['_lazysrc'])
        p_name = pic.img['alt']

        p_name1 = p_name + ' '
        span = pic.find('span')
        if span and len(span.text) > 0:
            p_name1 += '[COLOR FF00FFFF](' + span.text + ')[/COLOR] '

        score = inf.find('b', {'class': 'score'})
        if score:
            p_name1 += '[COLOR FFFF00FF][' + score.text + '][/COLOR]'

        if item.find("class='ico-dvd spdvd'") > 0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif item.find("class='ico-dvd hdvd'") > 0:
            p_name1 += ' [COLOR FF00FFFF][高清][/COLOR]'

        p_duration = item.find('i', {'class': 'tip'})
        if p_duration:
            p_name1 += ' [COLOR FF00FF00][' + p_duration.text + '][/COLOR]'

        desc = inf.find('p', {'class', 'desc'})
        if desc:
            p_name1 += ' (' + desc.text + ')'

        li = xbmcgui.ListItem(p_name1, iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type="Video", infoLabels={"Title": p_name})
        u = sys.argv[0] + '?mode=albumlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&title=' + p_name
        u += '&thumb=' + p_thumb
        u += '&url=' + href + '&vid=' + p_id
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)


##################################################################################
def singleVideo(params):
    url = params['url']
    sid = params['vid']
    title = params['title']
    thumb = params['thumb']
    name = params['name']

    u = sys.argv[0] + '?mode=movielist&title=' + urllib.quote_plus(title)
    u += '&name=' + urllib.quote_plus(name)
    u += '&thumb=' + urllib.quote_plus(thumb)
    u += '&vid=' + urllib.quote_plus(sid)

    li = xbmcgui.ListItem(BANNER_FMT % title, iconImage='', thumbnailImage=thumb)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)

    # playlist
    playList(params)

    # related
    relatedList(params)

    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
def seriesList(params):
    name = params['name']
    id = params['vid']
    thumb = params['thumb']
    # url = 'http://api.funshion.com/ajax/get_web_fsp/%s/mp4?isajax=1'
    url = 'http://api.funshion.com/ajax/vod_panel/%s/w-1?isajax=1'  #&dtime=1397342446859
    link = getHttpData(url % id)
    json_response = simplejson.loads(link)
    if json_response['status'] == 404:
        ok = xbmcgui.Dialog().ok(__addonname__, '本片暂不支持网页播放')
        return

    resolution = selResolution()

    items = json_response['data']['videos']
    # name = json_response['data']['name'].encode('utf-8')
    for item in items:
        p_name = '%s' % (item['name'].encode('utf-8'))
        # p_number = str(item['number'])
        try:
            hashid = item['streams'][resolution]['hashid']
        except:
            hashid = ''
        p_thumb = item['pic'].encode('utf-8')

        if len(p_thumb) < 2:
            p_thumb = thumb

        seconds = item['duration']
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time = "%d:%02d:%02d" % (h, m, s)

        u = sys.argv[0] + '?mode=movielist&title=' + urllib.quote_plus(p_name)
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(p_thumb)
        if item['dtype'] == 'prevue':
            extra = '|预'
            u += '&vid=' + str(item['videoid'])
        else:
            extra = ''
            u += '&hashid=' + urllib.quote_plus(hashid)

        li = xbmcgui.ListItem(p_name + '(' + time + extra + ')',
                              iconImage='', thumbnailImage=p_thumb)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, False)

    # playlist
    playList(params)

    # related
    relatedList(params)

    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
def selResolution():
    resolution = int(__addon__.getSetting('resolution'))
    if resolution == 4:
        list = [x[1] for x in RES_LIST]
        sel = xbmcgui.Dialog().select('清晰度', list)
        if sel == -1:
            sel = 2          # set default
        return sel
    else:
        return resolution


def PlayVideo_test(thumb):
    hashid = params.get('hashid')
    title = params.get('title')
    thumb = params.get('thumb')
    if hashid is None:
        id = params.get('vid')

        url = 'http://pv.funshion.com/v5/video/play/?id=%s&cl=aphone&uc=5'
        link = getHttpData(url % id)
        json_response = simplejson.loads(link)

        resolution = selResolution()

        hashid = json_response['mp4'][resolution]['infohash']
        filename = json_response['mp4'][resolution]['filename']
        # besides mp4, there maybe h265 available

    url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json' % (hashid)

    link = getHttpData(url)
    json_response = simplejson.loads(link)
    if json_response['return'].encode('utf-8') == 'succ':
        listitem = xbmcgui.ListItem(title, thumbnailImage=thumb)

        #xbmc.Player().play(json_response['playlist'][0]['urls'][0], listitem)
        # Randomly pick a server to stream video
        v_urls = json_response['playlist'][0]['urls']   #json_response['data']['fsps']['mult']
        # print "streamer servers: ", len(v_urls), v_urls, link, json_response['playlist'][0]
        i_url = randrange(len(v_urls))

        v_url = v_urls[i_url]
        v_url = replaceServer(v_url)
        xbmc.Player().play(v_url, listitem)
    else:
        ok = xbmcgui.Dialog().ok(__addonname__, '没有可播放的视频')


##################################################################################
def PlayVideo(params):
    name = params.get('name')

    videoplaycont = __addon__.getSetting('video_vplaycont')

    playlistA = xbmc.PlayList(0)
    playlist = xbmc.PlayList(1)
    playlist.clear()

    v_pos = int(name.split('.')[0]) - 1
    psize = playlistA.size()
    ERR_MAX = psize-1
    TRIAL = 1
    errcnt = 0
    k = 0

    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('匹配视频', '请耐心等候! 尝试匹配视频文件 ...')
    pDialog.update(0)

    for x in range(psize):
        # abort if ERR_MAX or more access failures and no video playback
        if (errcnt >= ERR_MAX and k == 0):
            pDialog.close()
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '无法播放：未匹配到视频文件')
            break

        if x < v_pos:
            continue
        p_item = playlistA.__getitem__(x)
        p_url = p_item.getfilename(x)
        p_list = p_item.getdescription(x)

        li = p_item   # pass all li items including the embedded thumb image
        li.setInfo(type="Video", infoLabels={"Title": p_list})

        type = 'video'        # choice?
        if not re.search('http://', p_url):  # fresh search
            if type == 'video':
                url = 'http://api.funshion.com/ajax/get_media_data/ugc/%s' % (p_url)
            else:
                url = 'http://api.funshion.com/ajax/get_media_data/video/%s' % (p_url)

            if (pDialog.iscanceled()):
                pDialog.close()
                x = psize     # quickily terminate any old thread
                err_cnt = 0
                return
            pDialog.update(errcnt*100/ERR_MAX + 100/ERR_MAX/TRIAL*1)

            link = getHttpData(url)
            try:
                json_response = simplejson.loads(link)
                hashid = json_response['data']['hashid'].encode('utf-8')
                filename = json_response['data']['filename'].encode('utf-8')
            except:
                errcnt += 1   # increment consequetive unsuccessful access
                continue
            url = 'http://jobsfe.funshion.com/query/v1/mp4/%s.json?file=%s' % (hashid, filename)

            link = getHttpData(url)
            try:   # prevent system occassion throw error
                json_response = simplejson.loads(link)
                status = json_response['return'].encode('utf-8')
            except:
                errcnt += 1   # increment consequetive unsuccessful access
                continue
            if status == 'succ':
                v_url = json_response['playlist'][0]['urls'][0]
                playlistA.remove(p_url)   # remove old url
                playlistA.add(v_url, li, x)  # keep a copy of v_url in Audio Playlist
            else:
                errcnt += 1   # increment consequetive unsuccessful access
                continue
        else:
            v_url = p_url

        err_cnt = 0    # reset error count

        v_url = replaceServer(v_url)
        playlist.add(v_url, li, k)
        k += 1
        if k == 1:
            pDialog.close()
            xbmc.Player(1).play(playlist)
        if videoplaycont == 'false':
            break


##################################################################################
def albumList(params):
    url = params['url']
    sid = re.search('http://www.fun.tv/vplay/.*v-(\d+)', url)
    vid = re.search('http://www.fun.tv/vplay/.*g-(\d+)', url)
    if sid:
        params['vid'] = sid.group(1)
        singleVideo(params)    # play single video
    elif vid:
        params['vid'] = vid.group(1)
        seriesList(params)     # list series
    else:
        xbmcgui.Dialog().ok(__addonname__, '本片暂不支持网页播放')
        return


##################################################################################
def mainList(params):
    name = params['name']
    url = params['url']
    filtrs = params.get('filtrs', '').encode('utf-8')

    html = getHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod-videos'})

    items = soup[0].find_all('div', {'class': 'mod-vd-i'})
    items = tree.find_all('div', {'class': 'mod-vd-i'})

    li = xbmcgui.ListItem(name + '【选择过滤】' + filtrs)
    u = sys.argv[0] + '?mode=filter&name=' + urllib.quote_plus(name)
    u += '&url=' + url
    u += '&filtrs=' + urllib.quote_plus(filtrs)
    xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    for item in items:
        pic = item.find('div', {'class': 'pic'})
        inf = item.find('div', {'class': 'info'})
        href = httphead(inf.a['href'])
        p_id = pic.a['data-id']
        p_thumb = httphead(pic.img['_lazysrc'])
        p_name = pic.img['alt']

        p_name1 = p_name + ' '
        span = pic.find('span')
        if span and len(span.text) > 0:
            p_name1 += '[COLOR FF00FFFF](' + span.text + ')[/COLOR] '

        score = inf.find('b', {'class': 'score'})
        if score:
            p_name1 += '[COLOR FFFF00FF][' + score.text + '][/COLOR]'

        if item.find("class='ico-dvd spdvd'") > 0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif item.find("class='ico-dvd hdvd'") > 0:
            p_name1 += ' [COLOR FF00FFFF][高清][/COLOR]'

        p_duration = item.find('i', {'class': 'tip'})
        if p_duration:
            p_name1 += ' [COLOR FF00FF00][' + p_duration.text + '][/COLOR]'

        desc = inf.find('p', {'class', 'desc'})
        if desc:
            p_name1 += ' (' + desc.text + ')'

        li = xbmcgui.ListItem(p_name1, iconImage='', thumbnailImage=p_thumb)
        li.setInfo(type="Video", infoLabels={"Title": p_name})
        u = sys.argv[0] + '?mode=albumlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&title=' + p_name
        u += '&thumb=' + p_thumb
        u += '&url=' + href
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    # Construct page selection
    soup = tree.find_all('div', {'class': 'pager-wrap'})
    if len(soup) > 0:
        pages = soup[0].find_all('a')

        for page in pages:
            href = page['href']
            if href == '###':
                continue
            else:
                href = httphead(href)
                title = page.text
                li = xbmcgui.ListItem(title)
                u = sys.argv[0] + '?mode=mainlist'
                u += '&name=' + urllib.quote_plus(name)
                u += '&url=' + href
                xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    xbmcplugin.setContent(pluginhandle, 'movies')
    xbmcplugin.endOfDirectory(pluginhandle)


##################################################################################
def rootList():
    html = getHttpData('http://www.fun.tv/retrieve/')
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'ls-nav-bar'})
    items = soup[0].find_all('li')

    for item in items:
        name = item.a.text.encode('utf-8')
        url = httphead(item.a['href'])
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?mode=mainlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&url=' + urllib.quote_plus(url)
        xbmcplugin.addDirectoryItem(pluginhandle, u, li, True)

    xbmcplugin.endOfDirectory(pluginhandle)


#  main program goes here #
pluginhandle = int(sys.argv[1])
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'rootList()',
    'mainlist': 'mainList(params)',
    'albumlist': 'albumList(params)',
    'movielist': 'PlayVideo_test(params)',
    'playvideo': 'PlayVideo(params)',
    'filter': 'updateListSEL(params)'
}

eval(runlist[mode])
