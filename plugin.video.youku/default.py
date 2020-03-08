#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui, xbmc
from xbmcgui import ListItem
from json import loads
import re
from common import get_html
from lib.youku import video_from_vid, video_from_url, urlencode, quote_plus

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

BANNER_FMT = '[COLOR gold][%s][/COLOR]'

plugin = Plugin()
url_for = plugin.url_for

def httphead(url):
    if len(url) < 2:
        return url
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = 'https://list.youku.com' + url

    return url

category = [
    {'剧集':['show', 97,
               ['古装','武侠','警匪','军事','神话','科幻','悬疑','历史','儿童',
                '农村','都市','家庭','搞笑','偶像','时装','优酷出品']]},
    {'电影':['show', 96,
               ['武侠','警匪','犯罪','科幻','战争','恐怖','惊悚','纪录片','西部',
                '戏曲','歌舞','奇幻','冒险','悬疑','历史','动作','传记','动画','儿童',
                '喜剧','爱情','剧情','运动','短片','优酷出品']]},
    {'综艺':['show', 85,
               ['热门','网综','优酷','牛人','脱口秀','真人秀','选秀','美食','旅游',
                '汽车','访谈','纪实','搞笑','时尚','晚会','理财','演唱会','曲艺',
                '益智','音乐','舞蹈','游戏','生活']]},
    {'动漫':['show', 100,
               ['热血','格斗','恋爱','美少女','校园','搞笑','LOLI','神魔','机战',
                '科幻','真人','青春','魔法','神话','冒险','运动','竞技','童话','亲子',
                '教育','励志','剧情','社会','历史','战争']]},
    {'少儿':['show', 177,
               ['动画','儿歌','绘本','故事','玩具','早教','艺术','探索纪实','少儿综艺',
                '亲子','英语','国学','课程辅导','人际交往','情商','认知启蒙','科普',
                '冒险','幽默','友情','益智','战斗','科幻','魔法','亲情','数学',
                '动物','热血']]},
    {'音乐':['show', 95,
               ['流行','摇滚','舞曲','电子','R&B','HIP-HOP','乡村','民族','民谣',
                '拉丁','爵士','雷鬼','新世纪','古典','音乐剧','轻音乐']]},
    {'教育':['show', 87,
               ['公开课','名人名嘴','文化','艺术','伦理','社会','理工','历史','心理学',
                '经济','政治','管理学','外语','法律','计算机','哲学','职业培训',
                '家庭教育']]},
    {'纪实':['show', 84,
               ['人物','军事','历史','自然','古迹','探险','科技','文化','刑侦',
                '社会','旅游']]},
    {'体育':['show', 98,
               ['奥运会','世界杯','格斗','足球','篮球','健身','跑步','广场舞',
                '综合','棋牌','电竞','冰壶','冰球','滑雪','滑冰','雪车雪撬','射击']]},
    {'文化':['show', 178, []]},

    {'娱乐':['show', 86, ['明星资讯','电影资讯','电视资讯','音乐资讯']]},
    {'游戏':['show', 99, []]},
    {'资讯':['video', 91,
               ['社会资讯','科技资讯','生活资讯','军事资讯','财经资讯','时政资讯',
                '法制']]},
    {'搞笑':['video', 94,
               ['恶搞短片','搞笑自拍','萌宠奇趣','搞笑达人','影视剧吐槽','恶搞配音',
                '欢乐街访','鬼畜']]},
    {'生活':['video', 103,
               ['休闲','美食','聚会','宠物','居家','健康','家居','女性','婚恋',
                '潮品','记录','生活达人']]},
    {'汽车':['video', 104, []]},
    {'科技':['video', 105,
               ['数码','IT','手机','笔记本','DC/DV','MP3/MP4','数字家电','GPS',
                '游戏机','App','平板','科技达人']]},
    {'时尚':['video', 89,
               ['美容','修身','服装服饰','时尚购物','潮人','情感星座','时尚达人',
                '美容达人']]},
    {'亲子':['video', 90,
               ['怀孕','育儿','早教','宝宝秀','搞笑儿童','妈妈']]},
    {'旅游':['video', 88,
               ['国内游','出境游','旅游业界','交通住宿','旅游用品','城市','乡村古镇',
                '游轮岛屿','人文景点','自然景点','节庆活动','户外运动',
                '攻略指南','旅游达人']]},
    {'微电影':['video', 171, []]},
    {'网剧':['video', 172, []]},
    {'拍客':['video', 174, []]},
    {'创意视频':['video', 175, []]},
    {'自拍':['video', 176, []]},
    {'广告':['video', 102, []]},
]


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


@plugin.route('/playvideo/<videoid>/<name>/')
def playvideo(videoid, name):
    level = int(plugin.addon.getSetting('resolution'))

    urls = video_from_vid(videoid, level=level)
    if len(urls) > 1:
        stackurl = 'stack://' + ' , '.join(urls)
        list_item = ListItem(name)
        list_item.setInfo(type="video", infoLabels={"Title": name})
        xbmc.Player().play(stackurl, list_item)
    else:
        plugin.set_resolved_url(urls[0])


@plugin.route('/select/<cid>/')
def select(cid):
    for item in category:
        title = item.keys()[0]
        if str(item[title][1]) == cid:
            type= item[title][0]
            g = item[title][2]
            break

    dialog = xbmcgui.Dialog()

    sel = dialog.select('类型', g)
    group = g[sel] if sel >= 0 else '0'

    return mainchannel(type=type, cid=cid, group=group, page=1)

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
            'path': url_for('episodelist', vid=item['showid']),
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
            'path': url_for('playvideo', videoid=item['videoId'], name=item['title']),
            'thumbnail': item['img'],
            'is_playable': True,
            'info': {'title': item['title'], 'plot': item['desc'],
                     'duration': duration}
        })
    return items


@plugin.route('/episodelist/<vid>/')
def episodelist(vid):
    plugin.set_content('TVShows')
    url = 'http://v.youku.com/v_show/id_{0}.html'.format(vid)
    page = get_html(url)

    m = re.search('__INITIAL_DATA__\s*=({.+?\});', page)
    
    p = loads(m.group(1))
    series = p['data']['data']['nodes'][0]['nodes'][2]['nodes']
    content = p['data']['data']['nodes'][0]['nodes'][0]['nodes'][0]['data']['desc']
    items = []
    for film in series:
        vid = film['data']['action']['value']
        title = film['data']['title'].encode('utf-8')

        items.append({
            'label': title,
            'path': url_for('playvideo', videoid=vid, name=title),
            'thumbnail': film['data']['img'],
            'is_playable': True,
            'info': {'title': title, 'plot': content}
        })

    return items

series = (97, 85, 100, 177, 87, 84, 98, 178, 86, 99) 

@plugin.route('/mainchannel/<type>/<cid>/<group>/<page>/')
def mainchannel(type, cid, group, page):
    plugin.set_content('TVShows')
    api = 'https://list.youku.com/category/page?'
    req = {
        'type': type,
        'c': cid,
        'p': page,
        'g': '' if group == '0' else group
    }

    html = get_html(api + urlencode(req))
    data = loads(html)

    items = previous_page('mainchannel', page, 300, type=type, cid=cid, group=group)
    if group == '0': c = '分类'
    else: c = '分类' + '|' + group
    items.append({
        'label': '[COLOR yellow][{0}][/COLOR]'.format(c),
        'path': url_for('select', cid=cid)
    })
    for item in data['data']:
        items.append({
            'label': item['title'] + '(' + item['summary'] +')',
            'thumbnail': httphead(item['img']),
            'info': {'title': item['title'], 'plot': item.get('subTitle', '')}
        })
        if int(cid) in series:
            items[-1]['path'] = url_for('episodelist', vid=item['videoId'])
        else:
            items[-1]['path'] = url_for('playvideo',
                                        videoid=item['videoId'],
                                        name=item['title'].encode('utf-8'))
            items[-1]['is_playable'] = True

    items += next_page('mainchannel', page, 300, type=type, cid=cid, group=group)

    return items

@plugin.route('/')
def index():
    items = []
    items.append({
        'label': '[COLOR magenta][搜索][/COLOR]',
        'path': url_for('search')
    })
    for item in category:
        title = item.keys()[0]
        items.append({
            'label': title,
            'path': url_for('mainchannel',
                            type=item[title][0],
                            cid=item[title][1],
                            group=0,
                            page=1)
        })
    return items


if __name__ == '__main__':
    plugin.run()
