#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import sys
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
sys.path.append(os.path.join(ADDON_PATH, 'resources', 'lib'))

from xbmcswift2 import Plugin, ListItem, xbmc, xbmcgui

from rrmj import RenRenMeiJu
from acfun import video_from_url as video_from_acfun
from youku import video_from_url as video_from_youku

from urlparse import parse_qsl
from urllib import urlencode
from json import loads, dumps
import sqlite3

CATLIST = [
    '爱情',
    '剧情',
    '喜剧',
    '科幻',
    '动作',
    '犯罪',
    '冒险',
    '家庭',
    '战争',
    '悬疑',
    '恐怖',
    '历史',
    '伦理',
    '罪案',
    '警匪',
    '惊悚',
    '奇幻',
    '魔幻',
    '青春',
    '都市',
    '搞笑',
    '纪录片',
    '时装',
    '动画',
    '音乐']

plugin = Plugin()
url_for = plugin.url_for

conn = sqlite3.connect(ADDON_PATH + '/local.db')
cur = conn.cursor()

Meiju = RenRenMeiJu()
PAGE_ROWS = int(plugin.get_setting('page_rows'))
SEASON_CACHE = plugin.get_storage('season')
HISTORY = plugin.get_storage('history')


def setSettingByRPC(key, value):
    """Set Kodi Setting by JSON-RPC

    Args:
        key (TYPE): Description
        value (TYPE): Description

    Returns:
        TYPE: Description
    """
    result = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Settings.SetSettingValue", "params":{"setting":"%s", "value":%s}, "id":1}' % (key, value))
    result = loads(result)
    return result


def set_auto_play():
    auto_play_setting = plugin.get_setting("auto_next")
    print setSettingByRPC("videoplayer.autoplaynextitem", auto_play_setting)


def colorize(label, color):
    return '[COLOR %s]%s[/COLOR]' % (color, label)


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


def remap_url(req_url):
    array = req_url.split("?")
    params = dict(parse_qsl(array[1]))
    if array[0] == "/video/search":
        endpoint = "search"
        if "cat" in params:
            endpoint = "cat_list"
        elif "mark" in params:
            endpoint = "mark_list"
    elif array[0] == "/video/album":
        endpoint = "album"
    return url_for(endpoint, **params)


@plugin.route('/uskseason')
def uskseason():
    seasonlist = Meiju.season_index(area='USK')
    total = seasonlist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS

    for x in seasonlist['data']['results']:
        items.append({
            'label': x['title'],
            'path': url_for('detail', seasonId=x['id'])
        })
    return items

@plugin.route('/categorylist/<area>/<catname>')
def categorylist(area, catname):
    dialog = xbmcgui.Dialog()
    sel = dialog.select('分类', ['全部'] + CATLIST)
    if sel == 0:
        catname = '0'
    elif sel > 0:
        catname = CATLIST[sel-1]

    return season(1, area, catname)


@plugin.route('/season/<page>/<area>/<catname>')
def season(page, area, catname):
    plugin.set_content('TVShows')
    items = [{
        'label': colorize('分类--'+catname, 'yellow'),
        'path': url_for('categorylist', area=area, catname=catname)
    }]

    seasonlist = Meiju.search(page,
                              PAGE_ROWS,
                              area=area,
                              category='' if catname=='全部' else catname)
    total = seasonlist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS
    items += previous_page('season',
                           page,
                           total_page,
                           area=area,
                           catname=catname)
    for x in seasonlist['data']['results']:
        status = u'(完结)' if x['finish'] else u'(更新到{})'.format(x['upInfo'])
        items.append({
            'label': x['title'] + status,
            'path': url_for("detail", seasonId=x['id']),
            'thumbnail': x.get('cover'),
            'info': {
                'title': x['title'],
                'plot': x.get('brief'),
                'rating': float(x['score']),
                'genre': ''
            }
        })

    items += next_page('season',
                       page,
                       total_page,
                       area=area,
                       catname=catname)
    return items


@plugin.route('/movieCatList/<catid>')
def movieCatList(catid):
    moviecat = Meiju.movie_catname()['data']['categoryList']
    dialog = xbmcgui.Dialog()
    catlist = [x['name'] for x in moviecat]
    sel = dialog.select('分类(可能不全)', ['全部'] + catlist)
    catid = moviecat[sel-1]['id'] if sel > 0 else '0'

    return movies(1, catid)


@plugin.route('/movies/<page>/<catid>')
def movies(page, catid):
    plugin.set_content('TVShows')
    items = [{
        'label': colorize('分类','yellow'),
        'path': url_for('movieCatList', catid=catid)
    }]

    movielist = Meiju.movie_query(page,
                                  PAGE_ROWS,
                                  categoryId='' if catid == '0' else catid)
    total = movielist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS

    items += previous_page('movies', page, total_page, catid=catid)
    for x in movielist['data']['results']:
        t = x.get('duration', '')
        if t == '': t = '0:0:0'
        duration = 0
        for y in t.split(':'):
            duration = 60*duration + int(y)
        items.append({
            'label': x['title'],
            'path': url_for('videodetail',
                            videoId=x['id'],
                            title=x['title'].encode('utf-8')),
            'thumbnail': x['cover'],
            'is_playable': True,
            'info': {'title': x['title'],
                     'plot': x['brief'],
                     'duration': duration}
        })

    items += next_page('movies', page, total_page, catid=catid)
    return items


@plugin.route('/videodetail/<videoId>/<title>')
def videodetail(videoId, title):
    video = Meiju.video_detail(videoId)
    play_url = video['data']['playLink']
    if play_url:
        play_url = play_url.split('|')
    else:
        video = Meiju.video_detail2(videoId)
        url = video['data']['videoDetailView']['playLink']
        if 'acfun' in url:
            play_url = video_from_acfun(url)
        elif 'youku' in url:
            play_url = video_from_youku(url)
        else:
            xbmcgui.Dialog().ok('视频地址' + url.encode('utf-8'),
                                '请使用其他插件搜索播放')
            return

    stackurl = 'stack://' + ' , '.join(play_url)
    plugin.set_resolved_url(stackurl)
    


@plugin.route('/leafCategory/<catid>/<page>')
def leafCategory(catid, page):
    plugin.set_content('videos')
    leaflist = Meiju.cat_index(page, PAGE_ROWS, categoryId=catid)

    total = leaflist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS
    items = previous_page('leafCategory', page, total_page, catid=catid)

    for x in leaflist['data']['results']:
        t = x.get('duration', '')
        if t == '': t = '0:0:0'
        duration = 0
        for y in t.split(':'):
            duration = 60*duration + int(y)
        items.append({
            'label': x['title'],
            'path': url_for('videodetail',
                            videoId=x['id'],
                            title=x['title'].encode('utf-8')),
            'thumbnail': x['cover'],
            'is_playable': True,
            'info': {'title': x['title'],
                     'plot': x['brief'],
                     'duration': duration}
        })

    items += next_page('leafCategory', page, total_page, catid=catid)
    return items


@plugin.route('/videos/<info>')
def videos(info):
    js = loads(info)
    items = []
    for y in js:
        items.append({
            'label': y['name'],
            'path': url_for('leafCategory', catid=y['id'], page=1)
        })

    return items


# list catagories
@plugin.route('/category')
def category():
    plugin.set_content('video')
    catlist = Meiju.category()
    items = []
    for x in catlist['data']['category']:
        items.append({
            'label': x['name'],
            'path': url_for('videos', info=dumps(x['leafCategory'])),
        })
    
    items.append({
        'label': '英美剧',
        'path': url_for('season', page=1, area='USK', catname='全部')
    })
    items.append({
        'label': '日韩剧',
        'path': url_for('season', page=1, area='JP', catname='全部')
    })
    items.append({
        'label': '泰剧',
        'path': url_for('season', page=1, area='TH', catname='全部')
    })

    items.append({
        'label': '电影',
        'path': url_for('movies', page=1, catid=0)
    })

    return items



# search entrance
@plugin.route('/hotword/')
def hotword():
    yield {
            'label': colorize('输入关键字搜索', 'yellow'),
            'path': url_for('input_keyword'),
        }
    hotwords = Meiju.hot_word()
    for word in hotwords['data']['wordList']:
        word = word.encode('utf-8')
        item = {
            'label': colorize(word, 'green'),
            'path': url_for('search', title=word, page=1)
        }
        yield item


# get search result by input keyword
@plugin.route('/input_keyword')
def input_keyword():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = url_for('search', title=keyword, page=1)
        plugin.redirect(url)


@plugin.route('/stay')
def stay():
    pass


@plugin.route('/search/<title>/<page>')
def search(title, page):
    plugin.set_content('video')
    searchlist = Meiju.search(name=title)['data']['results']

    items = []
    if searchlist:
        items.append({
            'label': colorize(u'剧集搜索-'+ title.decode('utf-8'), 'yellow'),
            'path': url_for('stay')
        })
    for item in searchlist:
        status = u'(完结)' if item['finish'] else u'(更新到{})'.format(item['upInfo'])
        items.append({
            'label': item['title'] + status,
            'path': url_for("detail", seasonId=item['id']),
            'thumbnail': item.get('url', ''),
            'info': {
                'title': item['title'],
                'plot': item.get('brief', ''),
                'rating': float(item['score']),
                'genre': ''
            }
        })
        #item._listitem.setArt({"poster": one["cover"]})

    # search local
    dt = title.decode('utf-8')
    p = cur.execute('select * from mjindex where name like ?', ('%'+dt+'%',))
    total = p.fetchall()
    if total:
        items.append({
            'label': colorize(u'本地数据库', 'yellow'),
            'path': url_for('stay')
        })
    for item in total:
        items.append({
            'label': item[1],
            'path': url_for('detail', seasonId=item[0])
        })

    # search videos
    searchlist = Meiju.video_search(page, PAGE_ROWS, name=title)['data']
    total = searchlist['total']
    if total:
        items.append({
            'label': colorize(u'其它视频', 'yellow'),
            'path': url_for('stay')
        })
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS
    items += previous_page('search', page, total_page, title=title)
    for x in searchlist['results']:
        t = x.get('videoDuration', 0)
        if int(t) < 0: t = 0
        items.append({
            'label': x['title'],
            'path': url_for('videodetail',
                            videoId=x['id'],
                            title=x['title'].encode('utf-8')),
            'thumbnail': x['url'],
            'is_playable': True,
            'info': {'title': x['title'],
                     'plot': x['brief'],
                     'duration': int(t)}
        })
    items += next_page('search', page, total_page, title=title)

    return items


@plugin.route('/album/<albumId>/', name="album")
def get_album(albumId):
    plugin.set_content('TVShows')
    c_list = Meiju.get_album(albumId)
    for one in c_list['data']['results']:
        yield {
            'label': one['title'],
            'path': url_for('detail', seasonId=one['id']),
            'icon': one['cover'],
            'thumbnail': one['cover'],
            'info': {'title': one['title'],
                     'plot': one.get('brief', ''),
                     'rating': float(one['score']),
                     'genre': one['cat'],
                     'season': one['seasonNo']}
        }


# get season episodes by season id
@plugin.route('/detail/<seasonId>')
def detail(seasonId):
    plugin.set_content('TVShows')
    detail = Meiju.season_detail(seasonId)
    season_data = detail['data']['season']
    title = season_data['title']
    SEASON_CACHE[seasonId] = detail['data']  # store season detail
    history = HISTORY.get('list', [])
    playing_episode = '0'
    for l in history:
        if l['seasonId'] == seasonId:
            playing_episode = l['index']

    items = []
    for episode in season_data['playUrlList']:
        label = title + str(episode['episode'])
        if episode['episode'] == playing_episode:
            label = '[B]' + colorize(label, 'green') + '[/B]'

        items.append({
            'label': label,
            'path': url_for('play_season',
                            seasonId=seasonId,
                            index=episode['episode'],
                            Esid=episode['episodeSid']),
            'thumbnail': season_data['cover'],
            'is_playable': True,
            'info': {'plot': season_data['brief'],
                     'title': title,
                     'episode': int(episode['episode']),
                     'season': 0},
        })

    unsorted = [(dict_['info']['episode'], dict_) for dict_ in items]
    unsorted.sort()
    sorted = [dict_ for (key, dict_) in unsorted]
    return sorted


@plugin.route('/play/<seasonId>/<index>/<Esid>', name='play_season')
def play(seasonId='', index='', Esid=''):
    season_data = SEASON_CACHE.get(seasonId).get('season')
    title = season_data['title']
    episode_sid = Esid
    play_url, _ = Meiju.get_by_sid(episode_sid, plugin.get_setting('quality'))
    if play_url is not None:
        play_url = play_url.split('|')
        stackurl = 'stack://' + ' , '.join(play_url)
        add_history(seasonId, index, Esid, title)
        li = ListItem(title+index,
                    path=stackurl,
                    thumbnail=season_data.get('cover'))
        li.set_info('video', {'title': title+index,
                              'plot': season_data.get('brief','')})

        plugin.set_resolved_url(li)
    else:
        plugin.set_resolved_url(False)


def add_history(seasonId, index, Esid, title):
    if 'list' not in HISTORY:
        HISTORY['list'] = []
    for l in HISTORY['list']:
        if l['seasonId'] == seasonId:
            HISTORY['list'].remove(l)
    item = {'seasonId': seasonId,
            'index': index,
            'sid': Esid,
            'season_name': title}
    HISTORY["list"].insert(0, item)


@plugin.route('/history')
def history():
    for l in HISTORY.get('list', []):
        seasonId = l['seasonId']
        index = l['index']
        sid = l['sid']
        yield {
            'label': u'[COLOR green]{title}[/COLOR]  观看到第[COLOR yellow]{index}[/COLOR]集'.format(title=l['season_name'], index=l['index']),
            'path': url_for('detail', seasonId=seasonId),
        }


@plugin.route('/update/<page>')
def update(page):
    plugin.set_content('TVShows')
    searchlist = Meiju.update(page, PAGE_ROWS)
    total = searchlist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS

    items = previous_page('update', page, total_page)
    for item in searchlist['data']['results']:
        status = u'(完结)' if item['finish'] else u'(更新到{})'.format(item['upInfo'])
        items.append({
            'label': item['title'] + status,
            'path': url_for("detail", seasonId=item['id']),
            'thumbnail': item.get('cover', ''),
            'info': {
                'title': item['title'],
                'plot': item.get('brief', ''),
                'rating': float(item['score']),
                'genre': ''
            }
        })
        #item._listitem.setArt({"poster": one["cover"]})

    items += next_page('update', page, total_page)
    return items

# main entrance
@plugin.route('/')
def index():
    #set_auto_play()
    yield {
        'label': u'分类',
        'path': url_for('category'),
    }
    yield {
        'label': u'搜索',
        'path': url_for('hotword'),
    }
    yield {
        'label': u'最新',
        'path': url_for('update', page=1),
    }
    yield {
        'label': '历史',
        'path': url_for('history'),
    }
    #mainpage = Meiju.index_info()['data']

    '''
    for serial in mainpage["index"]:
        url = remap_url(str(serial.get("requestUrl")))
        season_list = serial.get("seasonList")
        list_string = " ".join(season["title"] for season in season_list)
        item = {
            'label': "^^^".join([serial.get("title"), list_string]),
            'path': url,
        }
        yield item
    for album in mainpage["album"]:
        url = remap_url(str(album.get("requestUrl")))
        item = {
            'label': album["name"],
            'path': url,
            'icon': album["coverUrl"],
            'thumbnail': album["coverUrl"],
        }
        yield item
    '''

if __name__ == '__main__':
    plugin.run()
