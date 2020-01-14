#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmc, xbmcgui
from xbmcgui import ListItem
from urllib import quote_plus
import re
import os
from json import loads
from bs4 import BeautifulSoup
from common import get_html, r1
from lib.iqiyi import video_from_vid

########################################################################
# 爱奇艺 list.iqiyi.com
########################################################################

plugin = Plugin()
url_for = plugin.url_for
LIST_URL = 'http://list.iqiyi.com'
PCW_API = 'https://pcw-api.iqiyi.com/search/video/videolists?channel_id={}&mode={}&pageNum={}&pageSize=30&without_qipu=1&is_purchase=0'

PCW_API = 'https://pcw-api.iqiyi.com/search/video/videolists?access_play_control_platform=14&channel_id={}&data_type=1&from=pcw_list&is_album_finished=&is_purchase=&key=&market_release_date_level=&mode={}&pageNum={}&pageSize=48&site=iqiyi&source_type=&three_category_id=15\;must&without_qipu=1'

ALBUM_API = 'https://pcw-api.iqiyi.com/albums/album/avlistinfo?aid={}&page=1&size=300'


__profile__   = xbmc.translatePath(plugin.addon.getAddonInfo('profile'))
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
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def convertTImer(info):
    try:
        duration = 0
        for t in info.split(':'):
            duration += duration*60 + int(t)
        return duration
    except:
        return info


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/playvideo/<tvId>/<vid>/<title>/<pic>/')
def playvideo(tvId, vid, title, pic):
    sel = int(plugin.addon.getSetting('resolution'))
    m3u8set = plugin.addon.getSetting('m3u8')
    playmode = True if m3u8set == 'true' else None
    playmode = None
    urls = video_from_vid(tvId, vid, level=sel,
                          m3u8=playmode, m3u8file=__m3u8__)
    if urls is None:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'), '无法播放此视频')
        return

    if len(urls) > 1:
        stackurl = 'stack://' + ' , '.join(urls)
    else:
        stackurl = urls[0]
    list_item = xbmcgui.ListItem(title, thumbnailImage=pic)
    list_item.setInfo('video', {'title': title})
    xbmc.Player().play(stackurl, list_item)

    #plugin.set_resolved_url(stackurl)


@plugin.route('/reference/<tvId>/<vid>/<title>/<pic>/')
def reference(tvId, vid, title, pic):
    plugin.set_content('TVShows')
    # recommend
    items = []
    items.append({
        'label': BANNER_FMT % title,
        'path': url_for('playvideo', tvId=tvId, vid=vid,
                        title=title, pic=pic),
        'is_playable': True,
        'info': {'title': title}
    })

    url = 'http://mixer.video.iqiyi.com/jp/recommend/videos?referenceId=%s&area=swan&type=video' % tvId
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    videos = json_response['mixinVideos']
    for series in videos:
        if tvId == series['tvId']:
            mode, playable = 'playvideo', True
        else:
            mode, playable = 'reference', False

        items.append({
            'label': series['name'],
            'path': url_for(mode, tvId=series.get('tvId'),
                            vid=series.get('vid', 0),
                            title=series['name'].encode('utf-8'),
                            pic=series['imageUrl']),
            'thumbnail': series['imageUrl'],
            'is_playable': playable,
            'info': {'title': series['name'],
                     'plot': series['description'],
                     'duration': series['duration']}
        })
    return items


def listType1(albumType, albumId):
    url = 'http://cache.video.qiyi.com/jp/sdvlst/%d/%d/' % (albumType, albumId)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    items = []
    if 'data' not in json_response:
        return []

    for item in json_response['data']:
        items.append({
            'label': item['videoName'] + item['tvYear'],
            'path': url_for('playvideo',
                            tvId=item['tvId'],
                            vid=item['vid'],
                            title=item['videoName'].encode('utf-8'),
                            pic=item['aPicUrl']),
            'thumbnail': item['aPicUrl'],
            'is_playable': True,
            'info': {'title': item['videoName']}
        })

    return items


def listType2(albumId, page):
    url = 'http://cache.video.qiyi.com/avlist/%d/%s/50/' % (albumId, page)
    link = get_html(url)
    data = link[link.find('=')+1:]
    json_response = loads(data)
    items = []
    try:
        totalpages = json_response['data']['pgt']
    except:
        return items

    currpage = int(page)

    for item in json_response['data']['vlist']:
        items.append({
            'label': item['vn'] + ' ' + item['vt'],
            'path': url_for('playvideo',
                            tvId=item['id'],
                            vid=item['vid'],
                            title=item['vn'].encode('utf-8'),
                            pic=item['vpic']),
            'thumbnail': item['vpic'],
            'is_playable': True,
            'info': {'title': item['vn'], 'plot': item['desc'], 'duration': item['timeLength']}
        })

    if currpage > 1:
        items.append({
            'label': '上一页',
            'path': url_for('episodelist', albumId=albumId, page=currpage-1),
        })
    if currpage < totalpages:
        items.append({
            'label': '下一页',
            'path': url_for('episodelist', albumId=albumId, page=currpage+1),
        })

    return items


@plugin.route('/episodelist/<albumId>/<page>/')
def episodelist(albumId, page):
    plugin.set_content('TVShows')
    url = 'http://cache.video.qiyi.com/a/%s' % albumId
    items = []
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
        items.append({
            'label': BANNER_FMT % title,
            'path': url_for('playvideo', tvId=tvId, vid=vid, title=title,
                           pic=item.get('tvPictureUrl','0')),
            'thumbnail': item.get('tvPictureUrl', ''),
            'is_playable': True,
            'info': {'title': title, 'plot': item['tvDesc']}
        })
    else:
        item1 = listType1(albumType, albumId)
        items += item1
        if not item1:
           items += listType2(albumId, page)

    # recommend
    items += reference(tvId, vid, title, 'xxxx')
    if len(items) > 1 and items[0]['label'] == items[1]['label']:
        del items[1]
    return items


@plugin.route('/playfound/<url>/<title>/<pic>/')
def playfound(url, title, pic):
    items = []
    if not url.startswith('http'):
        return []

    link = get_html(url)
    tvId = r1(r'param\[\'tvid\'\]\s*=\s*"(.+)"', link)
    vid = r1(r'param\[\'vid\'\]\s*=\s*"(.+)"', link)
    if tvId is not None and vid is not None:
        items = [{
            'label': title,
            'path': url_for('playvideo', tvId=tvId, vid=vid,
                            title=title, pic=pic),
            'is_playable': True,
            'info': {'title': title}
        }]
    else:
        albumId = r1('albumid="(.+?)"', link)
        if albumId is not None:
            items = episodelist(albumId, 1)
    return items


@plugin.route('/filter/<url>/')
def filter(url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    filter = tree.find_all('div', {'class': 'mod_sear_list'})

    surl = url.split('/')
    lurl = surl[-1].split('-')

    dialog = xbmcgui.Dialog()

    for item in filter[1:]:
        title = item.h3.text
        si = item.find_all('li')
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
    return videolist(httphead(url))


###########################################################################
# search in http://so.iqiyi.com/so/q_%s?source=hot
############################################################################
@plugin.route('/search/')
def search():
    items = []
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1000)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return []

    keyword = keyboard.getText()
    key = quote_plus(keyword)
    url = 'http://so.iqiyi.com/so/q_' + key + '?source=hot'
    link = get_html(url)

    if link is None:
        items.append({
            'label':' 抱歉，没有找到[COLOR yellow] ' + keyword + ' [/COLOR]的相关视频',
            'path': url_for('stay')
        })
        return items

    plugin.set_content('TVShows')
    items.append({
        'label': '[COLOR yellow]当前搜索:(' + keyword + ')[/COLOR]',
        'path': url_for('stay')
    })

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.find_all('ul', {'class': 'mod_result_list'})
    for item in soup:
        lists = item.find_all('li', {'class': 'list_item'})
        for series in lists:
            img = series.img.get('src', '')
            title = series.img.get('title') or series.a.get('title')
            if title is None:
                continue
            text = series.find('span', {'class': 'result_info_txt'})
            try:
                info = text.text
            except:
                info = ''
            site = series.find_all('em', {'class': 'vm-inline'})
            for t in site:
                title += ' |' + t.text
            items.append({
                'label': title,
                'path': url_for('playfound',
                                url=httphead(series.a['href']),
                                title=title.encode('utf-8'),
                                pic=httphead(img)),
                'thumbnail': httphead(img),
                'info': {'title': title, 'plot': info}
            })

            album = series.find_all('li', {'class': 'album_item'})
            for page in album:
                title = page.a.get('title', '')
                items.append({
                    'label': '--' + title,
                    'path': url_for('playfound',
                                    url=page.a.get('href'),
                                    title=title.encode('utf-8'),
                                    pic=img),
                    'thumbnail': img,
                    'info': {'title': title}
                })
    return items


@plugin.route('/videolist/<url>/')
def videolist(url):
    plugin.set_content('TVShows')
    html = get_html(url)
    html = re.sub('\t|\r|\n', ' ', html)
    tree = BeautifulSoup(html, 'html.parser')

    ul = url.split('/')[-1]
    page = ul.split('-')[14]
    if page == '':
        page = '1'

    items = []
    items.append({
        'label': '[第%s页](分类过滤)' % page.encode('utf-8'),
        'path': url_for('filter', url=url)
    })

    items.append({
        'label': BANNER_FMT % '排序方式',
        'path': url_for('stay')
    })
    soup = tree.find_all('div', {'class': 'sort-result-l'})
    arrange = soup[0].find_all('a')
    for sort in arrange:
        title = sort.text.strip()
        select = sort.get('class', '')
        if 'selected' in select:
            title = INDENT_FMT1 % title
        else:
            title = INDENT_FMT0 % title
        items.append({
            'label': title,
            'path': url_for('videolist', url=httphead(sort['href']))
        })

    soup = tree.find_all('div', {'class': 'site-piclist_pic'})
    for item in soup:
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

        items.append({
            'label': title + extrainfo.strip(),
            'path': url_for('episodelist', albumId=albumId, page=1),
            'thumbnail': httphead(img),
            'info': infoLabels,
        })

    items.append({
        'label':INDENT_FMT0 % ('分页'),
        'path': url_for('stay')
    })

    pages = tree.find_all('div', {'class': 'mod-page'})
    pages = pages[0].find_all('a')
    for page in pages:
        items.append({
            'label': page.text,
            'path': url_for('videolist', url=httphead(page['href']))
        })
    return items


orderlist=[{"id":24,"name":"综合排序"},
           {"id":11,"name":"热播榜"},
           {"id":4,"name":"新上线"}]

@plugin.route('/category/<order>/<cid>/<page>/')
def category(order, cid, page):
    plugin.set_content('TVShows')
    items = []
    for x in orderlist:
        if int(x['id']) == int(order):
            style = '[COLOR red]{}[/COLOR]'.format(x['name'])
        else:
            style = '[COLOR yellow]{}[/COLOR]'.format(x['name'])
        items.append({
            'label': style,
            'path': url_for('category', order=x['id'], cid=cid, page=page)
        })

    api = PCW_API.format(cid, order, page)
    jdata = loads(get_html(api))
    items += previous_page('category', page, 300, order=order, cid=cid)
    for item in jdata['data']['list']:
        albumId=item.get('albumId')
        if albumId:
            items.append({
                'label': item['name'],
                'path': url_for('episodelist', albumId=albumId, page=1),
                'thumbnail': item['imageUrl'],
                'info': {'title': item['name'], 'plot': item.get('description')}
            })
        else:
            items.append({
                'label': item['name'],
                'path': url_for('playfound', url=item['playUrl'],
                                title=item['name'].encode('utf-8'),
                                pic=item['imageUrl']),
                'thumbnail': item['imageUrl'],
                'info': {'title': item['name'], 'plot': item.get('description')}
            })
    items += next_page('category', page, 300, order=order, cid=cid)
    return items

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


@plugin.route('/')
def index():
    yield {
        'label': '[COLOR yellow] 【爱奇艺 - 搜索】[/COLOR]',
        'path': url_for('search')
    }

    for channel in channellist:
        yield {
            'label': channel['name'],
            'path': url_for('category', order=24, cid=channel['cid'], page=1)
        }


if __name__ == '__main__':
    plugin.run()
