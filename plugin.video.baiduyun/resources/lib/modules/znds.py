#! /usr/bin/env python
# coding=utf-8

import re
import httplib
from urlparse import urljoin
from urllib import quote_plus
from xbmcswift2 import Module, Plugin

from utils import fetch_url, create_baidu_url
import xbmcutils


title = 'ZNDS智能电视网'
m = Module(__name__)
m.storage_path = Plugin().storage_path  # a bug from xbmcswift2
HOST_NAME = 'yun.znds.com'
HOST = 'http://yun.znds.com/'


@m.route('/')
def index():
    return [
        {'label': u'[COLOR FFFFFF00]猜你喜欢[/COLOR]',
            'path': m.url_for('guess')},
        {'label': u'全部',
            'path': m.url_for('list_movies', link='list.html')},
        {'label': u'喜剧',
            'path': m.url_for('list_movies', link='list-喜剧.html')},
        {'label': u'爱情',
            'path': m.url_for('list_movies', link='list-爱情.html')},
        {'label': u'动作',
            'path': m.url_for('list_movies', link='list-动作.html')},
        {'label': u'恐怖',
            'path': m.url_for('list_movies', link='list-恐怖.html')},
        {'label': u'科幻',
            'path': m.url_for('list_movies', link='list-科幻.html')},
        {'label': u'剧情',
            'path': m.url_for('list_movies', link='list-剧情.html')},
        {'label': u'战争',
            'path': m.url_for('list_movies', link='list-战争.html')},
        {'label': u'古装',
            'path': m.url_for('list_movies', link='list-古装.html')},
        {'label': u'伦理',
            'path': m.url_for('list_movies', link='list-伦理.html')},
        {'label': u'历史',
            'path': m.url_for('list_movies', link='list-历史.html')},
        {'label': u'[COLOR FFFFFF00]高清区[/COLOR]',
            'path': m.url_for('gaoqing')},
        {'label': u'[COLOR FFFFFF00]* 搜索 *[/COLOR]',
            'path': m.url_for('search')},
    ]


@m.route('/gaoqing/')
def gaoqing():
    return [
        {'label': u'[高清]全部', 'path':
            m.url_for('list_movies', link='gaoqing.html')},
        {'label': u'[高清]喜剧', 'path':
            m.url_for('list_movies', link='gaoqing-喜剧.html')},
        {'label': u'[高清]爱情', 'path':
            m.url_for('list_movies', link='gaoqing-爱情.html')},
        {'label': u'[高清]动作', 'path':
            m.url_for('list_movies', link='gaoqing-动作.html')},
        {'label': u'[高清]恐怖', 'path':
            m.url_for('list_movies', link='gaoqing-恐怖.html')},
        {'label': u'[高清]科幻', 'path':
            m.url_for('list_movies', link='gaoqing-科幻.html')},
        {'label': u'[高清]剧情', 'path':
            m.url_for('list_movies', link='gaoqing-剧情.html')},
        {'label': u'[高清]战争', 'path':
            m.url_for('list_movies', link='gaoqing-战争.html')},
        {'label': u'[高清]古装', 'path':
            m.url_for('list_movies', link='gaoqing-古装.html')},
        {'label': u'[高清]伦理', 'path':
            m.url_for('list_movies', link='gaoqing-伦理.html')},
        {'label': u'[高清]历史', 'path':
            m.url_for('list_movies', link='gaoqing-历史.html')},
    ]


@m.route('/guess/')
def guess():
    items = generate_items_from_page(
        fetch_url(urljoin(HOST, '/baidu.php')))

    items.append({
        'label': '换一批',
        'path': m.url_for('guess'),
    })

    return m.plugin.finish(items, view_mode='thumbnail')


@m.route('/search/')
def search():
    query = (xbmcutils.keyboard(heading=u'请输入搜索内容') or '').strip()
    if query:
        m.plugin.redirect(m.url_for(
            'search_result', keyword=query))


@m.route('/list_movies/<link>/')
def list_movies(link):
    content = fetch_url(urljoin(HOST, link))
    items = generate_items_from_page(content)

    match = re.search(
        r"<a class='nextPage' href='(.+?)'>下页</a>", content)  # noqa
    if match:
        items.append({
            'label': u'下一页',
            'path': m.url_for('list_movies', link=match.group(1))
        })

    return m.plugin.finish(items, view_mode='thumbnail')


@m.route('/show_detail/<page_id>/')
def show_detail(page_id):
    url = '%sview-%s.html' % (HOST, page_id)
    content = fetch_url(url)

    items = [{
        'label': ''.join(match.groups()[1:]),
        'path': m.url_for('bdyun_link', link=url + match.group(1))
    } for match in re.finditer(r'<a class="btn btn-inverse pull-left".*?href="(.+?)".*?>(.+?)<span class="baidusp">(.+?)</span>\s*<span class="baidusp2">(.+?)</span>', content)]  # noqa

    if len(items) != 1:
        return m.plugin.finish(items)

    m.plugin.redirect(items[0]['path'])


@m.route('/bdyun_link/<link>/')
def bdyun_link(link):
    conn = httplib.HTTPConnection(HOST_NAME)
    conn.request("GET", link[len(HOST) - 1:])
    r = conn.getresponse()
    conn.close()

    xbmcutils.update_plugin_url(create_baidu_url(r.getheader('Location')))


# def get_items_from_url(url):
#     content = fetch_url(url)
#     _RE = re.compile(
#         r'<li>\s*<a href="detail\.aspx\?id=(\d+)"[\s\S]*?'
#         '<img src="(.+?)"[\s\S]*?'
#         '<h3>(.+?)</h3>[\s\S]*?'
#         '<em>(.+?)</em>')
#     items = []
#     for match in _RE.finditer(content):
#         page_id, imgurl, name, grade = match.groups()
#         items.append({
#             'label': '%s [评分：%s]' % (name, grade),
#             'path': m.url_for('show_detail', page_id=page_id),
#             'thumbnail': urljoin(HOST, imgurl)
#         })

#     return items


@m.route('/search_result/<keyword>/')
def search_result(keyword):
    return m.plugin.finish(
        generate_items_from_page(
            fetch_url(
                HOST + 'if.php',
                'q=' + quote_plus(keyword)
            )
        ),
        view_mode='thumbnail'
    )


def generate_items_from_page(content):
    return [{
        'label': '%s [评分：%s]' % (match.group(3), match.group(4)),
        'path': m.url_for('show_detail', page_id=match.group(2)),
        'thumbnail': HOST + match.group(1),
    } for match in re.finditer(
        r'<li[^>]*?>\s*<a.*?><img src="(.+?)".*?/></a>\s*<span .*?><a href="/view-(\d+)\.html".*?>(.+?)</a>(.*?)</span>',   # noqa
        content
    )]
