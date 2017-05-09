#!/usr/bin/python
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
__profile__   = xbmc.translatePath(__addon__.getAddonInfo('profile'))
cacheFile = __profile__ + 'cache.qq'
if (__addon__.getSetting('keyboard') != '0'):
    from xbmc import Keyboard as Apps
else:
    from ChineseKeyboard import Keyboard as Apps

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'

UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

HOST_URL = 'https://v.qq.com'
CHANNEL_LIST = {'电视剧': '/x/list/tv',
                '综艺': '/x/list/variety',
                '电影': '/x/list/movie',
                '动漫': '/x/list/cartoon',
                '少儿': '/x/list/children',
                '娱乐': '/x/list/ent',
                '音乐': '/x/list/music',
                '纪录片': '/x/list/doco',
                '微电影': '/dv',
                '新闻': '/x/list/news',
                '体育': '/x/list/sports',
                '搞笑': '/x/list/fun',
                '原创': '/videoplus',
                'TED': '/vplus/ted/folders',
                '时尚': '/fashion',
                '生活': '/life',
                '科技': '/tech',
                '汽车': '/auto',
                '财经': '/finance'}

#PARSING_URL += '&callback=txplayerJsonpCallBack_getinfo_8458820'
#PARSING_URL += '&guid=daef38ead87c2db3d343ca75f432212f'
#PARSING_URL += '&ehost=%s'
#https://h5vv.video.qq.com/getinfo?
#callback=txplayerJsonpCallBack_getinfo_845882
#&charge=0&vid=t0018ut1022&defaultfmt=auto&otype=json
#&guid=daef38ead87c2db3d343ca75f432212f&platform=10901
#&defnpayver=1&appVer=3.0.52&sdtfrom=v1010&host=v.qq.com
#&ehost=https%3A%2F%2Fv.qq.com%2Fx%2Fcover%2F5c58griiqftvq00%2Ft0018ut1022.html
#&_rnd=1492350493&defn=hd&fhdswitch=0&show1080p=1&isHLS=0
#&newplatform=10901&defsrc=2


def httphead(url):
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


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

    tree = BeautifulSoup(httpdata, 'html.parser')
    try:
        jump = tree.title.text
    except:
        return httpdata
    if u'正在跳转' in jump:
        url = tree.link['href']
        httpdata = GetHttpData(url)

    return httpdata


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF808F00] 【腾讯视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    for name in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        if name in ('TED'):
            mode = 'tedlist'
        elif name in ('微电影', '时尚', '原创',
                      '生活', '财经', '汽车', '科技'):
            mode = 'otherlist'
        else:
            mode = 'mainlist'
        u = sys.argv[0] + '?mode=%s&name=%s' % (mode, name)
        u += '&url=' + httphead(CHANNEL_LIST[name])
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


def listSubMenu(params):
    url = params.get('url')
    del(params['url'])
    name = params.get('name')
    strparam = buildParams(params)
    aurl = url + '?' + strparam[1:]
    html = GetHttpData(aurl)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    if 'offset' in params:
        page = int(params['offset']) // 30 + 1
    else:
        page = 1
    li = xbmcgui.ListItem(BANNER_FMT % (name+'【第%d页】(分类过滤)' % page))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select' + strparam
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('li', {'class': 'list_item'})
    for mainpage in soup:
        img = httphead(mainpage.img['r-lazyload'])
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
        u += '&mode=episodelist&thumb=' + img + '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # PAGE LISTING
    soup = tree.find_all('div', {'class': 'mod_pages'})
    pages = soup[0].find_all('a')
    for site in pages:
        title = site.text
        try:
            number = int(title)
        except:
            number = -99
        if number == page:
            continue
        href = site['href']
        if href[0] == '?':
            href = href[1:]         #  href looks like '?&offset=30'

        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + url + strparam + href
        u += '&mode=mainlist&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seriesList(params):
    url = params['url']
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
        u = sys.argv[0] + '?url=' + httphead(href) + '&mode=playvideo'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    url = params['url']
    thumb = params['thumb']
    title = params['title']

    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    info = tree.find('meta', {'name': 'description'})['content']

    match = re.compile('var LIST_INFO = ({.+?}});{0,}\n').search(html)
    js = json.loads(match.group(1))
    li = xbmcgui.ListItem(BANNER_FMT % title,
                          iconImage=thumb, thumbnailImage=thumb)
    li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
    u = sys.argv[0] + '?url=' + url + '&mode=episodelist'
    u += '&title=' + title + '&thumb=' + thumb
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in js['vid']:
        try:
            title = js['data'][item]['title']
        except:
            continue
        vid = js['data'][item]['vid']
        try:
            img = js['data'][item]['preview']
        except:
            img = thumb
        img = httphead(img)
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playvideo&vid=' + vid
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
    u = sys.argv[0] + '?url=' + url + '&mode=episodelist'
    u += '&title=' + title + '&thumb=' + thumb
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('li', {'class': 'list_item'})
    for item in soup:
        vid = item.get('data-vid')
        if not vid:
            vid = item.get('id', '')
        img = item.img.get('r-lazyload')
        if not img:
            img = item.img.get('src')
        if not img:
            img = ''
        img = httphead(img)
        href = httphead(item.a['href'])
        href = href.replace('?', '&')
        titlemsg = item.find('a', {'_stat': 'tabs-columns:title'})
        if titlemsg:
            title = titlemsg.text
        else:
            try:
                title = item.img['alt']
            except:
                title = item.a['title']
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=episodelist'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&url=' + urllib.quote_plus(href)
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def tedAlbum(params):
    url = params['url']
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod_video_list_content ui_scroll_content'})
    soup = soup[0].find_all('li', {'class': 'item'})

    for item in soup:
        vid = item.a['id']
        info = item.a['desc']
        title = item.a['title']
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=playvideo&vid=' + vid
        u += '&title=' + title + '&thumb='
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def tedFolders(params):
    url = params['url']
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'site_container'})
    maintitle = soup[0].find('span', {'class': 'count_num'}).text

    li = xbmcgui.ListItem(BANNER_FMT % maintitle.encode('utf-8'))
    u = sys.argv[0] + '?url=' + url + '&mode=tedlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = soup[0].find_all('li', {'class': 'list_item'})

    for item in soup:
        href = httphead(item.a['href'])
        img = httphead(item.img['src'])
        text = item.find('strong', {'class': 'album_title'})
        if text is None:
            title = item.a['title']
        else:
            title = text.text
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        if '.html' in href:
            mode = 'tedalbum'
        else:
            mode = 'tedlist'
        u = sys.argv[0] + '?url=' + href + '&mode=' + mode
        u += '&title=' + title
        u += '&thumb=' + urllib.quote_plus(img)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def fashion(params):
    url = params['url']
    name = params['name']
    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'nav_area'})
    list1 = soup[0].find_all('a')
    soup = tree.find_all('div', {'class': 'slider_nav'})
    list2 = soup[0].find_all('a')

    li = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0] + '?url=' + url + '&mode=otherlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in list1 + list2:
        title = item.text
        href = httphead(item['href'])
        try:
            img = httphead(item['data-bgimage'])
        except:
            img = 'xxx'
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&title=' + title + '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')

    li = xbmcgui.ListItem(BANNER_FMT % '其他视频')
    u = sys.argv[0] + '?url=' + url + '&mode=otherlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('ul', {'class': 'figures_list'})
    for group in soup:
        items = group.find_all('li', {'class': 'list_item'})
        for item in items:
            title = item.a['title']
            href = item.a['href']
            try:
                img = item.img['src']
            except:
                img = item.img['lz_src']
            li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
            u += '&title=' + title + '&thumb=' + img
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def videoparse(vid):
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

    i_url = randrange(len(VIDEO_SRV))
    server = VIDEO_SRV[i_url] + '/vlive.qqvideo.tc.qq.com/'
    return server


def qq_by_vid(vid):
    info_api = 'http://vv.video.qq.com/getinfo?otype=json&appver=3%2E2%2E19%2E333&platform=11&defnpayver=1&vid=' + vid
    jspage = GetHttpData(info_api)
    jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
    video_json = json.loads(jspage)

    parts_vid = video_json['vl']['vi'][0]['vid']
    parts_ti = video_json['vl']['vi'][0]['ti']
    parts_prefix = video_json['vl']['vi'][0]['ul']['ui'][0]['url']
    parts_formats = video_json['fl']['fi']
    if parts_prefix.endswith('/'):
        parts_prefix = parts_prefix[:-1]
    # find best quality
    # only looking for fhd(1080p) and shd(720p) here.
    # 480p usually come with a single file, will be downloaded as fallback.
    best_quality = ''
    for part_format in parts_formats:
        if part_format['name'] == 'hd':
            best_quality = 'hd'
            break

        if part_format['name'] == 'sd':
            best_quality = 'sd'

    for part_format in parts_formats:
        if (not best_quality == '') and (not part_format['name'] == best_quality):
            continue
        part_format_id = part_format['id']
        part_format_sl = part_format['sl']
        part_urls = []
        if part_format_sl == 0:
            try:
                # For fhd(1080p), every part is about 100M and 6 minutes
                # try 100 parts here limited download longest single video of 10 hours.
                for part in range(1,100):
                    filename = vid + '.p' + str(part_format_id % 10000) + '.' + str(part) + '.mp4'
                    key_api = "http://vv.video.qq.com/getkey?otype=json&platform=11&format=%s&vid=%s&filename=%s" % (part_format_id, parts_vid, filename)
                    #print(filename)
                    #print(key_api)
                    jspage = GetHttpData(key_api)
                    jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
                    key_json = json.loads(jspage)
                    #print(key_json)
                    vkey = key_json['key']
                    url = '%s/%s?vkey=%s' % (parts_prefix, filename, vkey)
                    part_urls.append(url)
            except:
                pass

        else:
            fvkey = video_json['vl']['vi'][0]['fvkey']
            mp4 = video_json['vl']['vi'][0]['cl'].get('ci')
            if mp4:
                old_id = mp4[0]['keyid'].split('.')[1]
                new_id = 'p' + str(int(old_id) % 10000)
                mp4 = mp4[0]['keyid'].replace(old_id, new_id) + '.mp4'
            else:
                mp4 = video_json['vl']['vi'][0]['fn']
            url = '%s/%s?vkey=%s' % (parts_prefix, mp4, fvkey)
            part_urls.append(url)

    return part_urls, parts_ti


def videoparseX(vid):
    info_api = 'http://h5vv.video.qq.com/getinfo?vid=%s'
    info_api += '&defnpayver=1&appVer=3.0.52'
    info_api += '&defaultfmt=auto&defn=%s'
    info_api += '&otype=json&show1080p=1&isHLS=0&charge=0'
    info_api += '&sdtfrom=v1001&host=v.qq.com'
    if __addon__.getSetting('version') == '0':
        platform = '&platform=11'
    else:
        platform = '&platform=11'
    RESOLUTION = ['sd', 'hd', 'shd', 'fhd']
    sel = int(__addon__.getSetting('resolution'))
    if sel == 4:
        list = ['流畅(270P)', '高清(360P)', '超清(720P)', '蓝光(1080P)']
        sel = xbmcgui.Dialog().select('清晰度选择', list)
        if (sel < 0):
            return False, False

    jspage = GetHttpData(info_api % (vid, RESOLUTION[sel]) + platform)
    jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
    jsdata = json.loads(jspage)

    if jsdata['exem'] < 0:   # try again
        platform = '&platform=10901'
        jspage = GetHttpData(info_api % (vid, RESOLUTION[sel]) + platform)
        jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
        jsdata = json.loads(jspage)

    types = jsdata['fl']['fi']
    sel = min(sel, len(types) - 1)
    typeid = types[sel]['id']    # typeid: 10203 (int)
    format_sl = types[sel]['sl']   # sl
    js = jsdata['vl']['vi'][0]
    fvkey = js['fvkey']
    if fvkey == '':
        fvkey = open(cacheFile, 'r').read()
    else:
        open(cacheFile, 'w').write(fvkey)
    oldkey = fvkey

    title = js['ti']               # title in chinese
    filename = js['fn']           # filename 't0019fi7ura.p203.mp4'
    fc = js['cl']['fc']          # file counter
    preurl = js['ul']['ui']
    # url = []
    # for u in preurl:
    #     pattern = 'http://(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})'
    #     addr = re.compile(pattern).search(u['url'])
    #     if addr:
    #         url.append(u)

    # if len(url) > 0:
    #     server = url[0]['url']
    # else:
    #     server = videoparse(0)
    server = preurl[0]['url']
    urllist = []
    root = 'http://h5vv.video.qq.com/getkey?otype=json&sdtfrom=v1001&host=v.qq.com&vid=' + vid + platform
    lenfc = fc + 1
    if fc == 0:
        lenfc = 2
    for i in range(1, lenfc):
        file = filename.split('.')
        if fc != 0:
            file.insert(2, str(i))
            file[1] = 'p' + str(typeid % 10000)
        file = '.'.join(file)
        url = root + '&format=%d&filename=%s' % (typeid, file)
        html = GetHttpData(url)
        jspage = html[html.find('=')+1:-1]   # remove heading and tail
        jspage = json.loads(jspage)
        key = jspage.get('key', oldkey)
        app = '?vkey=%s&type=mp4' % key
        urllist.append(server + file + app)
        oldkey = key

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

    #urllist, title = qq_by_vid(vid)
    urllist, title = videoparseX(vid)
    if urllist is False:
        xbmcgui.Dialog().ok(__addonname__, '无法获取视频地址')
        return

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


def searchTencent(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    url = HOST_URL + '/x/search/?q=' + urllib.quote_plus(keyword)
    url += '&stag=0'

    link = GetHttpData(url)
    if link is None:
        li = xbmcgui.ListItem(' 抱歉，没有找到[COLOR FFFF0000] ' + keyword + '   [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.find_all('div', {'class': 'result_item'})
    for items in soup:
        href = httphead(items.a['href'])
        img = httphead(items.img['src'])
        title = items.img['alt']

        info = items.find('span', {'class': 'desc_text'})
        try:
            info = info.text
        except:
            info = ''

        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&title=' + title + '&thumb=' + img
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

        list = items.find_all('div', {'class': 'item'})
        for series in list:
            subtitle = series.a.text
            href = httphead(series.a['href'])
            li = xbmcgui.ListItem(subtitle)
            u = sys.argv[0] + '?url=' + href + '&mode=playvideo&title=' + subtitle
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

if mode is not None:
    del(params['mode'])

runlist = {
    None: 'mainMenu()',
    'mainlist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'otherlist': 'fashion(params)',
    'tedlist': 'tedFolders(params)',
    'tedalbum': 'tedAlbum(params)',
    'search': 'searchTencent(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo(params)'
}

eval(runlist[mode])
