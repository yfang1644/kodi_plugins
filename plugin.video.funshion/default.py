#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from bs4 import BeautifulSoup
from json import loads
from common import get_html, r1
from lib.funshion import video_from_url

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

LANG_LIST = [['chi','国语'], ['arm','粤语'], ['und','原声']]

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


@plugin.route('/vfilters/<url>/')
def vfilters(url):
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
    tree = BeautifulSoup(html, 'html.parser')

    lists = tree.find_all('a', {'class': 'vd-list-item'})

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
            dur = y.get('duration')
            if dur:
                duration = 0
                for t in dur.split(':'):
                    duration = duration * 60 + int(t)
                info['duration'] = duration
            info['tltle'] = y['name']
            info['plot'] = y['aword']
            if y['template'] == 'vplay':
                items.append({
                    'label': y['name'],
                    'path': url_for('playvideo',
                                    url=HOST_URL + '/vplay/v-' + y['id']),
                    'thumbnail': pic,
                    'is_playable': True,
                    'info': info
                })
            else:
                items.append({
                    'label': y['name'],
                    'path': url_for('albumlist',
                                    url=HOST_URL + '/vplay/g-' + y['id']),
                    'thumbnail': pic,
                    'info': info
                })
    return items


def singleVideo(url):
    items = playList(url)
    items += relatedList(url)
    return items


##########################################################################
def seriesList(url):
    epid = r1('http?://www.fun.tv/vplay/.*g-(\w+)', url)
    # url = 'http://api.funshion.com/ajax/get_web_fsp/%s/mp4?isajax=1'
    purl = 'http://api.funshion.com/ajax/vod_panel/%s/w-1?isajax=1'  #&dtime=1397342446859
    link = get_html(purl % epid)
    intro = loads(get_html(profile_m.format(epid)))
    poster = intro['poster'].encode('utf-8')
    json_response = loads(link)
    if json_response['status'] == 404:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '本片暂不支持网页播放')
        return []

    items = []
    videos = json_response['data']['videos']
    # name = json_response['data']['name'].encode('utf-8')

    for item in videos:
        p_name = item['name'].encode('utf-8')
        p_url = httphead(item['url'].encode('utf-8'))
        # p_number = str(item['number'])
        p_thumb = item['pic'].encode('utf-8')

        seconds = item['duration']

        if item['dtype'] == 'prevue':
            extra = EXTRA % '|预'
        else:
            extra = ''
        items.append({
            'label': p_name + extra.encode('utf-8'),
            'path': url_for('playvideo', url=p_url),
            'thumbnail': p_thumb,
            'is_playable': True,
            'info': {'title': p_name, 'duration': seconds,
                     'plot': intro['description']}
        })

    # playlist
    items += playList(url)

    # related
    items += relatedList(url)
    return items


##############################################################################
def selResolution():
    resolution = int(plugin.addon.getSetting('resolution'))
    if resolution == 4:
        list = [x[1] for x in RES_LIST]
        sel = xbmcgui.Dialog().select('清晰度', list)
        if sel == -1:
            sel = 2          # set default
        return sel
    else:
        return resolution

@plugin.route('/movielist/<url>/')
def playvideo(url):
    resolution = selResolution()

    v_urls = video_from_url(url, level=resolution)
    if len(v_urls) > 0:
        plugin.set_resolved_url(v_urls[0])
    else:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '没有可播放的视频')


@plugin.route('/albumlist/<url>/')
def albumlist(url):
    plugin.set_content('TVShows')
    vid = r1('http?://www.fun.tv/vplay/v-(\w+)', url)
    epid = r1('http?://www.fun.tv/vplay/.*g-(\w+)', url)
    if vid:
        return singleVideo(url)    # play single video
    elif epid:
        return seriesList(url)     # list series
    else:
        return []


@plugin.route('/mainlist/<url>/')
def mainlist(url):
    plugin.set_content('TVShows')
    html = get_html(url)

    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod-videos'})

    items = soup[0].find_all('div', {'class': 'mod-vd-i'})
    items = tree.find_all('div', {'class': 'mod-vd-i'})

    yield {
        'label': '[选择过滤]',
        'path': url_for('vfilters', url=url)
    }

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
            p_name1 += '[COLOR FF00FFFF](' + span.text.strip() + ')[/COLOR] '

        score = inf.find('b', {'class': 'score'})
        if score:
            p_name1 += '[COLOR FFFF00FF][' + score.text + '][/COLOR]'

        sp = item.find("class='ico-dvd spdvd'")
        hd = item.find("class='ico-dvd hdvd'")
        if sp is not None and sp > 0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif hd is not None and hd > 0:
            p_name1 += ' [COLOR FF00FFFF][高清][/COLOR]'

        p_duration = item.find('i', {'class': 'tip'})
        info = {
            'title': p_name,
        }
        desc = inf.find('p', {'class', 'desc'})
        if desc:
            info['plot'] = desc.text

        yield {
            'label': p_name1,
            'path': url_for('albumlist', url=href),
            'thumbnail': p_thumb,
            'info': info
        }

    # Construct page selection
    soup = tree.find_all('div', {'class': 'pager-wrap'})
    if len(soup) > 0:
        pages = soup[0].find_all('a')

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
    html = get_html(HOST_URL + '/retrieve/')
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'ls-nav-bar'})
    items = soup[0].find_all('li')

    for item in items:
        yield {
            'label': item.a.text,
            'path': url_for('mainlist', url=httphead(item.a['href']))
        }


if __name__ == '__main__':
    plugin.run()
