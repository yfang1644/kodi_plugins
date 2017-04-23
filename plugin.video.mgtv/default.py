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

HOST_URL = 'https://v.qq.com'
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
PARSING_URL = 'http://vv.video.qq.com/getinfo?vids=&defn=sd&otype=json'
VIDEO_SRV = ('http://182.254.72.11',
             'http://182.254.72.110',
             'http://182.254.72.117',
             'http://182.254.8.74',
             'http://124.89.197.14',
             'http://124.89.197.16',
             'http://111.47.228.17',
             'http://111.47.228.19',
             'http://117.135.168.23',
             'http://117.135.168.25',
             'http://117.135.168.26',
             'http://117.135.128.159',
             'http://117.135.128.160',
             'http://111.47.228.20',
             'http://111.47.228.26',
             'http://111.47.228.23')

# p203(270), p212(360), p201(720)

dbg = False
dbglevel = 3


def log(description, level=0):
    if dbg and dbglevel > level:
        print description


def GetHttpData(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', UserAgent_IPAD)
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
        if '(' in name:
            mode = 'otherlist'
        else:
            mode = 'mainlist'
        u = sys.argv[0] + '?mode=%s&name=%s' % (mode, name)
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
    print '---------AURL------',aurl
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    if 'offset' in params:
        page = int(params['offset']) // 30
    else:
        page = 0
    li = xbmcgui.ListItem(name+'【第%d页】(分类过滤)' % (page + 1))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select' + strparam
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    if 'mode' not in params:
        strparam += '&mode=episodelist'
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

        li = xbmcgui.ListItem(title + info, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + strparam
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
    strparam = buildParams(params)
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
        tn = item.a.text
        tn = re.sub('\t|\n|\r| ', '', tn)
        title = title + '--' + tn
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video',
                   infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + HOST_URL + href
        u += strparam + '&mode=playvideo'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    url = params['url']
    del(params['url'])
    strparam = buildParams(params)
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    match = re.compile('var LIST_INFO = ({.+?}});{0,}\n').search(html)
    js = json.loads(match.group(1))
    vidlist = js['vid']
    if len(vidlist) == 1:
        params['vid'] = vidlist[0]
        playVideo(params)
    else:
        for item in vidlist:
            try:
                title = js['data'][item]['title']
            except:
                break
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
    strparam = buildParams(params)
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

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def fashion(params):
    url = params['url']
    del(params['url'])
    print '=====================',url
    strparam = buildParams(params)
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod_title'})

    print soup
    show = soup[1].find_all('a')
    for item in show:
        title = item['title']
        href = HOST_URL + '/x/cover/' + item['data-cid'] + '.html'
        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist' + strparam
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def videoparse(vid):
    i_url = randrange(len(VIDEO_SRV))
    server = VIDEO_SRV[i_url] + '/vlive.qqvideo.tc.qq.com/'
    return server


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
    fmd5 = js['fmd5']
    typelist = jsdata['fl']['fi']
    files = js['cl']['fc']

    typeid = []
    for idlist in typelist:
        id = '%d' % idlist['id']
        if (id == '2') or (id == '320048'):
            id = typeid[0]['id'][0:3] + '12'
        if id[0:3] == '100':
            id = '10' + id[3:]

        typeid.append({'cname': idlist['cname'], 'id': id})

    filename = js['fn'].split('.')
    fid = filename[0]    # file-id
    title = js['ti']     # video title
    dur = js['td']       # video duration in seconds
    preurl = js['ul']['ui']
    url = []
    for u in preurl:
        pattern = 'http://(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})'
        addr = re.compile(pattern).search(u['url'])
        if addr:
            url.append(u)

    if len(url) > 0:
        server = url[0]['url']
    else:
        server = videoparse(0)

    sel = int(__addon__.getSetting('resolution'))
    if sel == 4:
        list = [x['cname'] for x in typeid]
        sel = xbmcgui.Dialog().select('清晰度选择', list)

    if sel < 0:
        sel = 0

    if sel >= len(typeid):
        sel = len(typeid) - 1

    id = typeid[sel]['id']
    id = '.p' + id[2:]

    url = PARSING_URL.replace('getinfo', 'getkey')
    url = url.replace('vids=', 'vid=' + vid)
    url += '&format=' + typeid[sel]['id']
    url += '&filename=' + fid + id
    urllist = []

    series = int(float(dur) / 300.0)       # each piece 5 minutes
    if series == 0:
        series = 1
    appver = '3.2.19.358'
    encryptver = '5.4'
    for i in range(1, int(files)+1):
        jspage = GetHttpData(url + '.%d.mp4' % i)
        jspage = jspage[13:-1]   # remove heading and tail
        jsdata = json.loads(jspage)
        print jsdata
        key = jsdata.get('key')

        app = '.%d.mp4?vkey=%s&appver=3.2.19.358&encryptver=5.4' % (i, key)
        app += '&platform=11'
        urllist.append(server + fid + id + app)

    return urllist, title


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
    ulen = len(urllist)
    if ulen > 0:
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for i in range(0, ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            liz = xbmcgui.ListItem(name, thumbnailImage='')
            liz.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(urllist[i], liz)

        xbmc.Player().play(playlist)
    else:
        xbmcgui.Dialog().ok(__addonname__, '无法获取视频地址')


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

if mode is not None:
    del(params['mode'])

runlist = {
    None: 'listRoot()',
    'mainlist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'otherlist': 'fashion(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo(params)'
    }

eval(runlist[mode])
