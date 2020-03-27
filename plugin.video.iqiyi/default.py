#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, setContent
import xbmcaddon
import re
import os
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from lib.iqiyi import video_from_vid, video_from_url, quote_plus, parse_qsl, urlencode

########################################################################
# 爱奇艺 list.iqiyi.com
########################################################################

LIST_URL = 'http://list.iqiyi.com'
PCW_API = 'https://pcw-api.iqiyi.com/search/video/videolists?channel_id={}&mode={}&pageNum={}&pageSize=30&without_qipu=1&is_purchase=0'

PCW_API = 'https://pcw-api.iqiyi.com/search/video/videolists?channel_id={}&data_type=1&from=pcw_list&is_album_finished=&is_purchase=&key=&market_release_date_level=&mode={}&pageNum={}&pageSize=30&site=iqiyi&source_type=&three_category_id=&without_qipu=1'

ALBUM_API = 'https://pcw-api.iqiyi.com/albums/album/avlistinfo?aid={}&page=1&size=300'

__profile__   = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
__m3u8__      = xbmc.translatePath(os.path.join(__profile__, 'temp.m3u8'))

BANNER_FMT =  '[COLOR FFDEB887][%s][/COLOR]'
INDENT_FMT0 = '[COLOR   red]    %s[/COLOR]'
INDENT_FMT1 = '[COLOR green]    %s[/COLOR]'
RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        li = ListItem('上一页 - {0}/{1}'.format(page, str(total_page)))
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) - 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        li = ListItem('下一页 - {0}/{1}'.format(page, str(total_page)))
        kwargs['mode'] = endpoint
        kwargs['page'] = int(page) + 1
        u = sys.argv[0] + '?' + urlencode(kwargs)
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
    items = []
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


def filter(params):
    url = params['url']
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.findAll('div', {'class': 'mod_sear_list'})

    surl = url.split('/')
    lurl = surl[-1].split('-')

    dialog = Dialog()

    for item in filter[1:]:
        title = item.h3.text
        si = item.findAll('li')
        list = []
        for x in si:
            if x.get('class') and 'selected' in x.get('class'):
                list.append('[COLOR FFF0F000]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel].a['href'].split('/')
        selurl = selurl[-1].split('-')
        if len(selurl) < 10:
            continue
        for i in xrange(len(selurl)):
            if (selurl[i] != '') and (selurl[i] != lurl[i]):
                lurl[i] = selurl[i]

    surl[-1] = '-'.join(lurl)
    url = '/'.join(surl)
    videolist({'url': httphead(url)})


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


def videolist(params):
    html = get_html(url)
    html = re.sub('\t|\r|\n', ' ', html)
    soup = BeautifulSoup(html, 'html.parser')

    ul = url.split('/')[-1]
    page = ul.split('-')[14]
    if page == '':
        page = '1'


    li = ListItem('[第%s页](分类过滤)' % page.encode('utf-8'))
    u = sys.argv[0] + '?mode=filter&url=' + url
    addDirectoryItem(int(sys.argv[1]), u, li, True)
    
    li = ListItem(BANNER_FMT % '排序方式')
    addDirectoryItem(int(sys.argv[1]), sys.argv[0], li, True)

    tree = soup.findAll('div', {'class': 'sort-result-l'})
    arrange = tree[0].findAll('a')
    for sort in arrange:
        title = sort.text.strip()
        select = sort.get('class', '')
        if 'selected' in select:
            title = INDENT_FMT1 % title
        else:
            title = INDENT_FMT0 % title
        li = ListItem(title)
        u = sys.argv[0] + '?mode=videolist&url=' + httphead(sort['href'])
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    tree = soup.findAll('div', {'class': 'site-piclist_pic'})
    for item in tree:
        href = item.a.get('href')
        img = item.img.get('src', '')
        title = item.a.get('title', '')
        try:
            info = item.find('span', {'class': 'icon-vInfo'}).text
        except:
            info = ''
        info = convertTImer(info)
        try:
            vip = item.find('span', {'class': 'icon-vip-zx'}).text
            vip = '|[COLOR FF809000]' + vip + '[/COLOR]'
        except:
            vip = ''
        try:
            pay = item.find('span', {'class': 'icon-vip-quan'}).text
            pay = '|[COLOR FF809000]' + pay + '[/COLOR]'
        except:
            pay = ''
        albumId = item.a.get('data-qidanadd-albumid')
        if albumId is None:
            albumId = item.a.get('data-qidanadd-tvid', 'X')
        extrainfo = vip + pay
        if isinstance(info, str):
            extrainfo = info + extrainfo
        if isinstance(info, str):
            infoLabels={'title': title, 'plot': info}
        else:
            infoLabels={'title': title, 'duration': info}

        li = ListItem(title + extrainfo.strip(), thumbnailImage=httphead(img))
        li.setInfo(type='Video', infoLabels=infoLabels)
        req = {
            'mode': 'episodelist',
            'albumId': albumId,
            'page': 1
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    li = ListItem(INDENT_FMT0 % '分页')
    addDirectoryItem(int(sys.argv[1]), sys.argv[0], li, True)

    pages = soup.findAll('div', {'class': 'mod-page'})
    pages = pages[0].findAll('a')
    for page in pages:
        li = ListItem(page.txt)
        u = sys.argv[0] + '?mode=videolist&url=' + httphead(page['href'])
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


orderlist=[{"id":24,"name":"综合排序"},
           {"id":11,"name":"热播榜"},
           {"id":4,"name":"新上线"}]

def category(params):
    order = params['order']
    cid = params['cid']
    page = params['page']
    items = []
    for x in orderlist:
        if int(x['id']) == int(order):
            style = '[COLOR red]{}[/COLOR]'.format(x['name'])
        else:
            style = '[COLOR yellow]{}[/COLOR]'.format(x['name'])
        li = ListItem(style)
        req = {
            'mode': 'category',
            'order': x['id'],
            'cid': cid,
            'page': page
        }
        u = sys.argv[0] + '?' + urlencode(req)
        addDirectoryItem(int(sys.argv[1]), u, li, True)

    api = PCW_API.format(cid, order, page)
    if cid == '16':
        api = api.replace('data_type=1', 'data_type=2')
    jdata = loads(get_html(api))
    total_page = jdata['data']['pageTotal']

    previous_page('category', page, total_page, order=order, cid=cid)
    for item in jdata['data']['list']:
        albumId = item.get('albumId')
        tvId = item.get('tvId')
        duration = item.get('duration', 0)
        duration = convertTImer(duration)
        li = ListItem(item['name'], thumbnailImage=item['imageUrl'])
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

    next_page('category', page, total_page, order=order, cid=cid)

    setContent(int(sys.argv[1]), 'tvshows')
    endOfDirectory(int(sys.argv[1]))


channellist=[{"cid":2,"name":"电视剧"},
             {"cid":1,"name":"电影"},
             {"cid":6,"name":"综艺"},
             {"cid":4,"name":"动漫"},
             {"cid":3,"name":"纪录片"},
             {"cid":8,"name":"游戏"},
             {"cid":25,"name":"资讯"},
             {"cid":7,"name":"娱乐"},
             {"cid":24,"name":"财经"},
             {"cid":16,"name":"网络电影"},
             {"cid":10,"name":"片花"},
             {"cid":5,"name":"音乐"},
             {"cid":28,"name":"军事"},
             {"cid":12,"name":"教育"},
             {"cid":17,"name":"体育"},
             {"cid":15,"name":"儿童"},
             {"cid":9,"name":"旅游"},
             {"cid":13,"name":"时尚"},
             {"cid":21,"name":"生活"},
             {"cid":26,"name":"汽车"},
             {"cid":22,"name":"搞笑"},
             {"cid":20,"name":"广告"},
             {"cid":27,"name":"原创"},
             {"cid":29,"name":"母婴"},
             {"cid":30,"name":"科技"},
             {"cid":31,"name":"脱口秀"},
             {"cid":32,"name":"健康"}]

def root():
    li = ListItem('[COLOR yellow] 【爱奇艺 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    addDirectoryItem(int(sys.argv[1]), u, li, True)

    for channel in channellist:
        li = ListItem(channel['name'])
        req = {
            'mode': 'category',
            'order': 24,
            'cid': channel['cid'],
            'page': 1
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
