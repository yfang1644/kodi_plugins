#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcgui
from urllib import quote_plus
import re
from json import loads
from bs4 import BeautifulSoup
from urlparse import urlparse
from common import get_html
from lib.sohu import video_from_url

from iqiyi import video_from_url as video_from_iqiyi
from qq import video_from_url as video_from_qq
from funshion import video_from_url as video_from_fun
from youku import video_from_url as video_from_youku

########################################################################
# 搜狐视频 tv.sohu.com
########################################################################

plugin = Plugin()
url_for = plugin.url_for

# Plugin constants
LIVEID_URL = 'http://live.tv.sohu.com/live/player_json.jhtml?lid=%s&type=1'
HOST_URL = 'https://tv.sohu.com'
LIST_URL = 'https://so.tv.sohu.com'
PROGRAM_URL = 'http://poll.hd.sohu.com/live/stat/menu-segment.jsonp?num=8&sid=%d'

BANNER_FMT = '[COLOR FFDEB887] %s [/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'
EXTRA = '[COLOR FF8080FF] %s[/COLOR]'


def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/playvideo/<url>')
def playvideo(url):
    level = int(plugin.addon.getSetting('resolution'))

    urls = video_from_url(url, level=level)

    if len(urls) < 1:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'), '节目暂不能播放')
        return

    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/playvideo_other/<url>/<site>')
def playvideo_other(url, site):
    if site == 'qq':
        resolver = video_from_qq
    elif site == 'fun':
        resolver = video_from_fun
    elif site == 'iqiyi':
        resolver = video_from_iqiyi
    elif site == 'youku':
        resolver = video_from_youku
    else:
        return

    urls = resolver(httphead(url))

    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/videolist/<name>/<url>')
def videolist(name, url):
    plugin.set_content('TVShows')
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')
    p10 = lurl[10]
    page = int(p10[3:]) if len(p10) > 3 else 1
    items = []
    items.append({
        'label': BANNER_FMT % ('【第%d页】(分类过滤)' % (page)),
        'path': url_for('select', name=name, url=url)
    })

    vlists = tree.find_all('ul', {'class': 'st-list'})
    lists = [] if len(vlists) == 0 else vlists[0].find_all('li')

    for item in lists:
        pic = item.find('div', {'class': 'st-pic'})
        href = pic.a.get('href')
        href = httphead(href)
        img = pic.img.get('src')
        img = httphead(img)
        try:
            hover = item.find('div', {'class': 'list-hover'})
            title = hover.a.text
        except:
            title = pic.img.get('alt')
        if len(title) == 0:
            title = pic.a.get('title', '')

        try:
            info = item.find('p', {'class': 'lh-info'}).text
        except:
            info = ''

        try:
            mask = item.find('span', {'class': 'maskTx'}).text
        except:
            mask = ''
        extra = ''
        auth = item.find('span', {'class': 'rl-hyuan'})
        if auth:
            extra += EXTRA % u'会员 '
        auth = item.find('span', {'class': 'rl-dbo'})
        if auth:
            extra += EXTRA % u'独播'

        if name in ('电视剧', '动漫', '综艺', '娱乐', '纪录片', '明星', '体育'):
            mode = 'episodelist1'
        elif name in ('搞笑', '游戏', '做饭', '科技', '学习考试', '自媒体'):
            mode = 'episodelist2'
        else:
            mode = 'playvideo'

        items.append({
            'label': title + ' ' + mask + extra,  
            'path': url_for(mode, url=href),
            'thumbnail': img,
            'is_playable': True if mode == 'playvideo' else False,
            'info': {'title': title, 'plot': info}
        })

    items.append({
        'label': INDENT_FMT0 % '分页',
        'path': url_for('stay')
    })

    pages = tree.find_all('div', {'class': 'ssPages area'})
    pages = [] if len(pages) == 0 else pages[0].find_all('a')
    for page in pages:
        items.append({
            'label': page['title'].encode('utf-8'),
            'path': url_for('videolist', name=name, url=httphead(page['href']))
        })
        
    return items


@plugin.route('/select/<name>/<url>')
def select(name, url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('dl', {'class': 'cfix'})

    dialog = xbmcgui.Dialog()

    surl = url.split('/')
    lurl = re.compile('(.+?).html').findall(surl[-1])
    lurl = lurl[0].split('_')

    for item in filter:
        title = item.dt.text.strip()
        si = item.find_all('a')
        list = []
        for x in si:
            if x.get('class') == ['aon']:
                list.append('[COLOR gold]' + x.text + '[/COLOR]')
            else:
                list.append(x.text)

        sel = dialog.select(title, list)

        if sel < 0:
            continue

        selurl = si[sel]['href'].split('/')
        selurl = re.compile('(.+?).html').findall(selurl[-1])
        selurl = selurl[0].split('_')
        for i in xrange(1, 14):
            if selurl[i] != 'p%d' % i:
                lurl[i] = selurl[i]

    surl[-1] = '_'.join(lurl) + '.html'
    url = '/'.join(surl)
    return videolist(name, url)


def sohuvideolist(playlistid):
    #listapi = 'http://hot.vrs.sohu.com/vrs_videolist.action?'
    #listapi = 'http://pl.hd.sohu.com/videolist?playlistid=9395603&order=0&cnt=1&withLookPoint=1&preVideoRule=1'
    listapi = 'http://pl.hd.sohu.com/videolist?playlistid=%s'

    link = get_html(listapi % playlistid, decoded=False)
    videos = loads(link.decode('gbk'))['videos']

    items = []
    for item in videos:
        p_name = item['showName'].encode('utf-8')
        p_thumb = item['largePicUrl'].encode('utf-8')
        p_url = item['pageUrl'].encode('utf-8')
        p_vid = str(item['vid']).encode('utf-8')
        p_tvId = str(item['tvId']).encode('utf-8')
        items.append({
            'label': p_name,
            'path': url_for('playvideo', url=p_url),
            'thumbnail': p_thumb,
            'is_playable': True,
            'info': {
                'title': p_name,
                'duration': int(item['playLength']),
                'plot': item['videoDesc'],
                'episode': int(item['order'])
            }
        })
    return items


def othersite(link):
    sitemap = {'qq': 'QQ', 'youku': '优酷', 'fun': '风行', 'iqiyi': '爱奇艺'}

    tree = BeautifulSoup(link, 'html.parser')
    soups = tree.findAll('div', {'class': 'episode cfix'})

    items = []
    for soup in soups:
        lists = soup.findAll('a')
        for item in lists:
            spliturl = urlparse(item['href'])
            site = spliturl.netloc.split('.')[1]
            try:
                siteinfo = sitemap[site]
            except:
                continue
            items.append({
                'label': item.text.encode('utf-8') + '(' + siteinfo + ')',
                'path': url_for('playvideo_other', url = item['href'], site=site),
                'is_playable': True,
                'info': {'title': item.text.encode('utf-8')}
            })
    return items


@plugin.route('/episodelist1/<url>')
def episodelist1(url):
    plugin.set_content('TVShows')
    link = get_html(url)

    match0 = re.compile('var playlistId\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)
    match0 += re.compile('var PLAYLIST_ID\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)

    items = []
    if len(match0) > 0:
        if match0[0] != '0':
            items = sohuvideolist(match0[0])
        else:
            items = othersite(link)
    else:
        tree = BeautifulSoup(link, 'html.parser')
        soup2 = tree.find_all('ul', {'class': 'list list-120 cfix'})

        for part in soup2:
            drama = part.find_all('li')

            for item in drama:
                img = httphead(item.img['src'])
                try:
                    title = item.strong.a['title']
                except:
                    title = item.a.text
                items.append({
                    'label': title,
                    'path': url_for('episodelist1', url=httphead(item.a['href'])),
                    'thumbnail': httphead(item.img['src'])
                })

    return items


@plugin.route('/episodelist2/<url>')
def episodelist2(url):
    plugin.set_content('TVShows')
    link = get_html(url)
    tree = BeautifulSoup(link, 'html.parser')

    listapi = 'http://my.tv.sohu.com/play/getvideolist.do?playlistid=%s&pagesize=30&order=1'

    match0 = re.compile('playlistId\s*=\s*["|\'](.+?)["|\'];', re.DOTALL).findall(link)

    link = get_html(listapi % match0[0])
    videos = loads(link)['videos']
    items = []
    for item in videos:
        length = item['playLength']
        p_date = item['publishTime'].encode('utf-8')
        p_order = int(item['order'])
        vid = item['vid']
        items.append({
            'label': item['subName'].encode('utf-8'),
            'path': url_for('playvideo', url=item['pageUrl']),
            'thumbnail': item['largePicUrl'],
            'is_playable': True,
            'info': {'title': item['subName'].encode('utf-8')},
        })

    return items


############################################################################
# Sohu 电视直播 Menu List
############################################################################
@plugin.route('/livechannel')
def livechannel():
    url ='http://tvimg.tv.itc.cn/live/stations.jsonp'
    link = get_html(url)
    link = link[link.find('=')+1: link.find(';channelList')]

    jsdata = loads(link)
    stations = jsdata['STATIONS']

    items = []
    for item in stations:
        title = item['STATION_NAME'].encode('utf-8')
        p_thumb = item['STATION_PIC']
        id = item['STATION_ID']
        p_thumb = httphead(p_thumb)
        if item['IsSohuSource'] == 1:
            disp_title = INDENT_FMT0 % title
        else:
            disp_title = INDENT_FMT1 % title

        html = get_html(PROGRAM_URL % id)
        try:
            program = loads(html)
        except:
            continue
        try:
            program = program['attachment'][0]['MENU_LIST']
        except:
            continue

        schedule = ''
        for s in program:
            schedule += '%s %s\n' % (s['START_TIME'], s['NAME'])
        items.append({
            'label': disp_title,
            'path': url_for('liveplay', station_id=id),
            'is_playable': True,
            'thumbnail': p_thumb,
            'info': {'title': disp_title, 'plot': schedule}
        })
    return items


############################################################################
# Sohu 电视直播 Player
############################################################################
@plugin.route('/liveplay/<station_id>')
def liveplay(station_id):
    link = get_html(LIVEID_URL % station_id)
    parsed_json = loads(link)
    url = httphead(parsed_json['data']['hls'])

    # link = get_html(url)
    # parsed_json = loads(link.decode('utf-8'))
    # url = parsed_json['url'].encode('utf-8')
    plugin.set_resolved_url(url)


###########################################################################
# Get user input for Sohu site search
############################################################################
@plugin.route('/search')
def search():
    plugin.set_content('TVShows')
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    p_url = 'http://so.tv.sohu.com/mts?chl=&tvType=-2&wd='
    url = p_url + quote_plus(keyword)

    # construct url based on user selected item
    page = 1
    p_url = url + '&fee=0&whole=1&m=1&box=1&p=%d' % page
    link = get_html(p_url)

    #########################################################################
    # Video listing for all found related episode title
    tree = BeautifulSoup(link, 'html.parser')
    soup = tree.find_all('div', {'class': 'ssItem cfix'})

    #########################################################################
    items = []
    for page in soup[0]:
        try:
            p_url = httphead(page.a['href'])
        except:
            continue
        p_name = page.a['title'].encode('utf-8')
        img = httphead(page.img['src'])
        infop = page.find('p', {'class': 'des'})
        try:
            info = infop.text
        except:
            info = ''
        items.append({
            'label': p_name,
            'path': url_for('episodelist1', url=p_url),
            'thumbnail': httphead(page.img['src']),
            'info': {'title': p_name, 'plot': info}
        })

        album = page.find_all('a', {'class': 'ts'})
        for series in album:
            items.append({
                'label': series['title'],
                'path': url_for('playvideo', url=httphead(series['href'])),
                'is_playable': True,
                'info': {'title': series['title']},
            })

    return items


@plugin.route('/')
def root():
    plugin.set_content('videos')
    yield {
        'label': '[COLOR FF00FF00] 【搜狐视频 - 搜索】[/COLOR]',
        'path': url_for('search')
    }
    yield {
        'label': u'电视直播',
        'path': url_for('livechannel')
    }

    url = '/list_p1_p2_p3_p4_p5_p6_p7_p8_p9_p10_p11_p12_p13.html'
    html = get_html(LIST_URL + url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'sort-nav cfix'})

    grp = soup[0].find_all('a')
    for prog in grp[1:]:
        title = prog.text.strip().encode('utf-8')
        yield {
            'label': title,
            'path': url_for('videolist', name=title, url=httphead(prog['href']))
        }


if __name__ == '__main__':
    plugin.run()
