#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if sys.version[0] == '3':
    from urllib.parse import urlencode
else:
    from urllib import urlencode
from xbmcswift2 import Plugin, xbmcgui
from common import get_html
from json import loads
import re
        
category = [
    {'电影': {
        'type': ['全部','动作','喜剧','惊悚','谍战','剧情','犯罪','战争','爱情',
                 '青春','悬疑','家庭','历史','奇幻','动画','偶像','科幻','冒险'],
        'area': ['全部','内地','香港地区','台湾地区','美国','英国','印度','韩国','日本',
                 '泰国','加拿大','德国','巴西','埃及','意大利','俄罗斯','捷克',
                 '西班牙','法国','澳大利亚','新加坡','新西兰','瑞典','爱尔兰',
                 '丹麦','土耳其','其他'],
        'year': ['全部','2020','2019','2018','2017','2016','2015','2014','2013',
                 '2012','2011','2010','2009','2008','2007','2006','2005','2004',
                 '2003','更早'],
        'pack':'1002581,1002601,1003862,1003864,1003866,1004121,1003861,1004761,1004641',
        'contDisplayType': 1000,},
    },
    {'电视剧': {
        'type': ['全部','谍战','军旅','家庭','爱情','古装','青春','偶像','伦理',
                 '武侠','刑侦','悬疑','都市'],
        'area': ['全部','内地','美国','英国','韩国','泰国','日本','香港地区','台湾地区'],
        'year': ['全部','2019','2018','2017','2016','2015','2014','2013','2012','2011',
                 '2010','2009','2008','2007','2006','2005','2004','2003','2002','2001',
                 '2000','90年代','80年代','更早'],
        'pack': '1002581,1003861,1003863,1003866,1002601,1004761,1004641',
        'contDisplayType': 1001}
    },
    {'综艺': {
        'type': ['全部','竞技','选秀','观点','美妆','旅行','亲子','益智','职场','军旅',
                 '游戏','歌舞','问答'],
        'area': ['全部','内地','台湾地区'],
        'year': ['全部','2019','2018','2017','2016','2015','2014','2013','2012','2011',
                 '2010','2009','2008','2007','2006','2005','2004','2003','更早'],
        'pack': '1002581,1002601',
        'contDisplayType': 1005}
    },
    {'动漫': {
        'type': ['全部','冒险','搞笑','动作','奇幻','青春','爱情','亲子'],
        'area': ['全部','日本','内地','美国','其他'],
        'year': ['全部','2019','2018','2017','2016','2015','2014','2013','2012','2011',
                 '2010','更早'],
        'pack': '1002601,1002581',
        'contDisplayType': 1007}
    },
    {'少儿': {
        'type': ['全部','动画','故事','儿歌','玩具'],
        'area': ['全部','内地','韩国','日本','爱尔兰','英国','澳大利亚','美国','巴西',
                 '俄罗斯','法国','加拿大','西班牙','意大利','印度','其他'],
        'year': ['全部','2019','2018','2017','2016','2015','2014','2013','2012',
                 '2011','2010','2009','2008','2007','2006','2005','2004','2003',
                 '2002','2001','2000','90年代','80年代','更早'],
        'pack': '1002581,1002601',
        'contDisplayType': 601382}
    },
    {'纪实': {
        'type': ['全部','军事','社会','自然','历史','刑侦','科技','人物','艺术','动物',
                 '文物','美食','旅游','古迹','探秘','其他'],
        'area': ['全部','内地','美国','英国','香港地区','其他'],
        'year': ['全部','2019','2018','2017','2016','2015','2014','2013','2012',
                 '2011','2010','2009','2008','2007','2006','2005','2004','2003','更早'],
        'pack': '1002581,1002601',
        'contDisplayType': 1002}
    },
    {'BBC':{
        'type': ['全部','自然','历史','科技','社会','人文','地理','军事','刑侦',
                 '人物','艺术','动物','美食','旅游','古迹','探秘','其他'],
        'area': ['全部'],
        'year': ['全部','2017','2016','2015','2014','2013','2012','2011','2010'],
        'pack': '1002581,1002601',
        'contDisplayType': 1002,
        'mediaChu': 'BBC'}
    },
    {'Discovery': {
        'type': ['全部','自然','历史','科技','社会','人文','地理','军事','刑侦',
                 '人物','艺术','动物','美食','旅游','古迹','探秘','其他'],
        'area': ['全部'],
        'year': ['全部','2017','2016','2015','2014','2013','2012','2011','2010','更早'],
        'pack': '1002581,1002601',
        'contDisplayType': 1002,
        'mediaChu': 'Discovery'}
    }
    ]

cateAPI = 'https://jadeite.migu.cn/search/v3/category?'
urlAPI = 'https://webapi.miguvideo.com/gateway/playurl/v3/play/playurl?contId=%s&rateType=1,2,3,4'
seriesAPI = 'https://www.miguvideo.com/gateway/program/v2/cont/content-info/'

plugin = Plugin()
url_for = plugin.url_for
TIPFMT = '[COLOR magenta][{0}][/COLOR]'

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []


def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

@plugin.route('/playvideo/<pid>/')
def playvideo(pid):
    level = int(plugin.addon.getSetting('resolution'))
    if level != 0: level = -1
    html = get_html(urlAPI % pid)
    data = loads(html)
    data = data['body']
    url = data['urlInfos'][level]['url']
    plugin.set_resolved_url(url)


@plugin.route('/filter/<index>/')
def filter(index):
    data = category[int(index)]
    name = list(data.keys())[0]
    x = data[name]

    dialog = xbmcgui.Dialog()
    result = {}
    for title in ('type', 'area', 'year'):
        sel = dialog.select(title, x[title])
        if sel < 0: sel = 0
        result[title] = x[title][sel]

    return categorylist(index,
                        type=result['type'],
                        area=result['area'],
                        year=result['year'],
                        pack=x['pack'],
                        cont=x['contDisplayType'],
                        Chu=x.get('mediaChu', '0'),
                        page=1)


@plugin.route('/series/<pid>/')
def series(pid):
    plugin.set_content('TVShows')
    html = get_html(seriesAPI + pid)
    data = loads(html)
    data = data['body']['data']
    items = []

    for item in data['datas']:
        t = item.get('duration', '')
        if t == '': t = '0:0:0'
        duration = 0
        for y in t.split(':'):
            duration = 60*duration + int(y)
        items.append({
            'label': item['name'],
            'path': url_for('playvideo', pid=item['pID']),
            'thumbnail': item['h5pics']['lowResolutionH'],
            'is_playable': True,
            'info': {'title': item['name'],
                     'plot': item['detail'],
                     'duration': duration,
                    }
        })
    return items


@plugin.route('/categorylist/<index>/<type>/<area>/<year>/<pack>/<cont>/<Chu>/<page>/')
def categorylist(index, type, area, year, pack, cont, Chu, page):
    plugin.set_content('TVShows')
    pagesize = 20
    req = {
        'packId': pack,
        'pageStart': page,
        'pageNum': pagesize,
        'contDisplayType': cont,
        #'mediaShape': '全片',
        'order': 2,
        'mediaType': '' if type=='全部' else type,
        'mediaArea': '' if area=='全部' else area,
        'mediaYear': '' if year=='全部' else year,
        'mediaChu': '' if Chu=='0' else Chu,
        'ct': 101,
    }

    html = get_html(cateAPI + urlencode(req))
    data = loads(html)
    total = int(data.get('resultNum', 0))
    total_page = (total + pagesize - 1) // pagesize
                         
    items = previous_page('categorylist', page, total_page, index=index,
                          type=type, area=area, year=year,
                          pack=pack, cont=cont, Chu=Chu)

    items.append({
        'label': '[COLOR yellow][分类][/COLOR]',
        'path': url_for('filter', index=index)
    })

    data = data['body']
    for item in data['data']:
        t = item.get('duration', '')
        if t == '': t = '0:0:0'
        duration = 0
        for y in t.split(':'):
            duration = 60*duration + int(y)
        pic = item['h5pics']['lowResolutionH']
        try:
            tip = item['tip']['msg']
            title = item['name'] + TIPFMT.format(tip)
        except:
            title = item['name']
        if duration == 0:
            update = item.get('updateEP', '')
            if update:
                update = '('+ update +')'

            items.append({
                'label': title + update,
                'path': url_for('series', pid=item['pID']),
                'thumbnail': pic,
                'info': {'title': item['name'],
                         'plot': item['detail'],
                         'rating': float(item['score'])
                        }
            })
        else:
            items.append({
                'label': title,
                'path': url_for('playvideo', pid=item['pID']),
                'thumbnail': pic,
                'is_playable': True,
                'info': {'title': item['name'],
                         'plot': item['detail'],
                         'duration': duration,
                         'rating': float(item['score'])
                        }
            })

    items += next_page('categorylist', page, total_page, index=index,
                       type=type, area=area, year=year,
                       pack=pack, cont=cont, Chu=Chu)
    return items


@plugin.route('/')
def index():
    for index, dic in enumerate(category):
        cl = list(dic.keys())[0]
        yield {
            'label': cl,
            'path': url_for('categorylist',
                            index=index,
                            type=dic[cl]['type'][0],
                            area=dic[cl]['area'][0],
                            year=dic[cl]['year'][0],
                            pack=dic[cl]['pack'],
                            cont=dic[cl]['contDisplayType'],
                            Chu=dic[cl].get('mediaChu', 0),
                            page=1
                           )
            }


if __name__ == '__main__':
    plugin.run()
