#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
from bs4 import BeautifulSoup
import simplejson
from common import get_html
from qq import video_from_url, video_from_vid

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')

BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

HOST_URL = 'https://v.qq.com'
CHANNEL_LIST = {'电视剧': '/x/list/tv',
                '综艺': '/x/list/variety',
                '电影': '/x/list/movie',
                '动漫': '/x/list/cartoon',
                '少儿': '/x/list/children',
                '娱乐': '/x/list/ent',
                '音乐': '/x/list/music',
                '纪录片': '/x/list/doco',
                '微电影': '/dv',
                '新闻': '/x/list/news',
                '体育': '/x/list/sports',
                '搞笑': '/x/list/fun',
                '原创': '/videoplus',
                'TED': '/vplus/ted/folders',
                '时尚': '/fashion',
                '生活': '/life',
                '科技': '/tech',
                '汽车': '/auto',
                '财经': '/finance'}


def httphead(url):
    if url[0:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


def GetHttpData(url):
    ''' some pages jump'''
    tree = BeautifulSoup(httpdata, 'html.parser')
    try:
        jump = tree.title.text
    except:
        return httpdata
    if u'正在跳转' in jump:
        url = tree.link['href']
        httpdata = GetHttpData(url)

    return httpdata


def mainMenu():
    li = xbmcgui.ListItem('[COLOR FF808F00] 【腾讯视频 - 搜索】[/COLOR]')
    u = sys.argv[0] + '?mode=search'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    for name in CHANNEL_LIST:
        li = xbmcgui.ListItem(name)
        if name in ('TED'):
            mode = 'tedlist'
        elif name in ('微电影', '时尚', '原创',
                      '生活', '财经', '汽车', '科技'):
            mode = 'otherlist'
        else:
            mode = 'mainlist'
        u = sys.argv[0] + '?mode=%s&name=%s' % (mode, name)
        u += '&url=' + httphead(CHANNEL_LIST[name])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def changeList(params):
    url = params.get('url')
    del(params['url'])
    name = params.get('name')
    del(params['name'])
    strparam = urllib.urlencode(params)
    html = get_html(url + '?' + strparam)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    dialog = xbmcgui.Dialog()

    setparam = ''
    for iclass in soup:
        si = iclass.find_all('a')
        list = []
        item = []
        for subitem in si:
            list.append(subitem.text)
            item.append(subitem['href'])
        sel = dialog.select(iclass.span.text, list)

        if sel >= 0:
            setparam += item[sel]

    setparam = setparam.replace('?', '&')
    setparam = 'url=%s' % url + setparam
    params = dict(urllib2.urlparse.parse_qsl(setparam))
    params['name'] = name
    listSubMenu(params)


def listSubMenu(params):
    url = params.get('url')
    del(params['url'])
    name = params.get('name')
    strparam = urllib.urlencode(params)
    html = get_html(url + '?' + strparam)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'filter_line'})

    if 'offset' in params:
        page = int(params['offset']) // 30 + 1
    else:
        page = 1
    li = xbmcgui.ListItem(BANNER_FMT % (name+'(第%d页 分类过滤)' % page))
    u = sys.argv[0] + '?url=' + url + '&mode=select&' + strparam
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    soup = tree.find_all('li', {'class': 'list_item'})
    for mainpage in soup:
        img = httphead(mainpage.img['r-lazyload'])
        title = mainpage.strong.a.text
        info = mainpage.find('span', {'class': 'figure_info'})
        if info:
            info = '(' + info.text + ')'
        else:
            info = ''
        href = mainpage.strong.a['href']
        mark = mainpage.find('i', {'class': 'mark_v'})
        if mark:
            info += '[COLOR FFD00080](' + mark.img['alt'] + ')[/COLOR]'

        li = xbmcgui.ListItem(title + info, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title})
        u = sys.argv[0] + '?url=' + href + '&' + strparam
        u += '&mode=episodelist&thumb=' + img + '&title=' + title
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    # PAGE LISTING
    soup = tree.find_all('div', {'class': 'mod_pages'})
    pages = soup[0].find_all('a')
    for site in pages:
        title = site.text
        try:
            number = int(title)
        except:
            number = -99
        if number == page:
            continue
        href = site['href']
        if href[0] == '?':
            href = href[1:]         #  href looks like '?&offset=30'

        li = xbmcgui.ListItem(title)
        u = sys.argv[0] + '?url=' + url + '&' + strparam + href
        u += '&mode=mainlist&name=' + urllib.quote_plus(name)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def seriesList(params):
    url = params['url']
    html = get_html(url)
    html = re.sub('\t|\n|\r| ', '', html)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('span', {'class': 'item'})

    info = tree.find('meta', {'name': 'description'})['content']
    img = tree.find('meta', {'itemprop': 'image'})['content']

    playlist = xbmc.PlayList(0)
    playlist.clear()
    j = 0
    for item in soup:
        try:
            p_title = item.a['title']
        except:
            continue
        try:
            href = httphead(item.a['href'])
        except:
            continue
        tn = item.a.text
        title = p_title + '--' + tn
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video',
                   infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?url=' + href + '&mode=playvideo'
        u += '&title=%d.%s' % (j, p_title)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
        playlist.add(href, li)
        j += 1

    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def episodesList(params):
    url = params['url']
    thumb = params['thumb']
    title = params['title']

    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    info = tree.find('meta', {'name': 'description'})['content']

    match = re.compile('var LIST_INFO\s*=\s*({.+?}});{0,}\n').search(html)
    js = simplejson.loads(match.group(1))
    li = xbmcgui.ListItem(BANNER_FMT % title,
                          iconImage=thumb, thumbnailImage=thumb)
    li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    playlist = xbmc.PlayList(0)
    playlist.clear()
    j = 0
    for item in js['vid']:
        try:
            title = js['data'][item]['title']
        except:
            continue
        vid = js['data'][item]['vid']
        try:
            img = js['data'][item]['preview']
        except:
            img = thumb
        img = httphead(img)
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=playvideo&vid=' + vid
        u += '&title=%d.%s' % (j, title) + '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        playlist.add(vid, li)
        j += 1

    li = xbmcgui.ListItem(BANNER_FMT % '相关视频')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('li', {'class': 'list_item'})
    for item in soup:
        vid = item.get('data-vid')
        if not vid:
            vid = item.get('id', '')
        img = item.img.get('r-lazyload')
        if not img:
            img = item.img.get('src')
        if not img:
            img = ''
        img = httphead(img)
        href = httphead(item.a['href'])
        href = href.replace('?', '&')
        titlemsg = item.find('a', {'_stat': 'tabs-columns:title'})
        if titlemsg:
            title = titlemsg.text
        else:
            try:
                title = item.img['alt']
            except:
                title = item.a['title']
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?mode=episodelist'
        u += '&title=' + urllib.quote_plus(title.encode('utf-8'))
        u += '&url=' + urllib.quote_plus(href)
        u += '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def tedAlbum(params):
    url = params['url']
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'mod_video_list_content ui_scroll_content'})
    soup = soup[0].find_all('li', {'class': 'item'})

    playlist = xbmc.PlayList(0)
    playlist.clear()
    j = 0

    for item in soup:
        vid = item.a['id']
        info = item.a['desc']
        href = httphead(item.a['href'])
        title = item.a['title']
        li = xbmcgui.ListItem(title)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        u = sys.argv[0] + '?mode=playvideo&vid=' + vid
        u += '&title=%d.%s' % (j, title) + '&url=' + href
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
        playlist.add(vid, li)
        j += 1

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def tedFolders(params):
    url = params['url']
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'site_container'})
    maintitle = soup[0].find('span', {'class': 'count_num'}).text

    li = xbmcgui.ListItem(BANNER_FMT % maintitle.encode('utf-8'))
    u = sys.argv[0] + '?url=' + url + '&mode=tedlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = soup[0].find_all('li', {'class': 'list_item'})

    for item in soup:
        href = httphead(item.a['href'])
        img = httphead(item.img['src'])
        text = item.find('strong', {'class': 'album_title'})
        if text is None:
            title = item.a['title']
        else:
            title = text.text
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        if '.html' in href:
            mode = 'tedalbum'
        else:
            mode = 'tedlist'
        u = sys.argv[0] + '?url=' + href + '&mode=' + mode
        u += '&title=' + title + '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def fashion(params):
    url = params['url']
    name = params['name']
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.find_all('div', {'class': 'nav_area'})
    list1 = soup[0].find_all('a')
    soup = tree.find_all('div', {'class': 'slider_nav'})
    list2 = soup[0].find_all('a')

    li = xbmcgui.ListItem(BANNER_FMT % name)
    u = sys.argv[0] + '?url=' + url + '&mode=otherlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    for item in list1 + list2:
        title = item.text
        href = httphead(item['href'])
        try:
            img = httphead(item['data-bgimage'])
        except:
            img = 'xxx'
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&title=' + title + '&thumb=' + img
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'video')

    li = xbmcgui.ListItem(BANNER_FMT % '其他视频')
    u = sys.argv[0] + '?url=' + url + '&mode=otherlist'
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    soup = tree.find_all('ul', {'class': 'figures_list'})
    for group in soup:
        items = group.find_all('li', {'class': 'list_item'})
        for item in items:
            title = item.a['title']
            href = item.a['href']
            try:
                img = item.img['src']
            except:
                img = item.img['lz_src']
            li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
            u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
            u += '&title=' + title + '&thumb=' + img
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playVideo(params):
    sel = int(__addon__.getSetting('resolution'))
    if sel == 4:
        list = ['流畅(270P)', '高清(360P)', '超清(720P)', '蓝光(1080P)']
        sel = xbmcgui.Dialog().select('清晰度选择', list)
        if (sel < 0):
            return False, False

    playmode = __addon__.getSetting('video_vplaycont')

    title = params['title'].split('.')

    playlistA = xbmc.PlayList(0)
    playlist = xbmc.PlayList(1)
    playlist.clear()

    title = title.split('.')
    v_pos = int(title[0])
    title = title[1]
    psize = playlistA.size()

    for x in range(v_pos, psize):
        p_item = playlistA.__getitem__(x)
        p_url = p_item.getfilename(x)
        p_list = p_item.getdescription(x)
        li = p_item      # pass all li items including the embedded thumb image
        li.setInfo(type='Video', infoLabels={'Title': p_list})

        if ('http://' in p_url) or ('https://' in p_url):
            urls = video_from_url(p_url, level=sel)
        else:
            urls = video_from_vid(p_url, level=sel)

        if urls is False:
            xbcgui.Dialog().ok(__addonname__, '无法获取视频地址')
            return

        ulen = len(urls)
        for i in range(0, ulen):
            name = title + '(%d/%d)' % (i + 1, ulen)
            liz = xbmcgui.ListItem(name, thumbnailImage='')
            liz.setInfo(type="Video", infoLabels={"Title": name})
            playlist.add(urls[i], liz)

        if x == v_pos:
            xbmc.Player(1).play(playlist)
        if playmode == 'false':
            break


def searchTencent(params):
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    url = HOST_URL + '/x/search/?q=' + urllib.quote_plus(keyword)
    url += '&stag=0'

    link = get_html(url)
    if link is None:
        li = xbmcgui.ListItem(' 抱歉，没有找到[COLOR FFFF0000] ' + keyword + '   [/COLOR]的相关视频')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        return

    li = xbmcgui.ListItem('[COLOR FFFF0000]当前搜索:(' + keyword + ')[/COLOR]')
    u = sys.argv[0]
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)

    # fetch and build the video series episode list
    content = BeautifulSoup(link, 'html.parser')
    soup = content.find_all('div', {'class': 'result_item'})

    playlist = xbmc.PlayList(0)
    playlist.clear()
    j = 0

    for items in soup:
        href = httphead(items.a['href'])
        img = httphead(items.img['src'])
        title = items.img['alt']

        info = items.find('span', {'class': 'desc_text'})
        try:
            info = info.text
        except:
            info = ''

        u = sys.argv[0] + '?url=' + href + '&mode=episodelist'
        u += '&title=' + title + '&thumb=' + img
        li = xbmcgui.ListItem(title, iconImage=img, thumbnailImage=img)
        li.setInfo(type='Video', infoLabels={'Title': title, 'Plot': info})
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)

        list = items.find_all('div', {'class': 'item'})
        for series in list:
            subtitle = series.a.text
            href = httphead(series.a['href'])
            li = xbmcgui.ListItem(subtitle)
            li.setInfo(type='Video', infoLabels={'Title': subtitle})
            u = sys.argv[0] + '?url=' + href + '&mode=playvideo'
            u += '&title=%d.%s' % (j, subtitle)
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
            playlist.add(href, li)
            j += 1

    xbmcplugin.setContent(int(sys.argv[1]), 'videos')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

if mode is not None:
    del(params['mode'])

runlist = {
    None: 'mainMenu()',
    'mainlist': 'listSubMenu(params)',
    'episodelist': 'episodesList(params)',
    'otherlist': 'fashion(params)',
    'tedlist': 'tedFolders(params)',
    'tedalbum': 'tedAlbum(params)',
    'search': 'searchTencent(params)',
    'select': 'changeList(params)',
    'playvideo': 'playVideo(params)'
}

exec(runlist[mode])
