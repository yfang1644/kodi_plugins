# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from urllib import urlencode
import urllib2
from json import loads, dumps

userAgent = 'Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10'
headers = {'User-Agent': userAgent}

plugin = Plugin()
url_for = plugin.url_for

HOST = 'http://www.qingting.fm'
PAGESIZE = 12
BANNER_FMT = '[COLOR gold][%s][/COLOR]'

def get_html(url):
    req = urllib2.Request(url, headers=headers)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    return loads(httpdata)


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


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/pagelist/<id>')
def pagelist(id):
    plugin.set_content('music')
    pageAPI = 'http://i.qingting.fm/wapi/channels/{}/programs/page/1/pagesize/1000'
    js = get_html(pageAPI.format(id))

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


@plugin.route('/Regions/<type>/<id><page>')
def Regions(type, id, page):
    data = loads(type)

    dialog = xbmcgui.Dialog()
    catlist = [x['title'] for x in data]
    sel = dialog.select('分类', catlist)
    if sel >= 0:
        return radiopage(data[sel]['id'], page=1)
    else:
        return radiopage(data[0]['id'], page=1)


@plugin.route('/radiopage/<id>/<page>')
def radiopage(id, page):
    radioPage = 'http://rapi.qingting.fm/categories'
    js = get_html(radioPage)

    area = js['Data']['regions'] + js['Data']['regions_map']
    type = js['Data']['channel_categories'] + js['Data']['program_categories']
    items = [
        {
            'label': u'地区',
            'path': url_for('Regions', type=dumps(area), id=id, page=page),
        },
        {
            'label': u'类型',
            'path': url_for('Regions', type=dumps(type), id=id, page=page)
        }
    ]

    req = {
        'page': page,
        'pagesize': PAGESIZE,
        'with_total': 'true'
    }

    regionAPI = 'http://rapi.qingting.fm/categories/{}/channels?'
    js = get_html(regionAPI.format(id) + urlencode(req))
    js = js['Data']
    
    total_page = (js['total'] + PAGESIZE - 1) // PAGESIZE
    items += previous_page('radiopage', page, total_page, id=id)

    for item in js['items']:
        cid = item['content_id']
        try:
            title = item['title'] + '(%s)' % (item['nowplaying']['title'])
            dur = int(item['nowplaying']['duration'])
        except:
            title = item['title']
            dur = 0
        items.append({
            'label': title,
            'path': 'http://lhttp.qingting.fm/live/{}/64k.mp3'.format(cid),
            'thumbnail': item['cover'],
            'is_playable': True,
            'info': {'title': title, 'duration': dur}
        })
    
    items += next_page('radiopage', page, total_page, id=id)
    return items

@plugin.route('/typelist/<data>/<attrs>/<page>')
def typelist(data, attrs, page):
    js = loads(data)
    dialog = xbmcgui.Dialog()
    catlist = [x['name'] for x in js]
    sel = dialog.select('分类', catlist)
    if sel >= 0:
        return categories(js[sel]['id'], 0, 1)
    else:
        return categories(js[0]['id'], 0, 1)


@plugin.route('/filters/<data>/<id>/<page>')
def filters(data, id, page):
    js = loads(data)
    dialog = xbmcgui.Dialog()

    pattrs = ''
    for cat in js:
        catlist = [x['name'] for x in cat['values']]
        sel = dialog.select(cat['name'], ['全部'] + catlist)
        if sel > 0:
            pattrs += str(cat['values'][sel-1]['id']) + '-'

    if pattrs == '':
        pattrs = '0'
    pattrs = pattrs.strip('-')
    return categories(id, pattrs, 1)


@plugin.route('/categories/<id>/<attrs>/<page>')
def categories(id, attrs, page):
    req = {
        'category': id,
        'attrs': attrs,
        'curpage': page
    }
    cateAPI = 'http://i.qingting.fm/capi/neo-channel-filter?'
    js = get_html(cateAPI + urlencode(req))
    total_page = (int(js['total']) + PAGESIZE - 1) // PAGESIZE
    js = js['data']

    if id == '0':
        id = js['categories'][0]['id']
        return categories(id, attrs, page)
    
    for x in js['categories']:
        if x['id'] == int(id):
            label_cat = x['name']
            break

    if attrs == '0':
        label_typ = u'全部'
    else:
        tlist = []
        for x in js['filters']:
            tlist += x['values']
        tdict = {}
        for x in tlist:
            tdict[str(x['id'])] = x['name']
        label_typ = ''
        ctype = str(attrs).split('-')
        for x in ctype:
            label_typ += '|' + tdict.get(x, '')  

    items = []
    items.append({
        'label': u'分类-' + label_cat,
        'path': url_for('typelist', data=dumps(js['categories']), attrs=attrs, page=page)
    })
    items.append({
        'label': u'过滤' + label_typ,
        'path': url_for('filters', data=dumps(js['filters']), id=id, page=page)
    })

    items += previous_page('categories', page, total_page, id=id, attrs=attrs)

    for item in js['channels']:
        items.append({
            'label': item['title'],
            'path': url_for('pagelist', id=item['id']),
            'thumbnail': item['cover'],
            'info': {'plot': item['description']}
        })

    items += next_page('categories', page, total_page, id=id, attrs=attrs)

    return items


@plugin.route('/XXcategories/<id>')
def XXcategories(id):
    cateAPI = 'http://i.qingting.fm/capi/neo-channel-filter?'
    js = get_html(cateAPI)

    for item in js['data']['categories']:
        yield {
            'label': item['name'],
            'path': url_for('sublist', id=item['id'], attrs=0, page=1)
        }

@plugin.route('/')
def root():
    yield {
        'label': u'听书、听音乐',
        'path': url_for('categories', id=0, attrs=0, page=1)
    }
    yield {
        'label': u'电台',
        'path': url_for('radiopage', id=85, page=1)
    }


if __name__ == '__main__':
    plugin.run()
