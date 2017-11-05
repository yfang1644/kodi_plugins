#!/usr/bin/python
# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, xbmc
from json import loads
from bigmovie import BigMovie

plugin = Plugin()
Bigmovie = BigMovie()
HISTORY = plugin.get_storage('history')

def colorize(label, color):
    return "[COLOR %s]" % color + label + "[/COLOR]"

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


def getSettingByRPC(key):
    """Get Kodi Setting by JSON-RPC

    Args:
        key (TYPE): Description

    Returns:
        TYPE: Description
    """
    result = xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.GetSettingValue","params":{"setting":"%s"},"id":1}' % key)
    result = loads(result)
    return result["result"]["value"]

def set_auto_play():
    auto_play_setting = plugin.get_setting("auto_next")
    print setSettingByRPC("videoplayer.autoplaynextitem", auto_play_setting)

# main entrance
@plugin.route('/')
def index():
    set_auto_play()
    data = Bigmovie.index()
    yield {
        'label': "电影" + colorize("最新", "green"),
        'path': plugin.url_for("movie_list", method="new"),
    }
    yield {
        'label': "电影" + colorize("最热", "green"),
        'path': plugin.url_for("movie_list", method="hot"),
    }
    yield {
        'label': "电影" + colorize("全部", "green"),
        'path': plugin.url_for("movie_list", method="all"),
    }
    for movie in data["movies"]:
        yield {
            'label': movie.get("title"),
            'path': plugin.url_for("more_movies", movie_id=movie.get("id", "")),
            'thumbnail': movie.get("img"),
        }

    yield {
        'label': "电视剧" + colorize("最新", "green"),
        'path': plugin.url_for("tv_list", method="new"),
    }
    yield {
        'label': "电视剧" + colorize("最热", "green"),
        'path': plugin.url_for("tv_list", method="hot"),
    }
    yield {
        'label': "电视剧" + colorize("全部", "green"),
        'path': plugin.url_for("tv_list", method="all"),
    }
    for tvshow in data["tvplays"]:
        yield  {
            'label': tvshow["title"],
            'path': plugin.url_for("episode_list", tv_id=tvshow.get("id", "")),
            'icon': tvshow["img"],
            'thumbnail': tvshow["img"],
        }

    yield {
        'label': colorize("输入关键字搜索", "yellow"),
        'path': plugin.url_for("input_keyword"),
    }


# search entrance
@plugin.route('/hotword/')
def hotword():
    yield {
        'label': colorize("输入关键字搜索", "yellow"),
        'path': plugin.url_for("input_keyword"),
    }
    hotwords = Bigmovie.hot_word()
    for word in hotwords["data"]["wordList"]:
        word = word.encode("utf8")
        item = {
            'label': colorize(word, "green"),
            'path': plugin.url_for("search", title=word),
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
        url = plugin.url_for("search", keyword=keyword)
        plugin.redirect(url)


@plugin.route('/search/<keyword>/')
def search(keyword):
    c_list = Bigmovie.search(keyword)
    for movie in c_list["movies"]:
        yield {
            'label': movie.get("title"),
            'path': plugin.url_for("more_movies", movie_id=movie.get("id", "")),
            'thumbnail': movie.get("img"),
        }

    for tvshow in c_list["tvplays"]:
        yield {
            'label': tvshow["title"],
            'path': plugin.url_for("episode_list", tv_id=tvshow.get("id", "")),
            'icon': tvshow["img"],
            'thumbnail': tvshow["img"],
        }

@plugin.route('/movie_list/<method>/')
def movie_list(method):
    if method not in ["hot", "new", "all"]:
        return
    if method in ["hot", "new"]:
        r_method = "new_hot"
    else:
        r_method = "all"
    detail = Bigmovie.movie_list(r_method)
    for movie in detail[method + "list"]:
        item = {
            'label': movie.get("title"),
            'path': plugin.url_for("more_movies", movie_id=movie.get("id", "")),
            'thumbnail': movie.get("img"),
        }
        yield item

@plugin.route('/more_movies/<movie_id>')
def more_movies(movie_id):
    detail = Bigmovie.movie_detail(movie_id)
    yield {
        'label': detail['title'] + colorize(u'(播放)', 'yellow'),
        'path': detail['list'][0]['url'],
        'thumbnail': detail['img'],
        'is_playable': True,
        'info': {
            'title': detail['title'],
            'plot': detail['info'],
            'duration': int(detail.get('duration',0))*60
        }
    }

    for others in detail['reclist']:
        yield {
            'label': others['title'],
            'thumbnail': others['img'],
            'path': plugin.url_for('more_movies', movie_id=others['id'])
        }

@plugin.route('/tv_list/<method>/')
def tv_list(method):
    if method not in ["hot", "new", "all"]:
        return
    if method in ["hot", "new"]:
        r_method = "new_hot"
    else:
        r_method = "all"
    detail = Bigmovie.tv_list(r_method)
    for tvshow in detail[method + "list"]:
        yield {
            'label': tvshow["title"],
            'path': plugin.url_for("episode_list", tv_id=tvshow.get("id", "")),
            'icon': tvshow["img"],
            'thumbnail': tvshow["img"],
        }

@plugin.route('/detail/<movie_id>', name='detail')
def movie_detail(movie_id):
    detail = Bigmovie.movie_detail(movie_id)
    plugin.set_resolved_url(detail["list"][0]["url"])


@plugin.route('/play/<url>')
def play(url):
    plugin.set_resolved_url(url)


@plugin.route('/episode_list/<tv_id>/')
def episode_list(tv_id):
    detail = Bigmovie.tv_detail(tv_id)
    for index, episode in enumerate(detail["list"]):
        yield {
            'label': episode['title'] + str(index + 1) + colorize(u'(播放)', 'yellow'),
            'thumbnail': detail['img'],
            'path': plugin.url_for('play', url=episode['url'].encode('utf-8')),
            'is_playable': True,
            'info': {'plot': detail['info']}
        }

    for others in detail['reclist']:
        yield {
            'label': others['title'],
            'thumbnail': others['img'],
            'path': plugin.url_for('episode_list', tv_id=others['id'])
        }


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


@plugin.route('/history/list/')
def list_history():
    if "list" in HISTORY:
        for l in HISTORY["list"]:
            seasonId = l["seasonId"]
            index = l["index"]
            sid = l["sid"]
            yield {
                'label': u"[COLOR green]{title}[/COLOR]  观看到第[COLOR yellow]{index}[/COLOR]集".format(title=l["season_name"], index=l["index"]),
                'path': plugin.url_for("detail", seasonId=seasonId),
                'is_playable': False
            }


if __name__ == '__main__':
    plugin.run()
