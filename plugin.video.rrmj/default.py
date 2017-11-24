#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import sys
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
sys.path.append(os.path.join(ADDON_PATH, 'resources', 'lib'))

from xbmcswift2 import Plugin, ListItem, xbmc
from rrmj import *
from urlparse import parse_qsl
from urllib import urlencode
from json import loads

CATE = [
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
Meiju = RenRenMeiJu()
PAGE_ROWS = int(plugin.get_setting("page_rows"))
SEASON_CACHE = plugin.get_storage('season')
HISTORY = plugin.get_storage('history')


def colorize(label, color):
    return "[COLOR %s]%s[/COLOR]" % (color, label)


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
    return plugin.url_for(endpoint, **params)


# list catagories
@plugin.route('/cat/')
def category():
    items = [{
        'label': ca,
        'path': plugin.url_for("cat_list", cat=ca),
    } for ca in CATE]
    return items


# search entrance
@plugin.route('/hotword/')
def hotword():
    yield {
            'label': colorize("输入关键字搜索", "yellow"),
            'path': plugin.url_for("input_keyword"),
        }
    hotwords = Meiju.hot_word()
    for word in hotwords["data"]["wordList"]:
        word = word.encode("utf8")
        item = {
            'label': colorize(word, "green"),
            'path': plugin.url_for("search_title", title=word),
        }
        yield item


# get search result by input keyword
@plugin.route("/input/")
def input_keyword():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        url = plugin.url_for("search_title", title=keyword)
        plugin.redirect(url)


options={'page': '1'}

@plugin.route('/search/cat_<cat>/page_<page>', name="cat_list", options=options)  # get search result by catagory
@plugin.route('/search/title_<title>/page_<page>', name="search_title", options=options)  # get search result by search title
@plugin.route('/search/s_<sort>/o_<order>/m_<mark>/page_<page>', name="mark_list", options=options)  # get search result by catagory and page
@plugin.route('/search/page_<page>', options=options)  # get search result by nothing??

def search(page, **kwargs):
    plugin.set_content('videos')
    searchlist = Meiju.search(page, PAGE_ROWS, **kwargs)
    total = searchlist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS
    items = previous_page('cat_list', page, total_page, **kwargs)
    for item in searchlist['data']['results']:
        status = u'(完结)' if item['finish'] else u'(更新到{})'.format(item['upInfo'])
        items.append({
            'label': item['title'] + status,
            'path': plugin.url_for("detail", seasonId=item['id']),
            'thumbnail': item.get('url', ''),
            'info': {
                'title': item['title'],
                'plot': item.get('shortBrief', ''),
                'rating': float(item['score']),
                'genre': ''
            }
        })
        #item._listitem.setArt({"poster": one["cover"]})

    items += next_page('cat_list', page, total_page, **kwargs)
    return items


@plugin.route('/album/<albumId>/', name="album")
def get_album(albumId):
    c_list = Meiju.get_album(albumId)
    for one in c_list["data"]["results"]:
        yield {
            'label': one.get("title"),
            'path': plugin.url_for("detail", seasonId=one.get("id")),
            'icon': one["cover"],
            'thumbnail': one["cover"],
            'info': {"title": one.get('title'),
                     "plot": one.get("brief", ""),
                     "rating ": float(one["score"]),
                     "genre": one["cat"],
                     "season": one["seasonNo"]}
        }
    plugin.set_content('TVShows')


# get season episodes by season id
@plugin.route('/detail/<seasonId>', name="detail")
def video_detail(seasonId):
    plugin.set_content('video')
    detail = Meiju.video_detail(seasonId)
    season_data = detail['data']['season']
    title = season_data['title']
    SEASON_CACHE[seasonId] = detail['data']  # store season detail
    history = HISTORY.get('list', None)
    playing_episode = "0"
    if history is not None:
        for l in history:
            if l['seasonId'] == seasonId:
                playing_episode = l['index']

    items = []
    for episode in season_data[s'playUrlList']:
        label = title + str(episode['episode'])
        if episode["episode"] == playing_episode:
            label = "[B]" + colorize(label, "green") + "[/B]"

        yield {
            'label': label,
            'path': plugin.url_for('play_season',
                                   seasonId=seasonId,
                                   index=episode['episode'],
                                   Esid=episode['episodeSid']),
            'thumbnail': season_data['cover'],
            'is_playable': True,
            'info': {'plot': season_data['brief'],
                     'title': title,
                     'episode': int(episode['episode']),
                     'season': 0},
        }
        #items.append({
        #    'label': label,
        #    'path': plugin.url_for('play_season',
        #                           seasonId=seasonId,
        #                           index=episode['episode'],
        #                           Esid=episode['episodeSid']),
        #    'thumbnail': season_data['cover'],
        #    'is_playable': True,
        #    'info': {'plot': season_data['brief'],
        #             'title': title,
        #             'episode': int(episode['episode']),
        #             'season': 0},
        #})

    #plugin.finish(items, sort_methods=['episode'])
    #return items


@plugin.route('/play/<seasonId>/<index>/<Esid>', name='play_season')
def play(seasonId="", index="", Esid=""):
    season_data = SEASON_CACHE.get(seasonId).get('season')
    title = season_data["title"]
    episode_sid = Esid
    rs = RRMJResolver()
    play_url, _ = rs.get_play(episode_sid, plugin.get_setting("quality"))
    if play_url is not None:
        stackurl = play_url.split('|')
        play_url = 'stack://' + ' , '.join(stackurl)
        add_history(seasonId, index, Esid, title)
        li = ListItem(title+index,
                    path=play_url,
                    thumbnail=season_data.get('cover'))
        li.set_info('video', {'title': title+index,
                              "plot": season_data.get('brief','')})

        plugin.set_resolved_url(li)
    else:
        plugin.set_resolved_url(False)


def add_history(seasonId, index, Esid, title):
    if "list" not in HISTORY:
        HISTORY["list"] = []
    for l in HISTORY["list"]:
        if l["seasonId"] == seasonId:
            HISTORY["list"].remove(l)
    item = {"seasonId": seasonId,
            "index": index,
            "sid": Esid,
            "season_name": title}
    HISTORY["list"].insert(0, item)


@plugin.route('/history')
def history():
    for l in HISTORY.get('list', {}):
        seasonId = l['seasonId']
        index = l['index']
        sid = l['sid']
        yield {
            'label': u"[COLOR green]{title}[/COLOR]  观看到第[COLOR yellow]{index}[/COLOR]集".format(title=l["season_name"], index=l["index"]),
            'path': plugin.url_for("detail", seasonId=seasonId),
        }


@plugin.route('/recommend/<page>')
def recommend(page):
    searchlist = Meiju.recommended(page, PAGE_ROWS)
    total = searchlist['data']['total']
    total_page = (total + PAGE_ROWS - 1) // PAGE_ROWS

    items = previous_page('recommend', page, total_page)
    for item in searchlist['data']['results']:
        status = u'(完结)' if item['finish'] else u'(更新到{})'.format(item['upInfo'])
        items.append({
            'label': item['title'] + status,
            'path': plugin.url_for("detail", seasonId=item['id']),
            'thumbnail': item.get('url', ''),
            'info': {
                'title': item['title'],
                'plot': item.get('shortBrief', ''),
                'rating': float(item['score']),
                'genre': ''
            }
        })
        #item._listitem.setArt({"poster": one["cover"]})

    items += next_page('recommend', page, total_page)
    return items
    


# main entrance
@plugin.route('/')
def index():
    yield {
        'label': u'分类',
        'path': plugin.url_for('category'),
    }
    yield {
        'label': u'搜索',
        'path': plugin.url_for('hotword'),
    }
    yield {
        'label': u'小编推荐'
        'path': plugin.url_for('recommend'),
    }
    yield {
        'label': '历史',
        'path': plugin.url_for('history'),
    }
    mainpage = Meiju.index_info()['data']

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
