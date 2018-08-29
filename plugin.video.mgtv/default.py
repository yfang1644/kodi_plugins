#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from bs4 import BeautifulSoup
from json import loads
from common import get_html, r1
from lib.mgtv import video_from_vid

plugin = Plugin()
url_for = plugin.url_for

# Plugin constants
__addonid__   = plugin.addon.getAddonInfo('id')
__addonname__ = plugin.addon.getAddonInfo('name')
__cwd__       = plugin.addon.getAddonInfo('path')

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
BANNER_FMT2 = '[COLOR FFDE0087]%s[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

LIST_URL = 'http://list.mgtv.com'
HOST_URL = 'http://www.mgtv.com'

RESOLUTION = {'sd': '标清', 'hd': '高清', 'shd': '超清', 'fhd': '全高清'}


def httphead(url):
    if len(url) < 2:
        return url
    if url[:2] == '//':
        url = LIST_URL + url
    elif url[0] == '/':
        url = LIST_URL + url

    return url


@plugin.route('/changeList/<url>')
def changeList(url):
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'm-tag-type'})

    surl = url.split('/')
    purl = surl[-1].split('-')

    dialog = xbmcgui.Dialog()

    filter = ''
    for iclass in soup:
        title = iclass.find('h5', {'class': 'u-title'}).text
        si = iclass.find_all('a')
        list = []
        for subitem in si:
            list.append(subitem.text)
        sel = dialog.select(title, list)

        if sel < 0:
            continue

        filter += u'|' + title + u'(' + si[sel].text + u')'
        seurl = si[sel]['onclick'].split('/')[-1]
        seurl = seurl.split('-')

        for i in range(0, len(purl)):
            if seurl[i] != '':
                purl[i] = seurl[i]

    surl[-1] = '-'.join(purl)
    url = '/'.join(surl)
    mainlist(url, filter)

@plugin.route('/mainlist/<url>/<filter>')
def mainlist(url, filter):
    filtitle = '' if filter == '0' else filter
    items = [{
        'label': BANNER_FMT % (u'[分类过滤]' + filtitle),
        'path': url_for('changeList', url=url)
    }]

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')

    soups = tree.find_all('div', {'class': 'm-result-list'})

    soup= soups[0].find_all('li', {'class': 'm-result-list-item'})
    for item in soup:
        thumb = item.img['src']
        t = item.find('a', {'class': 'u-title'})
        title = t.text
        href = t['href']
        t = item.find('a', {'class': 'u-video'})
        try:
            exinfo = '(' + item.em.text + ')'
        except:
            exinfo = ''

        # pay info
        pay = item.find('i', {'class': 'v-mark-v5'})
        if pay:
            pay = BANNER_FMT2 % ('(' + pay.text + ')')
        else:
            pay = ''

        pinfo = item.find('span', {'class': 'u-desc'})
        info = pinfo.text.replace(' ', '')
        info = info.replace('\t', '')
        items.append({
            'label': title + exinfo + pay,
            'path': url_for('episodelist', url=href, page=0),
            'thumbnail': item.img['src'],
            'info': {'title': title, 'plot': info}
        })

    # multiple pages
    setpage = tree.find_all('div', {'class': 'w-pages'})
    try:
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
            items.append({
                'label': BANNER_FMT % title,
                'path': url_for('mainlist', url=href, filter=filter)
            })
    except:
        pass
    return items

@plugin.route('/episodelist/<url>/<page>')
def episodelist(url, page):
    plugin.set_content('video')
    episode_api = 'http://pcweb.api.mgtv.com/movie/list'   # ???
    episode_api = 'http://pcweb.api.mgtv.com/episode/list'
    episode_api += '?video_id=%s&page=%d&size=40'
    page = int(page)
    if url[-1] == '/':    # is a directory
        html = get_html(url)
        id = r1('vid:\s*(\d+)', html)
    else:
        id = r1('(\d+).html', url)

    html = get_html(episode_api % (id, page))
    jsdata = loads(html)

    data = jsdata['data']
    list = data.get('list', []) + data.get('short', [])
    total_page = data.get('total_page', 1)

    for series in list:
        title = series['t1'] + ' ' + series['t2']
        if series['isnew'] == '1':
            title = title + u'(新)'
        elif series['isnew'] == '2':
            title = title + u'(预)'

        vip = series.get('isvip', 0)
        pay = '(VIP)' if vip == '1' else ''

        yield {
            'label': title + pay,
            'path': url_for('playvideo', vid=series['video_id']),
            'is_playable': True,
            'thumbnail': series['img'],
            'info': {'title': title}
        }

    if page > 0:
        yield {
            'label': BANNER_FMT % u'上一页',
            'path': url_for('episodelist', url=url, page=page-1)
        }
    if page < total_page - 1:
        yield {
            'label': BANNER_FMT % u'下一页',
            'path': url_for('episodelist', url=url, page=page+1)
        }

    related = data.get('related')
    if related:
        title = related['t1'] + ' ' + related['t2']
        img = related['img']
        href = httphead(related['url'])
        yield {
            'label': BANNER_FMT2 % title,
            'path': url_for('episodelist', url=href, page=page),
            'thumbnail': img,
            'info': {'title': title}
        }

@plugin.route('/playvideo/<vid>')
def playvideo(vid):
    level = int(__addon__.getSetting('resolution'))

    m3u_url = video_from_vid(vid, level=level)
    stackurl = 'stack://' + ' , '.join(m3u_url)
    plugin.set_resolved_url(stackurl)


@plugin.route('/')
def root():
    mainAPI = 'http://pc.bz.mgtv.com/odin/c1/channel/list?version=5.0&type=4&pageSize=999'
    jsdata = loads(get_html(mainAPI))

    for item in jsdata['data']:
        url = LIST_URL + '/-------------.html?channelId=' + item['pageType']
        yield {
            'label': item['title'],
            'path': url_for('mainlist',
                            url=url,
                            filter='0'),
            'info': {'title': item['title'], 'plot': item['vclassName']}
        }

if __name__ == '__main__':
    plugin.run()
