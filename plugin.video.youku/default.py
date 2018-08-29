#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui, xbmc
from urllib import quote_plus, urlencode
from json import loads
from common import get_html, match1
from lib.youku import video_from_vid

HOST = 'http://tv.api.3g.youku.com'
BASEIDS = {
    'pid': '0ce22bfd5ef5d2c5',
    'guid': '12d60728bd267e3e0b6ab4d124d6c5f0',
    'ngdid': '357e71ee78debf7340d29408b88c85c4',
    'ver': '2.6.0',
    'operator': 'T-Mobile_310260',
    'network': 'WIFI',
    'launcher': 0
}

########################################################################
# 优酷 www.youku.com
########################################################################

BANNER_FMT = '[COLOR gold][%s][/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

############################################################################
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


@plugin.route('/playvideo/<videoid>')
def playvideo(videoid):
    level = int(plugin.addon.getSetting('resolution'))

    urls = video_from_vid(videoid, level=level)
    stackurl = 'stack://' + ' , '.join(urls)
    plugin.set_resolved_url(stackurl)


@plugin.route('/select/<cid>')
def select(cid):
    req = {'cid': cid}
    req.update(BASEIDS)
    page = get_html(HOST + '/tv/v2_0/childchannel/list?' + urlencode(req))
    results = loads(page)['results']['result']

    lists = [x['sub_channel_title'] for x in results]
    f = [x['filter'] for x in results]

    dialog = xbmcgui.Dialog()

    sel = dialog.select(u'分类过滤', lists)
    filter = f[sel].encode('utf-8') if sel >= 0 else '0'
    filters = lists[sel].encode('utf-8') if sel >= 0 else '全部'
    return channel(cid, 1, filter, filters)


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return
    keyword = keyboard.getText()
    key = quote_plus(keyword)

    searchapi = HOST + '/layout/smarttv/showsearch?'
    req = {'video_type':1, 'keyword': keyword}
    req.update(BASEIDS)
    link = get_html(searchapi + urlencode(req))
    results = loads(link)['results']
    items = []
    for item in results:
        items.append({
            'label': item['showname'],
            'path': url_for('episodelist', tid=item['showid']),
            'thumbnail': item['show_vthumburl_hd']
        })

    searchapi = HOST + '/openapi-wireless/videos/search/{}?'
    req = {'pz': 500}
    req.update(BASEIDS)

    link = get_html(searchapi.format(key) + urlencode(req))

    # fetch and build the video series episode list
    finds = loads(link)
    for item in finds['results']:
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration*60 + int(t)

        items.append({
            'label': item['title'],
            'path': url_for('playvideo', videoid=item['videoid']),
            'thumbnail': item['img'],
            'is_playable': True,
            'info': {'title': item['title'], 'plot': item['desc'],
                     'duration': duration}
        })
    return items


@plugin.route('/videolist/<showid>')
def videolist(showid):
    url = HOST + '/layout/smarttv/shows/' + showid + '/series?'
    print "XXXXXXXXXXXXXXXXXXXXXXXXX",url + urlencode(BASEIDS)
    site = get_html(url + urlencode(BASEIDS))
    results = loads(site)['results']
    items = []
    for item in results:
        extra = '(' + item['show_videotype'] + ')' if int(item['is_trailer']) else ''
        items.append({
            'label': item['title'] + extra,
            'path': url_for('playvideo', videoid=item['videoid']),
            'thumbnail': item['img'],
            'is_playable': True,
            'info': {'title': item['title'], 'episode': item['video_stage']},
        })

    unsorted = [(dict_['info']['episode'], dict_) for dict_ in items]
    unsorted.sort()
    sorted = [dict_ for (key, dict_) in unsorted]
    return sorted


@plugin.route('/episodelist/<tid>')
def episodelist(tid):
    plugin.set_content('TVShows')
    req = {'id': tid}
    req.update(BASEIDS)
    site = get_html(HOST + '/layout/smarttv/play/detail?' + urlencode(req))
    results = loads(site)
    detail = results['detail']
    if detail['episode_total'] == '1':
        items = [{
            'label': detail['title'],
            'path': url_for('playvideo', videoid=detail['videoid']),
            'thumbnail': detail['img'],
            'is_playable': True,
            'info': {'title': detail['title'], 'plot': detail['desc']}
    }]
    else:
        items = [{
            'label': detail['title'] + '(' + detail['stripe_bottom'] + ')',
            'path': url_for('videolist', showid=detail['showid']),
            'thumbnail': detail['img'],
            'info': {'title': detail['title'], 'plot': detail['desc']}
        }]

    site = get_html(HOST + '/common/shows/relate?' + urlencode(req))
    results = loads(site)
    results = results['results']
    for item in results:
        items.append({
            'label': item['showname'] + '(' + item['stripe_bottom'] + ')',
            'path': url_for('episodelist', tid=item['showid']),
            'thumbnail': item['img_hd'],
        })
    return items


@plugin.route('/channel/<cid>/<page>/<filter>/<filters>')
def channel(cid, page, filter, filters):
    plugin.set_content('TVShows')
    pagesize = 20
    req = {
        'cid': cid,
        'pz': pagesize,
        'filter': '' if filter=='0' else filter,
        'pg': page
    }
    req.update(BASEIDS)
    try:
        site = get_html(HOST + '/layout/smarttv/item_list?' + urlencode(req))
    except:
        xbmcgui.Dialog().ok(plugin.addon.getAddonInfo('name'),
                            '此功能尚未实现')
        return index()

    jsdata = loads(site)
    total = jsdata['total']
    total_page = (total + pagesize - 1) // pagesize

    items = [{
        'label': '',
        'label': BANNER_FMT % ('分类过滤' + '('+ filters + ')'),
        'path': url_for('select', cid=cid),
    }]

    items += previous_page('channel', page, total_page, cid=cid, filter=filter, filters=filters)
    results = jsdata['results']
    for item in results:
        completed = u'--完结' if item['completed'] else ''
        reputation = str(item['reputation'])
        items.append({
            'label': item['showname'] + '(' + reputation + completed + ')' ,
            'path': url_for('episodelist', tid=item['tid']),
            'thumbnail': item['show_vthumburl_hd'],
        })

    items += next_page('channel', page, total_page, cid=cid, filter=filter, filters=filters)
    return items


@plugin.route('/')
def index():
    plugin.set_content('TVShows')
    page = get_html(HOST + '/tv/main/top?' + urlencode(BASEIDS))
    jsdata = loads(page)['results']['channel']
    items = [{
        'label': BANNER_FMT % '优酷视频--搜索',
        'path': url_for('search')
    }]
    for item in jsdata:
        items.append({
            'label': item['title'],
            'path': url_for('channel', cid=item['cid'], page=1, filter='0', filters='全部'),
            'thumbnail': item['image']
        })
    return items


if __name__ == '__main__':
    plugin.run()
