#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
import xbmcaddon
from urllib import urlencode
from json import loads
from common import get_html
from yinyuetai import video_from_vid

##########################################################################
# 音悦台MV
##########################################################################

__addon__     = xbmcaddon.Addon()

plugin = Plugin()
url_for = plugin.url_for

@plugin.route('/playvideo/<vid>')
def playvideo(vid):
    v_url = video_from_vid(vid)
    url = 'stack://' + ' , '.join(v_url)
    plugin.set_resolved_url(url)


@plugin.route('/setfilters')
def setfilters():
# a=ML
    AREA_LIST = {'全部': '0', '内地':'ML', '港台':'HT', '欧美':'US',
             '韩国': 'KR', '日本':'JP', '二次元':'ACG','其他': 'Other'}
# p=Boy
    PERSONS = {'全部': '0', '男艺人': 'Boy', '女艺人': 'Girl',
           '乐队组合': 'Combo', '其他': 'Other'}

# c=hd, shd..., 画质
    dialog = xbmcgui.Dialog()

    title = u'艺人地区'
    keyword = AREA_LIST.keys()
    sel = dialog.select(title, keyword)
    area = '0' if sel < 0 else AREA_LIST[keyword[sel]]

    title = u'艺人类别'
    keyword = PERSONS.keys()
    sel = dialog.select(title, keyword)
    person = '0' if sel < 0 else PERSONS[keyword[sel]]
    return videolist(sid=0, tid=0, page=1, area=area, person=person)


@plugin.route('/videolist/<sid>/<tid>/<page>/<area>/<person>')
def videolist(sid, tid, page, area, person):
    plugin.set_content('videos')
    res = int(__addon__.getSetting('video_resolution'))
    reslist = ('hd', 'shd', 'sh')

    page = int(page)
    req = {
        'sid': sid,
        'tid': tid,
        'a': '' if area == '0' else area,
        'p': '' if person == '0' else person,
        'c': reslist[res],
        's': '',
        'pageSize': 20,
        'page': page
    }
    
    data = urlencode(req)
    mvapi = 'http://mvapi.yinyuetai.com/mvchannel/so?'
    html = get_html(mvapi + data)
    results = loads(html)
    totalpage = int(results['pageInfo']['pageCount'])
    results = results['result']

    items = []
    if page > 1:
        items.append({
            'label': u'上一页 ({}/{})'.format(page-1, totalpage),
            'path': url_for('videolist',
                            sid=sid,
                            tid=tid,
                            page=page-1,
                            area=area,
                            person=person)
        })

    for item in results:
        d = item.get('duration', '0:0:0')
        duration = 0
        for t in d.split(':'):
            duration = duration*60 + int(t)

        items.append({
            'label': item['title'],
            'path': url_for('playvideo', vid=item['videoId']),
            'thumbnail': item['image'],
            'is_playable': True,
            'info': {'title': item['title'],
                     'plot': item['description'],
                     'duration': duration}
        })
    if page < totalpage:
        items.append({
            'label': u'下一页 ({}/{})'.format(page+1, totalpage),
            'path': url_for('videolist',
                            sid=sid,
                            tid=tid,
                            page=page+1,
                            area=area,
                            person=person)
        })

    return items


@plugin.route('/mainlist/<sid>/<tid>/<page>/<area>/<person>')
def mainlist(sid, tid, page, area, person):
    catapi = 'http://mvapi.yinyuetai.com/cata/get-cata?cataId=%s'
    items = [{
        'label': u'[选择地区/类别]',
        'path': url_for('setfilters')
    }]

    html = get_html(catapi % sid)
    catas = loads(html)['catas']
    catas.insert(0, {'cataName': u'全部', 'cataId': -1})
    for item in catas:
        tid = item['cataId']
        tid = tid if int(tid) > 0 else 0
        items.append({
            'label': item['cataName'],
            'path': url_for('videolist', sid=sid, tid=tid, page=page, area=area, person=person)
        })
    return items


@plugin.route('/')
def root():
    items = [
        ('全部', '0'),
        ('音乐视频', '3'),
        ('现场/live','4'),
        ('娱乐视频', '9'),
        ('舞蹈', '5'),
        ('演奏', '6'),
        ('ACG', '7'),
        ('戏剧', '8')]

    for (name, sid) in items:
        path = 'videolist' if sid == '0' else 'mainlist'
        yield {
            'label': name,
            'path': url_for(path,
                            sid=sid,
                            tid='0',
                            page=1,
                            area='0',
                            person='0')
        }


if __name__ == '__main__':
    plugin.run()
