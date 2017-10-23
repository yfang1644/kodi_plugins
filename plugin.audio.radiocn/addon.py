#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from urllib import urlencode
import urllib2
from json import loads

BaseHtml = 'http://www.radio.cn/pc-portal/erji'
BaseAPI = 'http://tacc.radio.cn/pcpages'
BANNER_FMT = '[B][COLOR gold][%s][/COLOR][/B]'

UserAgent = "Mozilla/5.0 (X11; Linux i686; rv:35.0) Gecko/20100101 Firefox/35.0"
headers = {"Host": "www.radio.cn",
           "User-Agent": UserAgent,
           "Referer": "http://www.radio.cn/index.php?option=default,radio"}

plugin = Plugin()
url_for = plugin.url_for

def request(url, js=True):
    print('request', url)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    cont = response.read()
    response.close()
    if js:
        cont = loads(cont.strip("()"))
    return cont

@plugin.route('/stay')
def stay():
    pass

@plugin.route('/station/<place_id>/<type_id>')
def station(place_id, type_id):
    #name, mode, icon, area, type
    plugin.set_content('video')
    req = {
        'place_id': '' if place_id == '0' else place_id,
        'type_id': '' if type_id == '0' else type_id
    }
    c = request(BaseAPI+'/radiopages?' + urlencode(req))
    items = []

    items.append({
        'label': BANNER_FMT % '地区',
        'path': plugin.url_for('stay')
    })
    for place in c['data']['place']:
        items.append({
            'label': place['name'],
            'path': url_for('station', place_id=place['id'],type_id=type_id)
        })
    items.append({
        'label': BANNER_FMT % '类型',
        'path': url_for('stay')
    })
    for type in c['data']['type']:
            items.append({
                'label': type['name'],
                'path': url_for('station', place_id=place_id,type_id=type['id'])
            })

    for top in c['data']['top']:
        items.append({
            'label': top['name'],
            'path': top['streams'][0]['url'],
            'thumbnail': top['icon'][0]['url'],
            'is_playable': True,
            'info': {'title': top['name']}
        })
    return items

@plugin.route('/sections/<id>')
def sections(id):
    plugin.set_content('music')
    req = {
        'od_id': id,
       # 'start': 1,
        'rows': 2000
    }
    c = request(BaseAPI + '/odchannelpages?' + urlencode(req))
    items = []
    for item in c['data']['program']:
        items.append({
            'label': item['name'],
            'path': item['streams'][0]['url'],
            'thumbnail': item['imageUrl'][0]['url'],
            'is_playable': True,
            'info': {'title': item['name'],
                     'plot': item['description'],
                     'duration': int(item['duration'])
                    }
        })
    return items

@plugin.route('/classification/<cate_id>/<page>')
def classification(cate_id, page):
    req = {
        'per_page': 16,
        'page': page,
        'cate_id': '' if cate_id == '0' else cate_id
    }
    c = request(BaseAPI + '/categorypages?'+urlencode(req))
    items = []
    for cat in c['data']['category']:
        items.append({
            'label': cat['name'],
            'path': url_for('classification', cate_id=cat['id'], page='1')
        })

    for chn in c['data']['odchannel']:
        items.append({
            'label': chn['name'],
            'path': url_for('sections', id=chn['id']),
            'thumbnail': chn['imageUrl'][0]['url'],
            'info': {'title': chn['name'],
                     'plot': chn['description'],
                     'artist': chn.get('source', '')}
        })

    items += [{'label': BANNER_FMT % u'分页', 'path': url_for('stay')}]
    for i_page in range(int(c['data']['total_page'])):
        if i_page == int(page)-1: continue
        items.append({
            'label': str(i_page+1),
            'path': url_for('classification', cate_id=cate_id, page=i_page+1)
        })
    return items

@plugin.route('/oneanchor/<id>')
def oneanchor(id):
    c = request(BaseAPI + '/oneanchor?' + 'anchorId=' + id)
    items = [{
        'label': item['name'],
        'path': url_for('sections', id=item['id']),
        'thumbnail': item['img'],
    } for item in c['ondemands']]

    return items

@plugin.route('/podcast/<domain>')
def podcast(domain):
    c = request(BaseAPI + '/anchorpages?')
    items = [{
        'label': item['name'],
        'path': url_for('podcast', domain=item['id'])
    } for item in c['AnchorsLabeldomain']]
    items.insert(0, {'label': BANNER_FMT  % u'主播分类',
                     'path': url_for('stay')})

    if domain == '0':
        domain = c['allAnchors']['id']
    req = {
        'limit': 2000,
        'offset': 1,
        'labeldomainId': domain
    }
    c = request(BaseAPI + '/anchorsByDomain?' + urlencode(req))

    for item in c['allAnchors']['anchors']:
        items.append({
            'label': item['name'],
            'path': url_for('oneanchor', id=item['id']),
            'thumbnail': item['img'],
            'info': {'plot': item['description']},
        })

    return items

@plugin.route('/')
def root():
    items = [
        {
            'label': '电台',
            'path': url_for('station', place_id='0', type_id='0')
        },
        {
            'label': '分类',
            'path': url_for('classification', cate_id='0', page=1)
        },
        {
            'label': '主播',
            'path': url_for('podcast', domain = '0')
        }
    ]
    return items

if __name__ == '__main__':
    plugin.run()
