#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from urllib import urlencode
import urllib2
from json import loads

BaseHtml = 'http://www.tingban.cn'
BANNER_FMT = '[COLOR gold][%s][/COLOR]'

UserAgent = "Mozilla/5.0 (X11; Linux i686; rv:35.0) Gecko/20100101 Firefox/35.0"

plugin = Plugin()
url_for = plugin.url_for

def request(url, js=True):
    print('request', url)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    cont = response.read()
    response.close()
    if js:
        cont = loads(cont)
    return cont

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


@plugin.route('/radiostation/<id>')
def radiostation(id):
    API = '/webapi/broadcast/detail?broadcastid={}'.format(id)
    c = request(BaseHtml + API)
    m3u8 = c['result']['playUrl']
    plugin.set_resolved_url(m3u8)


@plugin.route('/radio/<id>/<cid>')   # id and classid
def radio(id, cid):
    API = '/webapi/broadcast/programcategory'
    c = request(BaseHtml + API)
    for item in c['result']['dataList']:
        yield {
            'label': BANNER_FMT % item['name'],
            'path': url_for('radio', id=id, cid=item['id']),
        }

    if cid == 0:
        cid = c['result']['dataList'][0]['id']

    API = '/webapi/broadcast/arealist'
    c = request(BaseHtml + API)
    for item in c['result']['dataList']:
        yield {
            'label': BANNER_FMT % item['name'],
            'path': url_for('radio', id=item['id'], cid=cid),
        }
    
    if id == 0:
        id = c['result']['dataList'][0]['id']

    API = '/webapi/broadcast/search?'
    req = {
        'classifyid': cid,
        'area': id,
        'pagenum': 1,
        'pagesize': 200,
    }
    c = request(BaseHtml + API + urlencode(req))
    for item in c['result']['dataList']:
        yield {
            'label': item['name'],
            'path': url_for('radiostation', id=item['id']),
            'thumbnail': item['pic'],
            'is_playable': True
        }

@plugin.route('/sections/<id>/<page>')
def sections(id, page):
    plugin.set_content('music')
    API = '/webapi/audios/list?'
    req = {
        'id': id,
        'pagesize': 100,
        'pagenum': page,
        'sorttype': 1
    }
    c = request(BaseHtml + API + urlencode(req))

    total_page = c['result']['sumPage']
    items = previous_page('sections', page, total_page, id=id)
    for item in c['result']['dataList']:
        aac = item['aacPlayUrl']
        mp3 = item['mp3PlayUrl']
        m3u8 = item['m3u8PlayUrl']
        items.append({
            'label': item['audioName'],
            'path': aac,
            'thumbnail': item['audioPic'],
            'is_playable': True,
            'info': {'title': item['audioName'],
                     'plot': item['audioDes'],
                    }
        })
    items += next_page('sections', page, total_page, id=id)
    return items

@plugin.route('/classification/<fid>/<cid>/<page>')
def classification(fid, cid, page):
    plugin.set_content('music')
    API = '/webapi/category/list?fid={}'.format(fid)
    c = request(BaseHtml + API)
    items = []
    for cat in c['result']['dataList']:
        items.append({
            'label': BANNER_FMT % cat['categoryName'],
            'path': url_for('classification',
                            fid=fid, 
                            cid=cat['categoryId'],
                            page=1),
            'thumbnail': cat['logo'],
        })

    req = {
        'cid': cid if int(cid) else fid,
        'sorttype': 'HOT_RANK_DESC',
        'pagesize': 24,
        'pagenum': page
    }
    API = '/webapi/resource/search?'
    c = request(BaseHtml + API + urlencode(req))
    total_page = c['result']['totalPages']

    items += previous_page('classification', page, total_page, fid=fid, cid=cid)
    
    for item in c['result']['dataList']:
        items.append({
            'label': item['name'],
            'path': url_for('sections', id=item['id'], page=1),
            'thumbnail': item['pic'],
            'info': {'title': item['name'],
                     'plot': item['desc']}
        })

    items += next_page('classification', page, total_page, fid=fid, cid=cid)
    return items


@plugin.route('/')
def root():
    plugin.set_content('music')
    API = '/webapi/category/list'
    mainpage = request(BaseHtml + API)
    results = mainpage['result']['dataList']
    for item in results:
        if item['categoryId'] < 0:
            yield {
                'label': item['categoryName'],
                'path': url_for('radio', id=0, cid=0),
            }
        else:
            yield {
                'label': item['categoryName'],
                'path': url_for('classification',
                                fid=item['categoryId'],
                                cid=0,
                                page=1),
                'thumbnail': item['logo'],
            }


if __name__ == '__main__':
    plugin.run()
