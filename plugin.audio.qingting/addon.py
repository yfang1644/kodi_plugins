# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin
from urllib import urlencode
import urllib2
from json import loads

userAgent = 'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10'
headers = {'User-Agent': userAgent}

plugin = Plugin()
url_for = plugin.url_for

HOST = 'http://www.qingting.fm'

BANNER_FMT = '[COLOR gold][%s][/COLOR]'
def get_html(url):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    return httpdata


@plugin.route('/stay')
def stay():
    pass

@plugin.route('/pagelist/<id>')
def pagelist(id):
    plugin.set_content('music')
    pageAPI = 'http://i.qingting.fm/wapi/channels/{}/programs/page/1/pagesize/1000'
    page = get_html(pageAPI.format(id))
    js = loads(page)

    for item in js['data']:
        thisitem = {
            'label': item['name'],
            'info': {'title': item['name'], 'duration': int(item['duration'])}
        }
        path = item['file_path']
        if path is not None:
            thisitem['path'] = 'http://od.qingting.fm/' + path
            thisitem['is_playable'] = True
        else:
            thisitem['path'] = url_for('stay')
        yield thisitem


@plugin.route('/Regions/<id>/<page>')
def Regions(id, page=1):
    req = {
        'page': 1,
        'pagesize': 12,
        'with_total': 'true'
    }

    regionAPI = 'http://rapi.qingting.fm/categories/{}/channels?'
    html = get_html(regionAPI.format(id) + urlencode(req))
    js = loads(html)['Data']
    
    page = int(page)
    total_page = (js['total'] + 11) // 12
    if page > 1:
        yield {
            'label': u'上一页 - {0}/{1}'.format(page, total_page),
            'path': url_for('Regions', id=id, page=page-1)
        }

    for item in js['items']:
        cid = item['content_id']
        try:
            title = item['title'] + '(%s)' % (item['nowplaying']['title'])
            dur = int(item['nowplaying']['duration'])
        except:
            title = item['title']
            dur = 0
        yield {
            'label': title,
            'path': 'http://lhttp.qingting.fm/live/{}/64k.mp3'.format(cid),
            'thumbnail': item['cover'],
            'is_playable': True,
            'info': {'title': title, 'duration': dur}
        }
    if page < total_page:
        yield {
            'label': u'下一页 - {0}/{1}'.format(page, total_page),
            'path': url_for('Regions', id=id, page=page+1)
        }


@plugin.route('/radiopage')
def radiopage():
    radioPage = 'http://rapi.qingting.fm/categories'
    page = get_html(radioPage)
    js = loads(page)

    data = js['Data']['regions'] + js['Data']['regions_map']

    for item in data:
        if item['id'] < 0:
            continue
        yield {
            'label': item['title'],
            'path': url_for('Regions', id=item['id'], page=1)
        }

    for topic in js['Data']['program_categories']:
        continue
        yield {
            'label': topic['title'],
            'path': url_for('Regions', id=topic['id'], page=1),
            'thumbnail': topic['cover']
        }

@plugin.route('/sublist/<id>/<attrs>/<page>')
def sublist(id, attrs=0, page=1):
    req = {
        'category': id,
        'attrs': attrs,
        'curpage': page
    }
    cateAPI = 'http://i.qingting.fm/capi/neo-channel-filter?'
    html = get_html(cateAPI + urlencode(req))
    js = loads(html)

    total_page = (int(js['total']) + 11) // 12
    page = int(page)
    if page > 1:
        yield {
            'label': u'上一页 - {0}/{1}'.format(page, total_page),
            'path': url_for('sublist', id=id, attrs=attrs, page=page-1)
        }

    for item in js['data']['channels']:
        yield {
            'label': item['title'],
            'path': url_for('pagelist', id=item['id']),
            'thumbnail': item['cover'],
            'info': {'plot': item['description']}
        }

    if page < total_page:
        yield {
            'label': u'下一页 - {0}/{1}'.format(page, total_page),
            'path': url_for('sublist', id=id, attrs=attrs, page=page+1)
        }
    for filter in js['data']['filters']:
        for j in filter['values']:
            yield {
                'label': j['name'],
                'path': url_for('sublist', id=id, attrs=j['id'], page=1)
            }

@plugin.route('/categories')
def categories():
    cateAPI = 'http://i.qingting.fm/capi/neo-channel-filter?'
    page = get_html(cateAPI)
    js = loads(page)

    for item in js['data']['categories']:
        yield {
            'label': item['name'],
            'path': url_for('sublist', id=item['id'], attrs=0, page=1)
        }

@plugin.route('/')
def root():
    mainlist = {
        '分类': 'categories',
        '电台': 'radiopage'
    }

    items = [{
        'label': item,
        'path': url_for(mainlist[item]),
    } for item in mainlist]

    return items

if __name__ == '__main__':
    plugin.run()
