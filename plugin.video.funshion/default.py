#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
import re
from random import randrange
from bs4 import BeautifulSoup
from json import loads
from common import get_html, r1
from funshion import video_from_url

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
EXTRA = '[COLOR FF8080FF]%s[/COLOR]'

HOST_URL = 'https://www.fun.tv'

# get wrong IP from some local IP
unusableIP = ("121.32.237.24",
              "121.32.237.42",
              "222.84.164.2",
              "122.228.57.21")

# followings are usable
usableIP = ("112.25.81.203",
            "111.63.135.120",
            "122.72.64.198",
            "183.203.12.197",
            "223.82.247.101",
            "222.35.249.3")


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


def replaceServer(url):
    server = plugin.addon.getSetting('pickserver')
    if server == 'true':
        return url

    ip = re.compile('http://(\d+\.\d+\.\d+\.\d+)').findall(url)
    if ip[0] not in usableIP:    # replace a usable IP
        i_url = randrange(len(usableIP))
        return re.sub('http://(\d+\.\d+\.\d+\.\d+)',
                      'http://%s'%(usableIP[i_url]), url)
    else:
        return url


def httphead(url):
    if url[0:2] == '//':
        url = 'http:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


def mergeUrl(purl, curl):
    for x in curl:
        if len(x) < 2:
            continue
        hx = x[:2]
        for i in range(len(purl)):
            if purl[i].find(hx) >= 0:
                purl[i] = x
                break
        if x not in purl:
            purl.insert(0, x)

    return purl


##############################################################################
# Routine to update video list as per user selected filtrs
##############################################################################
@plugin.route('/vfilters/<url>/<filtrs>')
def vfilters(url, filtrs):
    surl = url.split('/')
    purl = surl[-2].split('.')

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'ls-nav-bar'})

    dialog = xbmcgui.Dialog()

    filter = ''
    for iclass in soup[1:]:
        si = iclass.find_all('li')
        list = []
        for subitem in si:
            if 'bar-current' in subitem['class']:
                title = '[COLOR FFFF00FF]' + subitem.a.text + '[/COLOR]'
            else:
                title = subitem.a.text
            list.append(title)

        try:
            caption = iclass.label.text
        except:
            caption = u'排序'
        sel = dialog.select(caption, list)
        if sel >= 0:
            filter += '|[COLOR FFF00080]' + caption + '[/COLOR](' + si[sel].text + ')'
            curl = si[sel].a['href'].split('/')
            curl = curl[-2].split('.')
            purl = mergeUrl(purl, curl)

    surl[-2] = '.'.join(purl)
    url = '/'.join(surl)

    return mainlist(url, filter.encode('utf-8'))


def playList(url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    lists = tree.find_all('a', {'class': 'vd-list-item'})

    if len(lists) < 1:
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
            'path': url_for('movielist', url=httphead(item['href'])),
            'thumbnail': p_thumb,
            'is_playable': True,
            'info': {'title': item['title'], 'duration': duration}
        })
    return items


def relatedList(url):
    vid = r1('https://www.fun.tv/vplay/.*g-(\d+)', url)
    # rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/media?isajax=1'
    rel_api = 'http://api1.fun.tv/api_get_related_videos/%s/video?isajax=1'
    link = get_html(rel_api % vid)
    tree = BeautifulSoup(link, 'html.parser')

    lists = tree.find_all('div', {'class': 'mod-vd-i'})
    items = []
    for item in lists:
        pic = item.find('div', {'class': 'pic'})
        inf = item.find('div', {'class': 'info'})
        try:
            href = inf.a['href']
        except:
            continue
        p_id = inf.a['data-id']
        p_thumb = httphead(pic.img['_lazysrc'])
        p_name = pic.img['alt']

        p_name1 = p_name + ' '

        score = inf.find('b', {'class': 'score'})
        if score:
            p_name1 += '[COLOR FFFF00FF][' + score.text + '][/COLOR]'

        if item.find("class='ico-dvd spdvd'") > 0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif item.find("class='ico-dvd hdvd'") > 0:
            p_name1 += ' [COLOR FF00FFFF][高清][/COLOR]'
        info = {'title': p_name}
        span = pic.find('span')
        if span and len(span.text) > 0:
            duration = 0
            for t in span.text.split(':'):
                duration = duration*60 + int(t)
            info['duration'] = duration

        desc = inf.find('p', {'class', 'desc'})
        if desc:
            p_name1 += ' (' + desc.text + ')'

        items.append({
            'label': p_name1,
            'path': url_for('albumlist', url=httphead(href), title=p_name.encode('utf-8')),
            'thumbnail': p_thumb,
            'info': info
        })
    return items


def singleVideo(url, title):
    items = [{
        'label': BANNER_FMT % title,
        'path': url_for('movielist', url=url),
        'is_playable': True,
    }]

    items += playList(url)

    items += relatedList(url)
    return items


##########################################################################
def seriesList(url, title):
    id = r1('https://www.fun.tv/vplay/.*g-(\d+)', url)
    # url = 'http://api.funshion.com/ajax/get_web_fsp/%s/mp4?isajax=1'
    purl = 'http://api.funshion.com/ajax/vod_panel/%s/w-1?isajax=1'  #&dtime=1397342446859
    print "XXXXXXXXXXXXXXXXXXXXXX",purl % id
    link = get_html(purl % id)
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
            'label': p_name + extra,
            'path': url_for('movielist', url=p_url),
            'thumbnail': p_thumb,
            'is_playable': True,
            'info': { 'title': p_name, 'duration': seconds}
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

@plugin.route('/movielist/<url>')
def movielist(url):
    resolution = selResolution()

    v_urls = video_from_url(url, level=resolution)
    if len(v_urls) > 0:
        v_url = replaceServer(v_urls[0])
        plugin.set_resolved_url(v_url)
    else:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '没有可播放的视频')


@plugin.route('/albumlist/<url>/<title>')
def albumlist(url, title):
    plugin.set_content('TVShows')
    sid = r1('https://www.fun.tv/vplay/.*v-(\d+)', url)
    vid = r1('https://www.fun.tv/vplay/.*g-(\d+)', url)
    if sid:
        return singleVideo(url, title)    # play single video
    elif vid:
        return seriesList(url, title)     # list series
    else:
        return []


@plugin.route('/mainlist/<url>/<filtrs>')
def mainlist(url, filtrs):
    html = get_html(url)

    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod-videos'})

    items = soup[0].find_all('div', {'class': 'mod-vd-i'})
    items = tree.find_all('div', {'class': 'mod-vd-i'})

    yield {
        'label': '[选择过滤]' + (filtrs if filtrs !='0' else ''),
        'path': url_for('vfilters', url=url, filtrs=filtrs)
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
            p_name1 += '[COLOR FF00FFFF](' + span.text + ')[/COLOR] '

        score = inf.find('b', {'class': 'score'})
        if score:
            p_name1 += '[COLOR FFFF00FF][' + score.text + '][/COLOR]'

        if item.find("class='ico-dvd spdvd'") > 0:
            p_name1 += ' [COLOR FFFFFF00][超清][/COLOR]'
        elif item.find("class='ico-dvd hdvd'") > 0:
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
            'path': url_for('albumlist', url=href ,title=p_name.encode('utf-8')),
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
            else:
                yield {
                    'label': page.text,
                    'path': url_for('mainlist', url=httphead(href), filtrs=filtrs)
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
            'path': url_for('mainlist', url=httphead(item.a['href']),
                            filtrs='0')
        }


if __name__ == '__main__':
    plugin.run()
