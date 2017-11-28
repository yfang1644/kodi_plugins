#!/usr/bin/python
# -*- coding: utf8 -*-

from xbmcswift2 import Plugin, ListItem, xbmc
from urlparse import parse_qsl
from urllib import urlencode
from json import loads
from bs4 import BeautifulSoup
from common import get_html

HOST = 'http://www.renrenyingshi.com'
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
url_for = plugin.url_for


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


@plugin.route('/sublist/<url>')
def sublist(url):
    if not url.startswith('http'):
        url = HOST + url
    pass

# main entrance
@plugin.route('/')
def index():
    page = get_html(HOST)
    tree = BeautifulSoup(page, 'html.parser')
    soup = tree.find_all('ul', {'id': 'nav'})
    soups = soup[0].find_all('li', {'class': 'nav-item'})
    for item in soups[1:]:
        yield {
            'label': item.text,
            'path': url_for('sublist', url=item.a['href'])
        }


if __name__ == '__main__':
    plugin.run()
