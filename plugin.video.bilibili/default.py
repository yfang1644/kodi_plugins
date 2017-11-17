#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from xbmcgui import ListItem
import xbmcplugin
import xbmcaddon
from urllib import urlencode
from urlparse import parse_qsl
from resources.lib.bilibili import Bilibili
from resources.lib.subtitle import subtitle_offset
import time
import string, os
from random import choice
from json import loads
from common import get_html
from qq import video_from_vid

try:
    from resources.lib.login_dialog import LoginDialog
except:
    #Debug for xbmcswift2 run from cli
    pass

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__cwd__       = __addon__.getAddonInfo('path')
__icon__      = __addon__.getAddonInfo('icon')

bilibili = Bilibili()
tempdir = xbmc.translatePath('special://home/temp')

class BiliPlayer(xbmc.Player):
    def __init__(self):
        self.subtitle = ""
        self.show_subtitle = False

    def setSubtitle(self, subtitle):
        if len(subtitle) > 0:
            self.show_subtitle = True
        else:
            self.show_subtitle = False
        self.subtitle = subtitle

    def onPlayBackStarted(self):
        time = float(self.getTime())
        if self.show_subtitle:
            if time > 1:
                self.setSubtitles(subtitle_offset(self.subtitle, -time))
            else:
                self.setSubtitles(self.subtitle)
        else:
            self.showSubtitles(False)

# helper function
def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        prev = dict(**kwargs)
        prev['page'] = page
        prev['mode'] = endpoint
        prev['label'] = '上一页 - {0}/{1}'.format(page, str(total_page))
        return [prev]
    else:
        return []


def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        next = dict(**kwargs)
        page = str(int(page) + 1)
        next = dict(**kwargs)
        next['page'] = page
        next['mode'] = endpoint
        next['label'] = '下一页 - {0}/{1}'.format(page, str(total_page))
        return [next]
    else:
        return []


def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict


def showPlayList(items):

    for item in items:
        thumb = item.get('thumbnail')
        li = ListItem(item['label'], thumbnailImage=thumb)
        info = item.get('info')
        li.setInfo(type='Video', infoLabels=info)
        u = sys.argv[0]
        data = urlencode(encoded_dict(item))
        dir = False if item['mode'] == 'play' else True
        u = sys.argv[0] + '?' + data
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, isFolder=dir)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def play(params):
    cid = params.get('cid')
    vid = params.get('vid')
    name = params.get('name', u'播放')
    if vid is not None and len(vid) > 0:        # QQ
        urls = video_from_vid(vid, level=0)
    else:
        urls = bilibili.get_video_urls(cid)
    stack_url = 'stack://' + ' , '.join(urls)

    print '-=============================', cid, urls
    danmu = __addon__.getSetting('danmu')

    playlist = xbmc.PlayList(1)
    playlist.clear()
    player = BiliPlayer()
    list_item = ListItem(name)
    playlist.add(stack_url, list_item)

    if danmu == 'true':
        bilibili.parse_subtitle(cid)
        player.setSubtitle(bilibili._get_tmp_dir() + '/tmp.ass')
    else:
        player.showSubtitles(False)
        player.show_subtitle = False

    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(500)


def list_video(params):
    aid = params.get('aid')
    result = bilibili.get_av_list(aid)

    for x in result:
        li = ListItem(x['pagename'])
        vid = x.get('vid', '')
        u = sys.argv[0] + '?mode=play'
        u += '&cid=%s&vid=%s&name=%s' % (x['cid'], vid, x['pagename'])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_av_item(aid, label):
    result = bilibili.get_av_list(aid)
    if not result:
        return {'label': u'(空)'}

    item = {'label': label}

    if len(result) == 1:
        vid = result[0].get('vid', '')
        if len(vid) > 0:
            item['label'] += '(QQ)'
   
        item['cid'] = result[0]['cid']
        item['vid'] = vid
        item['mode'] = 'play'
    else:
        item['mode'] = 'list_video'
        item['aid'] = aid
    return item


def searchResult(page, keyword):
    searchapi = 'https://search.bilibili.com/ajax_api/video?keyword=%s&page=%s&order=totalrank'
    html = get_html(searchapi % (quote_plus(keyword), str(page)), decoded=False)
    html = html.replace('\\"', '')
    html = html.replace('\\t', '')
    html = html.replace('\\n', '')

    js = loads(html)
    total = js['numResults']
    total_page = js['numPages']
    tree = BeautifulSoup(js['html'], 'html.parser')

    videos = tree.find_all('li')
    items = previous_page('searchResult', page, total_page, keyword=keyword)

    for item in videos:
        aid = item.i['data-aid']
        thumb = item.img['data-src']
        if thumb[0:2] == '//':
            thumb = 'https:' + thumb
        title = item.find('a', {'class': 'title'}).text
        desc = item.find('div', {'class': 'des'})
        if desc is not None:
            desc = desc.text
        genre = item.find('span', {'class': 'type'}).text

        info = {
            'plot': desc,
            'genre': genre
        }
        items.append(get_av_item(aid, label=title, thumbnail=thumb, info=info))
    items += next_page('searchResult', page, total_page, keyword=keyword)

    showPlayList(items)


# 按 av 号搜索
#https://search.bilibili.com/all?keyword=xxxxx&from_source=banner_search
def search():
    keyboard = xbmc.Keyboard('', '请输入关键字(片名或AV)')
    xbmc.sleep(1500)
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        searchResult(page=1, keyword=keyword)


# 视频分类
def category(params):
    tid = params['tid']
    results = bilibili.get_category(tid)

    for data in results:
        tid = data.keys()[0]
        value = data.values()[0]
        if not value.has_key('subs') or len(value['subs']) == 0:
            mode = 'mode=category_tag'
        else:
            mode = 'mode=category'
        u = sys.argv[0] + '?{}&tid={}'.format(mode, tid)
        li = ListItem(value['title'])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def category_tag(params):
    orderapi = 'https://api.bilibili.com/x/tag/hots?rid={}'
    tid = params.get('tid')
    html = get_html(orderapi.format(tid))
    jsdata = loads(html)
    tags = jsdata['data'][0]['tags']

    li = ListItem(u'全部')
    u = sys.argv[0] + '?mode=category_list&page=1&tid={}'.format(tid)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    for item in tags:
        li = ListItem(item['tag_name'])
        u = sys.argv[0] + '?mode=category_list&page=1'
        u += '&tag={}&tid={}'.format(item['tag_id'], tid)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def category_list(params):
    tag = params.get('tag', 0)
    tid = params.get('tid')
    page = params.get('page')

    lists = bilibili.get_category_by_tag(tag=tag, tid=tid, page=page)

    archives = lists['data']['archives']
    size = lists['data']['page']['size']
    count = lists['data']['page']['count']
    total_page = (count + size - 1) // size

    items = previous_page('category_list', page, total_page, tid=tid, tag=tag)

    for item in archives:
        x = archives[item] if tag == 0 else item
        info = {
            'genre': x.get('tname'),
            'writer': x.get('author'),
            'plot': x.get('description'),
            'duration': x.get('duration'),
        }
        try:
            info['year'] = int(x['create'][:4])
        except:
            pass

        li = get_av_item(x['aid'], x['title'])
        li['info'] = info
        li['thumbnail'] = x['pic']
        items.append(li)
    items += next_page('category_list', page, total_page, tid=tid, tag=tag)

    showPlayList(items)

# 我的动态
def dynamic(params):
    page = params.get('page')
    result, total_page = bilibili.get_dynamic(page)

    items = previous_page('dynamic', page, total_page)
    for item1 in result:
        item = item1['addition']
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'genre': item['typename'],
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(item['create'][:4])
        except:
            pass
        li = get_av_item(item['aid'], item['title'])
        li['info'] = info
        li['thumbnail'] = item['pic']
        items.append(li)
    items += next_page('dynamic', page, total_page)

    showPlayList(items)

#  我的历史
def history(params):
    page = params.get('page')
    result, total_page = bilibili.get_history(page)

    items = previous_page('history', page, total_page)
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass

        li = get_av_item(item['aid'], item['title'])
        li['info'] = info
        li['thumbnail'] = item['pic']
        items.append(li)
    items += next_page('history', page, total_page)

    showPlayList(items)


# 我的收藏
def fav_box(params):
    for item in bilibili.get_fav_box():
        li = ListItem(item['label'])
        u = sys.argv[0] + '?mode=fav&fav_box=%s&page=1' % (item['fav_box'])
        data = urlencode(encoded_dict(item))
        u = sys.argv[0] + '?' + data
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def fav(params):
    fav_box = params.get('fav_box')
    page = params.get('page')
    result, total_page = bilibili.get_fav(fav_box, page)
    items = previous_page('fav', page, total_page, fav_box=fav_box)
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
        }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        li = get_av_item(item['aid'], item['title'])
        li['info'] = info
        li['thumbnail'] = item['pic']
        items.append(li)
    items += next_page('fav', page, total_page, fav_box=fav_box)

    showPlayList(items)

# 我的追番
def bangumi_chase(params):
    page = params.get('page')
    result, total_page = bilibili.get_bangumi_chase(page)
    items = previous_page('bangumi_chase', page, total_page)
    for item in result:
        info = {
            'plot': item['brief'],
            }
        title = item['title']
        if item['is_finish'] == 0:
            title += u'【更新至第{0}集】'.format(item['newest_ep_index'])
        else:
            title += u'【已完结】'
        items.append({
            'label': title,
            'mode': 'season',
            'season_id': item['season_id'],
            'thumbnail': item['cover'],
            'info': info,
            })
    items += next_page('bangumi_chase', page, total_page)

    showPlayList(items)


def season(season_id):
    result = bilibili.get_bangumi_detail(season_id)
    bangumi_info = {
        'genre': '|'.join([tag['tag_name'] for tag in result['tags']]),
        'episode': len(result['episodes']),
        'castandrole': [u'{}|{}'.format(actor['actor'], actor['role']) for actor in result['actor']],
        'director': result['staff'],
        'plot': result['evaluate'],
    }

    items = []
    for item in result['episodes']:
        info = dict(bangumi_info)
        try:
            info['year'] = int(item['update_time'][:4])
        except:
            pass
        title = u'【第{}话】'.format(item['index'])
        title += item['index_title']
        if item.get('is_new', '0') == '1':
            title += u'【新】'

        li = get_av_item(item['av_id'])
        li['label'] = title
        li['thumbnail'] = item['cover']
        li['info'] = info

    showPlayList(items)


# 我的关注
def attention(params):
    page = params.get('page')
    result = bilibili.get_attention(page)
    items = [{
        'mode': 'user_info',
        'mid': item['mid'],
        'label': item['uname'],
        'thumbnail': item['face'],
    } for item in result]

    showPlayList(items)


def attention_video(params):
    mid = params.get('mid')
    tid = params.get('tid')
    page = params.get('page')
    result, total_page = bilibili.get_attention_video(mid, tid, page)
    items = []
    for item in result['vlist']:
        duration = 0
        for t in item['length'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['created'])))
        except:
            pass
        try:
            info['genre'] = bilibili.get_category_name(item['typeid'])
        except:
            pass

        li = get_av_item(item['aid'], item['title'])
        li['info'] = info
        li['thumbnail'] = item['pic']
        items.append(li)
    items += next_page('attention_video', page, total_page, mid=mid, tid=tid)

    showPlayList(items)


def attention_channel_list(params):
    mid = params.get('mid')
    cid = params.get('cid')
    page = params.get('page')
    result, total_page = bilibili.get_attention_channel_list(mid, cid, page)
    items = []
    for item1 in result_info:
        item = item1['info']
        info = {
            'genre': item['tname'],
            'plot': item['desc'],
            'duration': item['duration'],
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        li = get_av_item(item['aid'], item['title'])
        li['info'] = info
        li['thumbnail'] = item['pic']
        items.append(li)
    items += next_page('attention_channel_list', page, total_page, mid = mid, cid = cid)

    showPlayList(items)


def attention_channel(params):
    mid = params.get('mid')
    result = bilibili.get_attention_channel(mid)

    for item in result:
        title = u'{} ({}个视频) ({}更新)'.format(item['name'], str(item['count']), item['modify_time'][:10])
        li = ListItem(title)
        u = sys.argv[0]
        data = 'mode=attention_channel_list&mid={}&cid={}&page=1'.format(mid, item['id'])
        u = sys.argv[0] + '?' + data
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def user_info(params):
    mid = params.get('mid')
    result, total_page = bilibili.get_attention_video(mid, 0, 1, 1)
    items = []
    items.append({
        'mode': 'attention_channel',
        'label': u'频道',
        'mid': mid
        })
    title = u'{} ({}个视频)'.format(u'全部', str(result['count']))
    items.append({
        'mode': 'attention_video',
        'label': title,
        'mid': mid,
        'tid': 0,
        'page': 1
        })
    for item in result['tlist'].values():
        title = u'{} ({}个视频)'.format(item['name'], str(item['count']))
        items.append({
            'mode': 'attention_video',
            'label': title,
            'mid': mid,
            'tid': item['tid'],
            'page': 1
            })

    for item in items:
        li = ListItem(item['label'])
        u = sys.argv[0]
        data = urlencode(encoded_dict(item))
        u = sys.argv[0] + '?' + data
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# 登录与注销
def login():
    if bilibili.is_login == False:
        username = __addon__.getSetting('username')
        password = __addon__.getSetting('password')
        if username == '' or password == '':
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%('LOGIN',
                            '请设置用户名密码', 1000, __icon__))
            __addon__.openSettings()
            username = __addon__.getSetting('username')
            password = __addon__.getSetting('password')
            if username == '' or password == '':
                xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%('LOGIN',
                            '用户名或密码为空', 1000, __icon__))
                return
        filename = tempdir + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10)) + '.jpg'
        captcha = LoginDialog(captcha = bilibili.get_captcha(filename)).get()
        os.remove(filename)
        result, msg = bilibili.login(username, password, captcha)
        if result == True:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%('LOGIN', '登录成功', 1000, __icon__))
        else:
            xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%('LOGIN', msg, 1000, __icon__))


def logout():
    bilibili.logout()


def mainMenu():
    items = [
        {'label': u'视频搜索', 'mode': 'search'},
        {'label': u'视频分类', 'mode': 'category', 'tid': '0'},
    ]
    if bilibili.is_login:
        items += [
            {'label': u'我的动态', 'mode': 'dynamic', 'page': '1'},
            {'label': u'我的历史', 'mode': 'history', 'page': '1'},
            {'label': u'我的收藏', 'mode': 'fav_box'},
            {'label': u'我的追番', 'mode': 'bangumi_chase', 'page': '1'},
            {'label': u'我的关注', 'mode': 'attention', 'page': '1'},
            {'label': u'退出登录', 'mode': 'logout'},
        ]
    else:
        items += [
            {'label': u'登录账号', 'mode': 'login'},
        ]

    for item in items:
        li = ListItem(item['label'])
        item.pop('label')
        data = urlencode(item)
        u = sys.argv[0] + '?' + data
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'mainMenu()',
    'search': 'search()',
    'category': 'category(params)',
    'dynamic': 'dynamic(params)',
    'history': 'history(params)',
    'fav_box': 'fav_box(params)',
    'fav': 'fav(params)',
    'bangumi_chase': 'bangumi_chase(params)',
    'attention': 'attention(params)',
    'user_info': 'user_info(params)',
    'attention_video': 'attention_video(params)',
    'attention_channel': 'attention_channel(params)',
    'logout': 'logout()',
    'login': 'login()',
    'category_tag': 'category_tag(params)',
    'category_list': 'category_list(params)',
    'list_video': 'list_video(params)',
    'play': 'play(params)',
}

exec(runlist[mode])
