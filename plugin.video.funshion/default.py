#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from bs4 import BeautifulSoup
from json import loads
from common import get_html, r1
from lib.funshion import video_from_url, video_from_vid

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
EXTRA = '[COLOR FF8080FF]%s[/COLOR]'

HOST_URL = 'http://www.fun.tv'

profile_m = 'http://pm.funshion.com/v5/media/profile?id={}'

########################################################################
# 风行视频(Funshion)"
########################################################################

# Plugin constants

RES_LIST = [['tv', '低清'],
            ['dvd', '标清'],
            ['high-dvd', '高清'],
            ['super_dvd', '超清']]

plugin = Plugin()
url_for = plugin.url_for


def httphead(url):
    if url[0:2]=='//':
        url = 'http:' + url
    elif url[0]=='/':
        url = HOST_URL + url

    return url

##############################################################################
# Routine to update video list as per user selected filtrs
##############################################################################
@plugin.route('/stay')
def stay():
    pass


##############################################################################
@plugin.route('/playvideo/<url>/')
def playvideo(url):
    resolution = int(plugin.addon.getSetting('resolution'))
    if resolution == 4:
        list = [x[1] for x in RES_LIST]
        sel = xbmcgui.Dialog().select('清晰度', list)
        resolution = 2 if sel < 0 else sel    # set default

    v_urls = video_from_url(url, level=resolution)
    if len(v_urls) > 0:
        plugin.set_resolved_url(v_urls[0])
    else:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '没有可播放的视频')


@plugin.route('/filter/<url>/')
def filter(url):
    surl = url.split('/')
    purl = surl[-2].split('.')

    for x in purl:
        if x[0] == 'c':
            ctype = x
            break

    html = get_html(url + '?isajax=1')
    data = loads(html)
    fl = data['data']['data']['navs'][1:]
    dialog = xbmcgui.Dialog()

    select = []
    for item in fl:
        type = item['value']
        dlist, val = [], []
        for subitem in item['nitems']:
            url1 = subitem['url'].split('/')[-2]
            types = url1.split('.')
            for x in types:
                if type == x[0]:
                    val += [x]
                    break
            dlist += [subitem['name']]

        sel = dialog.select(item['title'], dlist)
        if sel >= 0:
            select += [val[sel]]
        else:
            return mainlist(url)

    select.insert(0, ctype)
    surl[-2] = '.'.join(select)
    url = '/'.join(surl)
    return mainlist(url)


def playList(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    lists = soup.find_all('a', {'class': 'vd-list-item'})

    if lists is None:
        return []

    items = []
    for item in lists:
        p_thumb = item.img.get('src')
        if p_thumb is None:
            p_thumb = item.img.get('_lazysrc', '')
        d = item.find('i', {'class': 'vtime'})
        duration = 0
        for t in d.text.split(':'):
            duration = duration * 60 + int(t)
        items.append({
            'label': item['title'],
            'path': url_for('playvideo', url=httphead(item['href'])),
            'thumbnail': p_thumb,
            'is_playable': True,
            'info': {'title': item['title'], 'duration': duration}
        })

    return items


def relatedList(url):
    epid = r1('http?://www.fun.tv/vplay/.*g-(\w+)', url)
    if not epid:
        epid = r1('http?://www.fun.tv/vplay/v-(\w+)', url)

    # rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/media?isajax=1'
    # rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/video?isajax=1'
    rel_api = 'http://pm.funshion.com/v6/media/relate?id=%s'
    link = get_html(rel_api % epid)
    jsdata = loads(link)

    relates = jsdata['relates']
    items = []

    for x in relates:
        items.append({
            'label': BANNER_FMT % x['name'],
            'path': url_for('stay')
        })
        for y in x['contents']:
            pic = y['poster'] if y['poster'] else y['still']
            info = {}
            dur = y.get('duration', '0:0')
            duration = 0
            for t in dur.split(':'):
                duration = duration * 60 + int(t)
            items.append({
                'label': y['name'],
                'thumbnail': pic,
                'info': {'title': y['name'], 'plot': y['aword'], 'duration': duration}
                })

            if ['template'] == 'vplay':
                items[-1]['path'] = url_for('playvideo',
                                            url=httphead('/vplay/v-' + y['id']))
                items[-1]['is_playable'] = True
            else:
                items[-1]['path'] = url_for('albumlist',
                                            url=httphead('/vplay/g-' + y['id']))

    return items

##########################################################################
def seriesList(url):
    html = get_html(url + '?isajax=1')
    data = loads(html)

    items = []

    gvideos = data['data']['play_lists']['dvideos'][0]['videos']
    infos = data['data']['share']

    try:
        videos = []
        for x in gvideos:
            videos += x['lists']
    except:
        videos = gvideos

    for item in videos:
        d = item.get('duration', '0:0')
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration*60 + int(t)
        items.append({
            'label': item['name'],
            'path': url_for('playvideo', url=httphead(item['url'])),
            'thumbnail': item.get('pic') or infos['pic'],
            'is_playable': True,
            'info': {'title': item['name'], 'duration': duration,
                     'plot': infos['desc']}
        })
    return items

@plugin.route('/albumlist/<url>/')
def albumlist(url):
    plugin.set_content('TVShows')
    vid = r1('http?://www.fun.tv/vplay/v-(\w+)', url)
    epid = r1('http?://www.fun.tv/vplay/.*g-(\w+)', url)
    items = []
    if vid:
        items += playList(url)    # play single video
    elif epid:
        items += seriesList(url)     # list series

    # add some related videos
    items += relatedList(url)
    return items


@plugin.route('/mainlist/<url>/')
def mainlist(url):
    plugin.set_content('TVShows')
    html = get_html(url + '?isajax=1')

    data = loads(html)

    yield {
        'label': '[选择过滤]',
        'path': url_for('filter', url=url)
    }

    for item in data['data']['data']['ritems']:
        info = item.get('update_info')
        if info:
            extra = EXTRA % ('(' + info +')')
        else: extra = ''
        yield {
            'label': item['title'] + extra,
            'path': url_for('albumlist', url=httphead(item['url'])),
            'thumbnail': item['pic'],
            'info': {'title': item['title'], 'plot': item.get('desc')},
        }

    # Construct page selection
    pages = data['data']['page']
    soup = BeautifulSoup(pages, 'html.parser')
    pages = soup.findAll('a')
    for page in pages:
        href = page['href']
        if href == '###':
            continue
        yield {
            'label': page.text,
            'path': url_for('mainlist', url=httphead(href))
        }


@plugin.route('/')
def index():
    html = get_html(HOST_URL + '/retrieve/?isajax=1')
    data = loads(html)

    for item in data['data']['data']['navs'][0]['nitems']:
        yield {
            'label': item['name'],
            'path': url_for('mainlist', url=httphead(item['url']))
        }


if __name__ == '__main__':
    plugin.run()
