# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import gzip
from random import randrange
import StringIO
from bs4 import BeautifulSoup
try:
    import json
except:
    import simplejson as json

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'

UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

HOST_URL = 'http://v.qq.com'
CHANNEL_LIST = {'电视剧': '/x/list/tv',
                '综艺': '/x/list/variety',
                '电影': '/x/list/movie',
                '动漫': '/x/list/cartoon',
                '少儿': '/x/list/children',
                '娱乐': '/x/list/ent',
                '音乐': '/x/list/music',
                '纪录片': '/x/list/doco',
                '(微电影)': '/dv',
                '新闻': '/x/list/news',
                '体育': '/x/list/sports',
                '搞笑': '/x/list/fun',
                '(原创)': '/videoplus',
                '(时尚)': '/fashion',
                '(生活)': '/life',
                '(科技)': '/tech',
                '(汽车)': '/auto',
                '(财经)': '/finance'}

RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}
PARSING_URL = 'http://vv.video.qq.com/getinfo?vids=&charge=0&otype=json'
VIDEO_SRV = ('http://182.254.72.11',
             'http://182.254.72.110',
             'http://182.254.72.117',
             'http://182.254.8.74',
             'http://111.47.228.17',
             'http://111.47.228.19',
             'http://111.47.228.20',
             'http://111.47.228.26',
             'http://111.47.228.23')

# p203(270), p212(360), p201(720)
INDENT1 = '    '


dbg = False
dbglevel = 3


def log(description, level=0):
    if dbg and dbglevel > level:
        print description


def GetHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        response.close()
        if response.headers.get('content-encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    except:
        print 'GetHttpData Error: %s' % url
        return ''

    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    charset = ''
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf-8', 'ignore')
    return httpdata


def listRoot():
    for name in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?mode=mainlist&name=' + name
        u += '&url=' + HOST_URL + CHANNEL_LIST[name]
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def changeList(params):
    url = params.get('url')
    del(params['url'])
    name = params.get('name')
    del(params['name'])
    strparam = buildParams(params)
    aurl = url + '?' + strparam[1:]
    html = GetHttpData(aurl)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    change = False
    dialog = xbmcgui.Dialog()

    setparam = ''
    for iclass in soup:
        si = iclass.find_all('a')
        list = []
        item = []
        for subitem in si:
            list.append(subitem.text)
            item.append(subitem['href'])
        sel = dialog.select(iclass.span.text, list)

        if sel >= 0:
            setparam += item[sel]

    setparam = setparam.replace('?', '&')
    setparam = 'url=%s' % url + setparam
    params = dict(urllib2.urlparse.parse_qsl(setparam))
    params['name'] = name
    params['mode'] = 'mainlist'
    listSubMenu(params)


def buildParams(params):
    str = ''
    for item in params:
            str += '&%s=' % item + urllib.quote_plus(params[item])
    return str


def getMovieInfo(url):
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('span', {'class': 'item'})

    info = tree.find('meta', {'name': 'description'})['content']
    if info:
        return info
    else:
        return ''


def listSubMenu(params):
    url = params.get('url')
    del(params['url'])
    name = params.get('name')
    strparam = buildParams(params)
    aurl = url + '?' + strparam[1:]
    html = GetHttpData(aurl)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    offset = params.get('offset')
    if offset:
        page = int(offset) // 30
    else:
        page = 0
    li = xbmcgui.ListItem(name+'【第%d页】(分类过滤)' % (page + 1))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select' + strparam
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('li', {'class': 'list_item'})
    for mainpage in soup:
        img = mainpage.img['r-lazyload']
        if img[0:2] == '//':
            img = 'http:' + img
        title = mainpage.strong.a.text
        info = mainpage.find('span', {'class': 'figure_info'})
        if info:
            info = '(' + info.text + ')'
        else:
            info = ''
        href = mainpage.strong.a['href']
        mark = mainpage.find('i', {'class': 'mark_v'})
        if mark:
            info += '(' + mark.img['alt'] + ')'

        if name in ('电影'):
            minfo = ''    # getMovieInfo(href)
        li = xbmcgui.ListItem(title + info, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist' + strparam
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # PAGE LISTING
    soup = tree.find_all('div', {'class': 'mod_pages'})
    pages = soup[0].find_all('a')
    for page in pages:
        title = page.text
        href = page['href']
        if href[0] == '?':
            href = href[1:]

        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + url + strparam + href
        u += '&mode=mainlist&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seriesList(params):
    url = params['url']
    del(params['url'])
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('span', {'class': 'item'})

    info = tree.find('meta', {'name': 'description'})['content']
    img = tree.find('meta', {'itemprop': 'image'})['content']
    for item in soup:
        try:
            title = item.a['title']
        except:
            continue
        try:
            href = item.a['href']
        except:
            continue
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video',
                   infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + HOST_URL + href + '&mode=playvideo'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def documentList(params):
    url = params['url']
    del(params['url'])
    strparam = buildParams(params)
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('span', {'class': 'item'})
    match = re.compile('var LIST_INFO = ({.+?}});{0,}\n').search(html)

    js = json.loads(match.group(1))
    for item in js['data']:
        title = js['data'][item]['title']
        vid = js['data'][item]['vid']
        img = js['data'][item]['preview']
        if img[0:2] == '//':
            img = 'http:' + img
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playvideo&vid=' + vid + strparam
        u += '&name=' + urllib.quote_plus(title.encode('utf-8'))
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def musicList(params):
    url = params['url']
    del(params['url'])
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find('div', {'class': 'player_side_bd'})
    soup = soup.find_all('li', {'class': 'list_item'})

    for item in soup:
        vid = item.get('data-vid')
        if not vid:
            vid = item.get('id')
        if not vid:
            continue
        title = item.img['alt']
        img = item.img.get('r-lazyload')
        if not img:
            img = item.img.get('src')
        if not img:
            img = ''

        if img[0:2] == '//':
            img = 'http:' + img
        href = item.a['href']
        if href[0] == '/':
            href = HOST_URL + href
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo&vid=' + vid
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'music')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    name = params['name']
    if name in ('纪录片'):
        documentList(params)
    elif name in ('音乐'):
        musicList(params)
    elif name in ('电视剧', '卡通', '少儿'):
        seriesList(params)
    else:
        playVideo(params)


def videoparseX(vid):
    print '------------------------'
    url = PARSING_URL.replace('vids=', 'vids=' + vid)
    print url
    jspage = GetHttpData(url)
    jspage = jspage[13:-1]   # remove heading and tail
    print jspage
    jsdata = json.loads(jspage)

    js = jsdata['vl']['vi'][0]
    fvkey = js['fvkey']
    typelist = jsdata['fl']['fi']
    typeid = ['%d' % x['id'] for x in typelist]
    filename = js['fn'].split('.')
    fid = filename[0]    # file-id
    title = js['ti']     # video title
    dur = js['td']       # video duration in seconds
    url = js['ul']['ui']
    for u in url:
        if u['vt'] == 0:
            url.remove(u)

    x = randrange(len(url))
    server = url[x]['url']

    resolution = int(__addon__.getSetting('resolution'))
    if resolution >= len(typeid):
        resolution = len(typeid) - 1
    id = typeid[resolution]
    if id == '2':
        typeid[resolution] = typeid[0][:3] + '12'
        id = typeid[resolution]
    id = '.p' + id[2:]

    url = PARSING_URL.replace('getinfo', 'getkey')
    url = url.replace('vids=', 'vid=' + vid)
    url += '&format=' + typeid[resolution]
    url += '&filename=' + fid + id
    urllist = []
    print url
    for i in range(1, 1000):   # set a big number
        jspage = GetHttpData(url + '.%d.mp4' % i)
        jspage = jspage[13:-1]   # remove heading and tail
        jsdata = json.loads(jspage)
        if jsdata.get('filename'):
            urllist.append(server + fid + id + '.%d.mp4' % i)
        else:
            break

    return urllist, title


def videoparse(vid):
    i_url = randrange(len(VIDEO_SRV))
    server = VIDEO_SRV[i_url] + '/vlive.qqvideo.tc.qq.com/' + vid
    return server


def playVideo(params):
    vid = params.get('vid')
    if not vid:
        url = params['url']
        http = GetHttpData(url)
        http = re.sub('\r|\n|\t', '', http)
        vid = re.compile('var VIDEO_INFO.+?vid:(.+?),').findall(http)
        vid = re.sub(' ', '', vid[0])
        vid = vid.strip('"')

    urllist, title = videoparseX(vid)
    print urllist
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    item = xbmcgui.ListItem(title, thumbnailImage='')
    for i in range(0, len(urllist)):
        playlist.add(urllist[i])

    xbmc.Player().play(playlist)


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

if mode is None:
    listRoot()
else:
    del(params['mode'])

if mode == 'mainlist':
    listSubMenu(params)
elif mode == 'episodelist':
    episodesList(params)
elif mode == 'playvideo':
    playVideo(params)
elif mode == 'play':
    playSingle(params)
elif mode == 'select':
    changeList(params)
