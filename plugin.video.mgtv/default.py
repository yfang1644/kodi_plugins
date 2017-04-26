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
import simplejson

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'

UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

LIST_URL = 'http://list.mgtv.com'
HOST_URL = 'http://www.mgtv.com'

RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if len(url) < 2:
        return url
    if url[:2] == '/b':
        url = HOST_URL + url
    elif url[0] == '/':
        url = LIST_URL + url

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
    return httpdata


def mainMenu():
    http = GetHttpData(LIST_URL)
    tree = BeautifulSoup(http, 'html.parser')
    soup = tree.find_all('div', {'class': 'm-catgory-listbox'})

    title0 = soup[0].span.text
    items = soup[0].find_all('li')
    for item in items:
        name = item.a.text
        href = httphead(item.a['href'])
        li = xbmcgui.ListItem(name)
        u = sys.argv[0] + '?url=' + urllib.quote_plus(href)
        u += '&mode=mainlist&name=' + name
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def changeList(params):
    url = params['url']
    name = params['name']
    filter = params.get('filter')

    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'm-catgory-listbox'})

    surl = url.split('/')
    purl = surl[-1].split('-')

    dialog = xbmcgui.Dialog()

    filter = ''
    for iclass in soup[1:]:
        title = iclass.find('span', {'class': 'u-meta'}).text
        si = iclass.find_all('a')
        list = []
        item = []
        for subitem in si:
            list.append(subitem.text)
            item.append(subitem['href'])
        sel = dialog.select(title, list)

        if sel < 0:
            continue

        filter += '|' + title + '(' + si[sel].text + ')'
        seurl = si[sel]['href'].split('/')[-1]
        seurl = seurl.split('-')
        for i in range(0, len(purl)):
            if seurl[i] != '':
                purl[i] = seurl[i]

    surl[-1] = '-'.join(purl)
    params['url'] = '/'.join(surl)
    params['filter'] = filter

    listSubMenu(params)


def listSubMenu(params):
    url = params['url']
    name = params['name']
    filter = params.get('filter', '')
    filter = filter.encode('utf-8')
    li = xbmcgui.ListItem(BANNER_FMT % (name + '[分类过滤]' + filter))
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url)
    u += '&mode=select&name=' + name
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = GetHttpData(url)
    tree = BeautifulSoup(html, 'html.parser')

    soup = tree.find_all('ul', {'class': 'v-list-inner'})
    items = soup[0].find_all('li')
    for item in items:
        thumb = item.img['src']
        t = item.find('a', {'class': 'u-title'})
        title = t.text
        href = t['href']
        t = item.find('a', {'class': 'u-video'})
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        try:
            exinfo = '(' + item.em.text + ')'
        except:
            exinfo =''

        pinfo = item.find('span', {'class': 'u-desc'})
        info = pinfo.text.replace(' ', '')
        li = xbmcgui.ListItem(title + exinfo,
                              iconImage=thumb, thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u += '&name=' + urllib.quote_plus(name)
        u += '&thumb=' + urllib.quote_plus(thumb)
        u += '&filter=' + urllib.quote_plus(filter)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # multiple pages
    setpage = tree.find_all('div', {'class': 'w-pages'})
    pages = setpage[0].find_all('li')

    for page in pages:
        try:
            title = page.a['title']
        except:
            continue
        href = page.a['href']
        if href == 'javascript:;':
            continue
        else:
            href = httphead(href)
        li = xbmcgui.ListItem(BANNER_FMT % title)
        u = sys.argv[0] + '?url=' + href + '&mode=mainlist'
        u += '&name=' + urllib.quote_plus(name)
        u += '&filter=' + urllib.quote_plus(filter)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    episode_api = 'http://pcweb.api.mgtv.com/episode/list?video_id=%s&page=1&size=50'
    url = params['url']
    id = url.split('/')[-1]
    id = re.compile('(\d+).html').findall(id)[0]
    html = GetHttpData(episode_api % id)
    jsdata = simplejson.loads(html)

    data = jsdata['data']
    list = data.get('list')
    for series in list:
        title = series['t1'] +' ' + series['t2']
        if series['isnew'] != '0':
            title = title + u'(预)'
        img = series['img']
        href = httphead(series['url'])
        vid = series['video_id']
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo&vid=' + vid
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    short = data.get('short')
    for series in short:
        title = series['t1'] + ' ' + series['t2']
        if series['isnew'] != '0':
            title = title + u'(预)'
        img = series['img']
        href = httphead(series['url'])
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo&vid=' + vid
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    related = data.get('related')
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_mgtv_real_url(url):
    """str->list of str
    Give you the real URLs."""
    content = simplejson.loads(GetHttpData(url))
    m3u_url = content['info']
    split = urlsplit(m3u_url)

    base_url = "{scheme}://{netloc}{path}/".format(scheme = split[0],
                                                   netloc = split[1],
                                                   path = dirname(split[2]))

    content = GetHttpData(content['info'])  #get the REAL M3U url, maybe to be changed later?
    segment_list = []
    segments_size = 0
    for i in content.split():
        if not i.startswith('#'):  #not the best way, better we use the m3u8 package
            segment_list.append(base_url + i)
            # use ext-info for fast size calculate
        elif i.startswith('#EXT-MGTV-File-SIZE:'):
            segments_size += int(i[i.rfind(':')+1:])

    return m3u_url, segments_size, segment_list


def playVideo(params):
    vid = params['vid']
    thumb = params['thumb']
    api_endpoint = 'http://pcweb.api.mgtv.com/player/video?video_id='
    html = GetHttpData(api_endpoint + vid)
    content = simplejson.loads(html)
    stream = content['data']['stream']

    title = content['data']['info']['title']
    domain = content['data']['stream_domain'][0]
    level = int(__addon__.getSetting('resolution'))
    if level == 4:
        level = 0

    purl = content['data']['stream'][level]['url']

    url = domain + re.sub(r'(\&arange\=\d+)', '', purl)  #Un-Hum
    content = simplejson.loads(GetHttpData(url))
    m3u_url = content['info']

    li = xbmcgui.ListItem(title, thumbnailImage=thumb)
    playlist = xbmc.Player().play(m3u_url, li)


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'mainlist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo(params)'
    }

eval(runlist[mode])
