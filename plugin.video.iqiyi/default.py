#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
import os
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from lib.iqiyi import video_from_vid, video_from_url, quote_plus, parse_qsl, urlencode

########################################################################
# 爱奇艺 list.iqiyi.com
########################################################################

LIST_URL = 'https://list.iqiyi.com'

ALBUM_API = 'https://pcw-api.iqiyi.com/albums/album/avlistinfo?aid={}&page=1&size=300'

__profile__   = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8'))

BANNER_FMT =  '[COLOR FFDEB887] (%s) [/COLOR]'
INDENT_FMT0 = '[COLOR   red]    %s[/COLOR]'
INDENT_FMT1 = '[COLOR green]    %s[/COLOR]'
RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url

def previous_page(endpoint, page, total_page, params):
    if int(page) > 1:
        li = ListItem('上一页 - {0}/{1}'.format(page, str(total_page)))
        params['mode'] = endpoint
        params['page'] = int(page) - 1
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def next_page(endpoint, page, total_page, params):
    if int(page) < int(total_page):
        li = ListItem('下一页 - {0}/{1}'.format(page, str(total_page)))
        params['mode'] = endpoint
        params['page'] = int(page) + 1
        u = sys.argv[0] + '?' + urlencode(params)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def convertTImer(info):
    try:
        duration = 0
        for t in info.split(':'):
            duration += duration*60 + int(t)
        return duration
    except:
        return info


def playvideo(params):
    name = params['name']
    thumbnail = params['thumbnail']
    tvId = params['tvId']
    vid = params['vid']
    level = int(xbmcaddon.Addon().getSetting('resolution'))
    m3u8set = xbmcaddon.Addon().getSetting('m3u8')
    playmode = True if m3u8set == 'true' else None
    urls = video_from_vid(tvId, vid, level=level, m3u8=playmode)
    if urls is None:
        Dialog().ok(xbmcaddon.Addon().getAddonInfo('name'), '无法播放此视频')
        return

    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    stackurl = 'stack://' + ' , '.join(urls)
    list_item = ListItem(name, thumbnailImage=thumbnail)
    list_item.setInfo('video', {'title': name})
    playlist.add(stackurl, list_item)
    xbmc.Player().play(playlist)


def playurl(params):
    url = params.pop('url')
    link = get_html(url)
    videoId = r1(r'#curid=.+_(.*)$', url) or \
            r1(r'vid=([^&]+)', url) or \
            r1(r'data-player-videoid="([^"]+)"', link) or \
            r1(r'vid=(.+?)\&', link) or \
            r1(r'param\[\'vid\'\]\s*=\s*"(.+?)"', link)
    params['vid'] = videoId
    playvideo(params)


def reference(params):
    tvId = params['tvId']
    thumbnail = params['thumbnail']
    # recommend

    li = ListItem(BANNER_FMT % params['name'], thumbnailImage=thumbnail)
    req = {
        'mode': 'playvideo',
        'tvId': tvId,
        'vid': params['vid'],
        'name': params['name'],
        'thumbnail': thumbnail
    }
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, False)

    url = 'http://mixer.video.iqiyi.com/jp/recommend/videos?referenceId=%s&area=swan&type=video' % tvId
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    videos = json_response['mixinVideos']
    for series in videos:
        if tvId == series['tvId']:
            mode, isFolder = 'playvideo', False
        else:
            mode, isFolder = 'reference', True
        
        li = ListItem(series['name'], thumbnailImage=series['imageUrl'])
        li.setInfo(type='Video', infoLabels={'title': series['name'], 'plot': series['description'], 'duration': series['duration']})
        req = {
            'mode': mode,
            'tvId': series.get('tvId'),
            'vid': series.get('vid', 0),
            'name': series['name'].encode('utf-8'),
            'thumbnail': series['imageUrl']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, isFolder)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def listType1(albumType, albumId):
    url = 'http://cache.video.qiyi.com/jp/sdvlst/%d/%d/' % (albumType, albumId)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    if 'data' not in json_response:
        return []

    for item in json_response['data']:
        li = ListItem(item['videoName'] + item['tvYear'], thumbnailImage=item['aPicUrl'])
        req = {
            'mode': 'playvideo',
            'tvId': item['tvId'],
            'vid': item['vid'],
            'name': item['videoName'].encode('utf-8'),
            'thumbnail': item['aPicUrl']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)


def listType2(albumId, page):
    url = 'http://cache.video.qiyi.com/avlist/%d/%s/50/' % (albumId, page)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    try:
        totalpages = json_response['data']['pgt']
    except:
        return

    currpage = int(page)

    for item in json_response['data']['vlist']:
        li = ListItem(item['vn']+' '+item['vt'], thumbnailImage=item['vpic'])
        li.setInfo(type='Video', infoLabels={'title': item['vn'], 'plot': item['desc'], 'duration': item['timeLength']})
        req = {
            'mode': 'playvideo',
            'tvId': item['id'],
            'vid': item['vid'],
            'name': item['vn'].encode('utf-8'),
            'thumbnail': item['vpic']
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)

    req = {
        'mode': 'episodelist',
        'albumId': albumId
    }
    if currpage > 1:
        li = ListItem('上一页')
        req['page'] = currpage - 1
    if currpage < totalpages:
        li = ListItem('下一页')
        req['page'] = currpage + 1
    u = sys.argv[0] + '?' + urlencode(req)
    addDirectoryItem(int(sys.argv[1]), u, li, True)


def episodelist(params):
    albumId = params['albumId']
    page = params['page']
    url = 'http://cache.video.qiyi.com/a/%s' % albumId

    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    item = json_response['data']
    p_year = item.get('tvYear', '0')
    p_director = ' / '.join(item['directors'])
    p_cast = [x for x in item['mainActors']]
    info = item['tvDesc']
    albumType = item['albumType']
    albumId = item['albumId']
    tvId = item['tvId']
    vid = item['vid']
    title = item['tvName'].encode('utf-8')
    isSeries = item['isSeries']
    if isSeries == 0:
        img = item.get('tvPictureUrl', '')
        li = ListItem(BANNER_FMT % title, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'title': title, 'plot': item['tvDesc']})
        req = {
            'mode': 'playvideo',
            'tvId': tvId,
            'vid': vid,
            'name': title,
            'thumbnail': img
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)
    else:
        listType1(albumType, albumId)
        listType2(albumId, page)

    # recommend
    req = {
        'tvId': tvId,
        'vid': vid,
        'name': title,
        'thumbnail': ''
    }
    reference(req)


def playfound(params):
    url = params['url']
    thumbnail = params['thumbnail']
    name = params['name']
    if url[0:4] != 'http':
        return

    link = get_html(url)
    tvId = r1(r'param\[\'tvid\'\]\s*=\s*"(.+)"', link)
    vid = r1(r'param\[\'vid\'\]\s*=\s*"(.+)"', link)
    if tvId is not None and vid is not None:
        li = ListItem(title, thumbnailImage=thumbnail)
        req = {
            'mode': 'playvideo',
            'tvId': tvId,
            'vid': vid,
            'name': name,
            'thumbnail': thumbnail
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, False)
    else:
        albumId = r1('albumid="(.+?)"', link)
        if albumId is not None:
            episodelist({'albumId': albumId, 'page':1})


###########################################################################
# search in http://so.iqiyi.com/so/q_%s?source=hot
############################################################################
def search(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1000)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    key = quote_plus(keyword)
    url = 'http://so.iqiyi.com/so/q_' + key + '?source=hot'
    link = get_html(url)

    if link is None:
        li =  ListItem('抱歉，没有找到[COLOR yellow] ' + keyword + ' [/COLOR]的相关视频')
        addDirectoryItem(int(sys.argv[1]), sys.argv[0], li, True)
        return

    li =  ListItem('[COLOR yellow]当前搜索:(' + keyword + ')[/COLOR]')
    addDirectoryItem(int(sys.argv[1]), sys.argv[0], li, True)

    # fetch and build the video series episode list
    soup = BeautifulSoup(link, 'html.parser')
    tree = soup.findAll('ul', {'class': 'mod_result_list'})
    for item in tree:
        lists = item.findAll('li', {'class': 'list_item'})
        for series in lists:
            img = series.img.get('src', '')
            img = httphead(img)
            title = series.img.get('title') or series.a.get('title')
            if title is None:
                continue
            text = series.find('span', {'class': 'result_info_txt'})
            try:
                info = text.text
            except:
                info = ''
            site = series.findAll('em', {'class': 'vm-inline'})
            for t in site:
                title += ' |' + t.text

            li = ListItem(title, thumbnailImage=img)
            li.setInfo(type='Video', infoLabels={'title': title, 'plot': info})
            req = {
                'mode': 'playfound',
                'url': httphead(series.a['href']),
                'name': title.encode('utf-8'),
                'thumbnail': img
            }
            u = sys.argv[0] + '?' + urlencode(req)
            addDirectoryItem(int(sys.argv[1]), u, li, True)

            album = series.findAll('li', {'class': 'album_item'})
            for page in album:
                title = page.a.get('title', '')
                li = ListItem('--' + title, thumbnailImage=img)
                req = {
                    'mode': 'playfound',
                    'url': page.a.get('href'),
                    'name': title.encode('utf-8'),
                    'thumbnail': img
                }
                u = sys.argv[0] + '?' + urlencode(req)
                addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def filter(params):
    url = 'https://list.iqiyi.com/www/{}/-------------24-1-1-iqiyi--.html'
    #chninfo = 'https://pcw-api.iqiyi.com/search/category/categoryinfo?brand=IQIYI&channel_id={}&locale=zh'
    cid = params['cid']
    html = get_html(url.format(cid))

    dialog = Dialog()

    m = r1("category-list='(\[.+?\])'", html)
    data = loads(m)

    f = []
    tn = ''
    for item in data:
        lst = [x['name'] for x in item['child']]
        lst.insert(0, '全部')
        sel = dialog.select(item['name'], lst)
        if sel > 0:
            f += [str(item['child'][sel-1]['id']) + ';must']
            tn += '|' + item['child'][sel-1]['name']

    m = r1("my-year='(\{.+?\})'", html)
    data = loads(m)

    lst = [x['name'] for x in data['list']]
    sel = dialog.select('年份', lst)
    if sel >= 0:
        params['year'] = data['list'][sel]['id']
        tn += '|' + data['list'][sel]['name']

    m = r1("order-list='(\[.+?\])'", html)
    data = loads(m)

    lst = [x['name'] for x in data]
    sel = dialog.select('排序', lst)
    sel = max(sel, 0)
    params['order'] = data[sel]['id']
    tn += '|' + data[sel]['name']
    
    params['type'] = ','.join(f)
    params['page'] = '1'
    params['typename'] = tn.encode('utf-8')
    category(params)


def category(params):
    order = params.get('order', 24)    # 综合排序
    cid = params['cid']
    year = params.get('year', '')
    page = params.get('page', 1)
    type = params.get('type', '')
    typename = params.get('typename', '')

    li = ListItem('[COLOR FFDEB887][分类过滤  %s][/COLOR]' % typename)
    u = sys.argv[0] + '?mode=filter&' + urlencode(params)
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    PCW_API = 'https://pcw-api.iqiyi.com/search/video/videolists?'
    req = {
        'access_play_control_platform': 14,
        'channel_id': cid,
        'data_type': 2 if cid=='16' else 1,
        'from': 'pcw_list',
        'is_album_finished': '',
        'is_purchase': '',
        'key': '',
        'market_release_date_level': year,
        'mode': order,
        'pageNum': page,
        'pageSize': 30,
        'site': 'iqiyi',
        'source_type': '',
        'three_category_id': type,
        'without_qipu': 1
    }

    api = PCW_API + urlencode(req)
    jdata = loads(get_html(api))
    total_page = jdata['data']['pageTotal']

    previous_page('category', page, total_page, params=params)
    for item in jdata['data']['list']:
        albumId = item.get('albumId')
        tvId = item.get('tvId')
        extra = item.get('videoCount', '')
        if extra:
            extra =  BANNER_FMT % extra
        duration = item.get('duration', 0)
        duration = convertTImer(duration)
        li = ListItem(item['name'] + extra, thumbnailImage=item['imageUrl'])
        li.setInfo(type='Video', infoLabels={'title': item['name'],'plot':item.get('description'), 'duration': duration})
        if albumId:
            req = {
                'mode': 'episodelist',
                'albumId': albumId,
                'page': 1
            }
            isFolder = True
        elif tvId:
            req = {
                'mode': 'playurl',
                'tvId': tvId,
                'url': item['playUrl'],
                'name': item['name'].encode('utf-8'),
                'thumbnail': item['imageUrl']
            }
            isFolder = False
        else:
            req = {
                'mode': 'playfound',
                'url': item['playUrl'],
                'name': item['name'].encode('utf-8'),
                'thumbnail': item['imageUrl']
            }
            isFolder = True
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, isFolder)

    next_page('category', page, total_page, params=params)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


def root():
    li = ListItem('[COLOR yellow] 【爱奇艺 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    html = get_html(LIST_URL)
    m = r1("channel-list='(\[.+?\])'", html)
    channels = loads(m)
    for channel in channels:
        li = ListItem(channel['name'])
        req = {
            'mode': 'category',
            'cid': channel['cid'],
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
runlist = {
    'category': 'category(params)',
    'episodelist': 'episodelist(params)',
    'playfound': 'playfound(params)',
    'reference': 'reference(params)',
    'search': 'search(params)',
    'filter': 'filter(params)',
    'playurl': 'playurl(params)',
    'playvideo': 'playvideo(params)'
}

params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')
if mode:
    del (params['mode'])
    exec(runlist[mode])
else:
    root()
