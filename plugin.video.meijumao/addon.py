#!/usr/bin/python
# -*- coding: utf-8 -*-

# Module: default
# Author: BirdZhang
# Created on: 6.6.2017
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
# Largely following the example at 
# https://github.com/romanvm/plugin.video.example/blob/master/main.py

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urlparse
import urllib2
import urllib
import sys
import re
from bs4 import BeautifulSoup
from common import get_html

GREENBANNER = '[COLOR green]%s[/COLOR]'
YELLOWBANNER = '[COLOR yellow] %s [/COLOR]'

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')

_meijumao = "http://www.meijumao.net"

dialog = xbmcgui.Dialog()
pDialog = xbmcgui.DialogProgress()

__index__ = [
    ("/search", GREENBANNER % u'搜索'),
    ("/categories",u"分类"),
    ("/maogetvs",u"猫哥推荐"),
    ("/alltvs",u"所有美剧"),
    ("/populartvs",u"热门美剧")
    # ("/sitemaptvs",u"美剧索引")
]


def post(url, data):
    req = urllib2.Request(url)
    #enable cookie
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()


def index():
    listing = []
    is_folder=True
    for i in __index__:
        list_item = xbmcgui.ListItem(label=i[1])
        url='{0}?action=index_router&article={1}'.format(_url,i[0])
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    xbmcplugin.endOfDirectory(_handle)


# get articles
def list_categories(article):
    html = get_html(_meijumao + article, headers={'Host': 'www.meijumao.net'})
    soup = BeautifulSoup(html, "html.parser")
    is_folder=True
    listing = []
    for urls in soup.find_all("a",attrs={"data-remote":"true"}):
        list_item = xbmcgui.ListItem(label=urls.div.get_text())
        url='{0}?action=list_sections&section={1}'.format(_url, urls.get("href").replace(_meijumao,""))
        listing.append((url, list_item, is_folder))

    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    #xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


# get sections
def list_sections(section):
    if section == "#":
        return
    html = get_html(_meijumao + section, headers={'Host': 'www.meijumao.net'})
    soup = BeautifulSoup(html, "html.parser")

    listing = []
    is_folder=True
    for section in soup.find_all("article"):
        p_title = section.img.get("alt")
        p_thumb = section.img.get("src")
        list_item = xbmcgui.ListItem(label=p_title, thumbnailImage=p_thumb)
        list_item.setProperty('fanart_image', p_thumb)
        url = '{0}?action=list_series&series={1}&seriesname={2}&fanart_image={3}'.format(_url, section.a.get("href"),p_title.encode("utf-8"),p_thumb)
        listing.append((url, list_item, is_folder))
    
    #pagination
    will_page = soup.find("ul",attrs={"id":"will_page"}).find_all("li")
    if len(will_page) > 0:
        # print will_page[0].get("class"),will_page[0].find("a").get("href")
        list_item = xbmcgui.ListItem(label="上一页")
        url='{0}?action=list_sections&section={1}'.format(_url, will_page[0].find("a").get("href"))
        listing.append((url, list_item, is_folder))
        list_item = xbmcgui.ListItem(label="下一页")
        url='{0}?action=list_sections&section={1}'.format(_url, will_page[-1].find("a").get("href"))
        listing.append((url, list_item, is_folder))
    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    xbmcplugin.endOfDirectory(_handle)
    

def list_series(series, seriesname, fanart_image):
    html = get_html(_meijumao + series, headers={'Host': 'www.meijumao.net'})
    soup_series = BeautifulSoup(html, "html.parser")

    s = soup_series.find_all('div',{'class':'col_two_third portfolio-single-content col_last nobottommargin'})
    if s is not None:
        info = s[0].text
    else:
        info = ''

    p_series = soup_series.find_all("div",attrs={"class":"col-lg-1 col-md-2 col-sm-4 col-xs-4"})
    listing = []
    is_folder=False
    for serie in p_series:
        if not serie.a:
            continue
        if not serie.a.get("href").startswith("/"):
            continue
        title = serie.a.get_text().replace(" ", "").replace("\n", "")
        list_item = xbmcgui.ListItem(label=title)
        list_item.setInfo(type='Video', infoLabels={'Title': title,
                                                    'Plot': info})
        url = '{0}?action=play_video&episode={1}'.format(_url, serie.a.get("href"))
        url += '&name=' + GREENBANNER % seriesname
        url += YELLOWBANNER % title.encode("utf-8")
        listing.append((url, list_item, is_folder))
        
    xbmcplugin.addDirectoryItems(_handle,listing,len(listing))
    xbmcplugin.endOfDirectory(_handle)


def list_playsource(episode, name):
    html = get_html(_meijumao + episode, headers={'Host': 'www.meijumao.net'})
    soup_source = BeautifulSoup(html, "html.parser")
    listing = []
    for source in soup_source.find_all("a",attrs={"class":"button button-small button-rounded"}):
        list_item = xbmcgui.ListItem(label=source.get_text())
        if source.get("href").startswith("http"):
            continue
        # url = '{0}?action=play_video&episode={1}&name={2}'.format(_url, source.get("href"),name)
        listing.append((source.get("href"),name))
    if len(listing) == 0:
        dialog.ok(__addonname__, '没有找到视频源')
        return
    else:
        play_video(listing[0])


def get_maomaoURL(episode):
    episode = episode.replace("show_episode?","play_episode?")
    html = get_html(_meijumao + episode, headers={'Host': 'www.meijumao.net'})
    if not html:
        return None
    url = re.compile('decodeURIComponent\((.+?)\)').findall(html)
    if len(url) > 0:
        play_url = url[0].strip("'")
        return play_url
    else:
        return None



def get_otherURL(source):
    if 'sohu.com' in source:
        from sohu import video_from_url
    elif 'qiyi.com' in source:
        from iqiyi import video_from_url
    elif 'pptv.com' in source:
        from pptv import video_from_url
    else:
        return None

    videourl = video_from_url(source)
    stackurl = 'stack://' + ' , '.join(videourl)
    return stackurl


def play_video(episode, name):
    """
    Play a video by the provided path.
    :param path: str
    :return: None
    """

    html = get_html(_meijumao + episode, headers={'Host': 'www.meijumao.net'})
    soup_js = BeautifulSoup(html, "html.parser")
    title = ""
    soup = soup_js.find_all("h1")
    if soup:
        title = soup[0].get_text()
    soup = soup_js.find_all("li",attrs={"class":"active"})
    if soup:
        title += " - "+soup[0].get_text()
    html = html.replace('\n', '')

    soup = soup_js.find_all('div', {'class':'col_full portfolio-single-content'})
    for s in soup:
        if '播放源' in s.h2.text.encode('utf-8'):
            source = s.find_all('a')
            urls = [x['href'] for x in source]
            break

    if (urls is None) or (len(urls) < 1):
        dialog.ok(__addonname__, '没有找到视频源')
        return

    for source in urls:
        if source[0] == '/':
            play_url = get_maomaoURL(episode)
        else:
            play_url = get_otherURL(source)
        if play_url is not None:
            break
        
    if play_url is None:
        dialog.ok(__addonname__, '视频源不能解析')
        return
    play_item = xbmcgui.ListItem(name)
    play_item.setInfo(type="Video",infoLabels={"Title":name})
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    # directly play the item.
    xbmc.Player().play(play_url, play_item)


def search():
    keyboard = xbmc.Keyboard('','请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
        p_url = "/search?q="
        url = p_url + urllib.quote_plus(keyword)
        list_sections(url)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring
    :param paramstring:
    :return:
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(urlparse.parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'index_router':
            if params['article'] == '/search':
                search()
            elif params['article'] == '/maogetvs'  or params['article'] == '/alltvs' or params['article'] == '/populartvs':
                list_sections(params['article'])
            elif params['article'] == '/categories':
                list_categories('/alltvs')
        elif params['action'] == 'list_sections':
            list_sections(params['section'])
        elif params['action'] == 'list_series':
            list_series(params['series'],params["seriesname"],params["fanart_image"])
        elif params['action'] == 'list_playsource':
            list_playsource(params['episode'],params["name"])
        elif params['action'] == 'play_video':
            play_video(params['episode'],params["name"])
            
    else:
        index()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
