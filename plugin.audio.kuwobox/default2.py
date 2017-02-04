# -*- coding: utf-8 -*-

#v1.0.0 2009/11/08 by robinttt, initial release
#v1.1.0 2011/12/04 by d744000, full web scraping, added search.

import urllib, urllib2, os, re, sys
import gzip, StringIO #playvideo
import hashlib, time
from bs4 import BeautifulSoup
import xbmc, xbmcplugin, xbmcgui, xbmcaddon


UserAgent = 'Mozilla/5.0 (Windows NT 5.1; rv:8.0) Gecko/20100101 Firefox/8.0'
URL_BASE = 'http://yinyue.kuwo.cn'
MAX_TEST = 300
INDENT_STR = '    '
BANNER_FMT = '[COLOR FFDEB887]【%s】[/COLOR]'


#
# Web process engine
#
def getUrlTree(url, data=None):
    headers = {
        'User-Agent': UserAgent,
    }
    if data and not isinstance(data, str):
        # 2-item tuple or param dict, assume utf-8
        data = urllib.urlencode(data)
    req = urllib2.Request(url, data, headers)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        # BeautifulSoup handles encoding, thus skip transcoding here.

    tree = BeautifulSoup(httpdata, "html.parser")
    return tree


def make_param(query, url=None):
    if url is None:
        url = sys.argv[0]
    param = "%s?%s" % (url, urllib.urlencode(query))
    return param


def addDir(name, url, mode, iconimage='DefaultFolder.png', context={}, folder=True, total=0):
    if url == '#@':
        url = params['url']
    elif url.startswith('/'):
        url = URL_BASE + url

    param = {"url": url, "mode": mode}
    param.update(context)
    u = make_param(param)

    item = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=item, isFolder=folder, totalItems=total)


def endDir(cache=True):
    xbmcplugin.endOfDirectory(pluginhandle, cacheToDisc=True)


context_params = {}

def driller(tree, lCont):
    #global item
    global context_params
    if not isinstance(lCont, list):
        lCont = [lCont]

    for cont in lCont:
        result = None
        context_params = cont.get('context', {})
        items = tree.find_all(*cont['tag'])
        #print("to find:", cont)
        for item in items:
            #print('found')
            if cont.get('vect', None):
                try:
                    result = cont['vect'](item)
                except:
                    pass
            if result != 'DRILLER_NO_DEEPER':
                if cont.get('child', None):
                    driller(item, cont['child'])


def processWebPage(tagHandler):
    global tree
    url = params['url']
    post = params.get('urlpost', None)
    tree = getUrlTree(url, post)
    driller(tree, tagHandler)
    endDir()


def get_params(params):
    param = {}
    if len(params) >= 2:
        cleanedparams = params.rsplit('?', 1)
        if len(cleanedparams) == 2:
            cleanedparams = cleanedparams[1]
        else:
            cleanedparams = params.replace('?', '')
        param = dict(urllib2.urlparse.parse_qsl(cleanedparams))
    return param


#
# Keyboard for search
#
def processSearch(url):
    key = get_params(url).get('key', None)
    params['url'] = url
    params['indent'] = str(True)
    params['search_key'] = key
    processWebPage(searchList)


def searchDefaultKeyboard(key=None, mode='all'):
    if key:
        url = make_param({"key": key, 'type': mode}, 'http://sou.kuwo.cn/ws/NSearch')
        processSearch(url)
    else:
        keyb = xbmc.Keyboard('', '搜索(可用拼音)')
        keyb.doModal()
        if keyb.isConfirmed():
            key = keyb.getText()


def searchChineseKeyboard(key=None, mode='all', pn=0):
    if key:
        url = make_param({"key": key, 'type': mode}, 'http://sou.kuwo.cn/ws/NSearch')
        processSearch(url)
    else:
        # Somehow, current chinese keyboard implementation works differently than the
        # default keyboard. The doModal doesn't prevent xbmcplugin from popping up the
        # directory-scanning window, which covers up the keyboard window.
        # A workaround is to terminate the directory, doModal, pass in keyboard input
        # as new param of the container, then relaunch the container.
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        # 中文输入法
        keyboard = ChineseKeyboard.Keyboard('', '搜索')
        keyboard.doModal()
        if keyboard.isConfirmed():
            keyword = keyboard.getText()
            if keyword:
                u = make_param({'url': '', 'mode': 'search("%s")' % keyword})
                xbmc.executebuiltin('Container.Update(%s,replace)' % u)


#
# Media player
#
def get_content_by_tag(tree, tag):
    f = tree.find(tag)
    if f and f.contents:
        return f.contents[0].encode('utf-8')
    else:
        return ''


def PlayMusic():
    mids = params['url']

    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    mids = mids.split('/')
    for mid in mids:
        if mid == '':
            continue
        tree = getUrlTree('http://player.kuwo.cn/webmusic/st/getNewMuiseByRid?rid=MUSIC_'+mid)
        title = get_content_by_tag(tree, 'name')
        # kuwo has names like "song name(抢听版)", causing lyrics look up failure
        true_title = title.split('(')[0].rstrip()
        artist = get_content_by_tag(tree, 'artist')
        iconimage = get_content_by_tag(tree, 'artist_pic240')

        # prefer AAC or WMA, somehow it starts or loads faster than the mp3 link,
        # change AAC to the first download.  edit by runner6502@gamil.com
        path = get_content_by_tag(tree, 'aacpath')
        dl = get_content_by_tag(tree, 'aacdl')
        if not (path and dl):
            path = get_content_by_tag(tree, 'path')
            dl = get_content_by_tag(tree, 'wmadl')
            if not (path and dl):
                path = get_content_by_tag(tree, 'mp3path')
                dl = get_content_by_tag(tree, 'mp3dl')

        if path and dl:
            timestamp = ("%x" % int(time.time()))[:8]
            hashstr = hashlib.md5("kuwo_web@1906/resource/%s%s" % (path, timestamp)).hexdigest()
            url = 'http://%s/%s/%s/resource/%s' % (dl, hashstr, timestamp, path)

            listitem = xbmcgui.ListItem(title, iconImage=iconimage, thumbnailImage=iconimage)
            listitem.setInfo(type="Music", infoLabels={"Title": true_title, "Artist": artist})
            playlist.add(url, listitem)

        xbmc.Player().play(playlist)

#
# Utilities
#
def addBanner(name):
    ''' Add a banner, a button without action, but to separate groups of other buttons. '''
    # Burlywood color
    if name:
        name = BANNER_FMT % name
        addDir(name, '', 'pass', '', folder=False)


def addH1Banner(item):
    addBanner(item.h1.text.encode('utf-8'))


def addNav(item, mode):
    item_url = extractHref(item)
    if item_url == '#@':
        return
    name = extractName(item)
    addDir(name, item_url, mode, '')

#
# Kuwo tag handlers
#

def extractName(item):
    if not item:
        return ''
    name = ''
    span_name = item.find('span')
    if span_name:
        name = span_name.contents[0]
    elif item.has_attr('title'):
        name = item['title']
    elif item.contents:
        content = item.contents[0]
        if 'String' in str(type(content)):
            #BeautifulSoup NavigableString
            name = content
        else:
            try:
                name = content['title']
            except:
                pass
    return name.encode('utf-8')


def extractHref(item):
    if item and item.has_attr('href'):
        return item['href'].encode('utf-8')
    return ''


def extractImg(item):
    if item:
        for k in ['lazy_src', 'sr', 'src', 'init_src']:
            if item.has_attr(k):
                return item[k].encode('utf-8')
    return ''


def extractImgSearch(item, name=''):
    iconimage = extractImg(item.find('img'))
    if (not iconimage) and name:
        attrs = {'title': unicode(name, 'utf-8')}
        iconimage = extractImg(item.findChild('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findPreviousSibling('img', attrs))
        if not iconimage:
            iconimage = extractImg(item.findParent().findPreviousSibling('img', attrs))
    return iconimage


#
# XBMC plugin
#
def addLink(title, artist, url, mode, iconimage='', total=0, video=False):
    u = make_param({'url': url, 'mode': mode})
    displayname = artist + ' - ' + title if artist else title
    displayname = INDENT_STR + displayname
    itemType = 'Video' if video else 'Music'

    item = xbmcgui.ListItem(displayname, iconImage=iconimage, thumbnailImage=iconimage)
    item.setInfo(type=itemType, infoLabels={'Title': title, 'Artist': artist})
    xbmcplugin.addDirectoryItem(pluginhandle, url=u, listitem=item, isFolder=False, totalItems=total)


def addBillboardPhase(item):
    nxt_idx = None
    cur_idx = params.get('billboard_idx', item.find('li')['idx'].encode('utf-8'))
    cur_item = item.find('li', {'idx': cur_idx})
    if cur_item:
        tabDef = cur_item.find('p')
        if tabDef and tabDef.contents:
            params['playall_title'] = ('播放' + tabDef.contents[0].encode('utf-8') + '歌曲')
        nxt_item = cur_item.findNextSibling('li')
        if nxt_item:
            nxt_idx = nxt_item['idx'].encode('utf-8')

    # previous billboard phase
    if nxt_idx:
        rgtArrow = item.find(attrs={'id': 'goRight', 'class': 'jtRig'})
        if rgtArrow and rgtArrow.has_attr('onclick'):
            catId = re.search("getData\((\d+),1\)", rgtArrow['onclick'])
            if catId:
                catId = catId.groups()[0].encode('utf-8')
                url = 'http://yinyue.kuwo.cn/yy/dd/BillBoardIndex'
                post = 'cat='+catId+'&phase='+nxt_idx
                context = {'urlpost': post, 'billboard_idx': nxt_idx, 'billboard_phases': str(item)}
                addDir('查看前一期', url, 'processWebPage([songList])', '', context=context)


# 排行榜
def addBoardMusic(item):
    mid = item.find(attrs={'type':'checkbox'})
    if not (mid and mid.has_attr('mid')):
        return
    mid = mid['mid']
    title = item.find(attrs={'class':'songName'}).a['title'].encode('utf-8')
    # artist page has album name in 'class songer', not artist name
    artist = params.get('artist', '')
    if not artist:
        chld = item.find(attrs={'class':'songer'})
        if chld and chld.findChild('a'):
            chld = chld.findChild('a')
            if chld.has_attr('title'):
                artist = chld['title'].encode('utf-8')
    addLink(title, artist, mid, 'PlayMusic()', '')


def addBoardMusicList(item):
    if 'billboard_phases' in params:
        print(params['billboard_phases'])
        phase_item = BeautifulSoup(params['billboard_phases'], "html.parser")
        addBillboardPhase(phase_item)
    mids = item.find_all(attrs={'type':'checkbox'})
    mids = [x['mid'] for x in mids if x.has_attr('mid')]
    if mids:
        mids = '/'.join(mids)
        disp_title = params.get('playall_title', '播放全部歌曲')
        iconimg = params.get('playall_icon', '')
        addDir(disp_title, mids, 'PlayMusic()', iconimg, folder=False)


def addBoard(item):
    name = extractName(item)
    item_url = extractHref(item)
    iconimage = extractImgSearch(item, name)
    mode = 'processWebPage(boardMusicList)'
    playall_title = '播放【%s】所含曲目' % name
    context = {'indent': str(True), 'playall_title': playall_title, 'playall_icon': iconimage}
    addDir(name, item_url, mode, iconimage, context=context)


# 歌手
def addArtistMusicNav(item):
    mode = 'processWebPage(artistMusicPage)'
    addNav(item, mode)


def addArtistNav(item):
    mode = 'processWebPage(artistListPage)'
    addNav(item, mode)


def addArtistList(item):
    item_url = extractHref(item.a) + "music.htm"
    name = INDENT_STR + extractName(item.a)
    mode = 'processWebPage(artistMusicPage)'
    iconimage = extractImg(item.a.img)
    addDir(name, item_url, mode, iconimage)


def addArtistCategory(item):
    item = item.h1
    item_url = "http://www.kuwo.cn%s" % extractHref(item.a)
    name = item.contents[0].encode('utf-8')
    mode = 'processWebPage(artistListPage)'
    addDir(name, item_url, mode, '')


# 分类
def addHotMusic(item):
    l = re.findall('"musiclist":(\[.+\]),"rids"', item.text)
    print '---',l,'---'
    if not l:
        return
    l = eval(l[0])
    mids = "/".join([d['musicrid'] for d in l])
    disp_title = params.get('playall_title', '播放全部歌曲')
    iconimg = params.get('playall_icon', '')
    addDir(disp_title, mids, 'PlayMusic()', iconimg, folder=False)
    for d in l:
        title = d['name']
        artist = d['artist']
        mid = d['musicrid']
        addLink(title, artist, mid, 'PlayMusic()', '')


def addHotMusicList(item):
    ''' playlist item '''
    url = extractHref(item.a)
    name = extractName(item.a)
    iconimg = extractImg(item.a.img)
    playall_title = '2 播放【%s】所含曲目' % name
    context = {'indent': str(True), 'playall_title': playall_title, 'playall_icon': iconimg}
    addDir(INDENT_STR + name, url, 'processWebPage(hotMusic)', iconimg, context=context)


def addHotList(item):
    ''' playlist item '''
    url = extractHref(item.a)
    name = extractName(item.a)

    iconimg = extractImg(item.a.img)
    playall_title = ''
    context = {'indent': str(True), 'playall_title': playall_title, 'playall_icon': iconimg}
    addDir(INDENT_STR + name, url, 'processWebPage(hotMusicListPage)', iconimg, context=context)


# 专辑
def addMusic(item):
    '''for mingxing and album'''
    artist = item.find(attrs={'class':'s_name'}).a['title'].encode('utf-8')
    title = item.find(attrs={'class':'m_name'}).a['title'].encode('utf-8')
    mid = item.find(attrs={'class':'number'}).input['mid'].encode('utf-8')
    addLink(title, artist, mid, 'PlayMusic()', '')


def addAlbumMusicList(item):
    disp_title = params.get('playall_title', '播放全部歌曲')
    iconimg = params.get('playall_icon', '')
    mids = [i.input['mid'] for i in item.find_all(attrs={'class': 'number'})]
    mids = "/".join(mids)
    addDir(disp_title, mids, 'PlayMusic()', iconimg, folder=False)


def addAlbum(item):
    # album item
    url = extractHref(item.a)
    title = extractName(item.a)
    iconimg = extractImg(item.find('img'))
    albumCont = item.findNextSibling(attrs={'class':'albumCont'})
    playall_title = '播放【' + title + '】所含曲目'
    dispname = title
    context = {'indent': str(True), 'playall_title':playall_title, 'playall_icon': iconimg}
    if 'indent' in params:
        dispname = INDENT_STR + dispname
    addDir(dispname, url, 'processWebPage(albumMusicList)', iconimg, context=context)


def addAlbumNav(item):
    mode = 'processWebPage(albums)'
    addNav(item, mode)


def addAlbumList(item):
    item_url = extractHref(item.a)
    name = item.a.string.encode('utf-8')
    mode = 'processWebPage(albums)'
    addDir(name, item_url, mode, '')


# 淘歌单
def addPlaylistMusic(item):
    s = item.string
    if not s:
        return
    l = re.findall('wbarr =(.*?);', s)
    if not l:
        return
    l = eval(l[0])
    mids = "/".join([d['rid'].split('_')[1] for d in l])
    disp_title = params.get('playall_title', '播放全部歌曲')
    iconimg = params.get('playall_icon', '')
    addDir(disp_title, mids, 'PlayMusic()', iconimg)
    for d in l:
        title = d['name']
        artist = d['art']
        mid = d['rid'].split('_')[1]
        iconimage = ''
        addLink(title, artist, mid, 'PlayMusic()', iconimage)


def addPlaylistAlbum(item):
    iconimg = extractImg(item.find('img'))
    item = item.find('a', attrs={'class': 'gdPlay'})
    url = extractHref(item)
    title = extractName(item.find_previous_sibling('a'))
    playall_title = '播放【%s】' % title
    playall_icon = iconimg
    score = item.find_next_sibling().text.encode('utf-8')
    dispname = '%s【%s】' % (title, score)
    context = {'indent': str(True), 'playall_title': playall_title, 'playall_icon': iconimg}
    if 'indent' in params:
        dispname = INDENT_STR + dispname
    addDir(dispname, url, 'processWebPage(playlistMusic)', iconimg, context=context)


def addPlaylist(item):
    addBanner(item.text.encode('utf-8'))
    items = item.find_next_sibling().find_all('li')
    for item in items:
        item = item.a
        name = extractName(item)
        item_url = extractHref(item)
        iconimage = extractImgSearch(item, name)
        mode = 'processWebPage(playlistAlbum)'
        addDir(name, item_url, mode, iconimage)


# 搜索
def addSearch(item):
    name = BANNER_FMT % item.h1.text.encode('utf-8')
    item_url = extractHref(item.h1.a)
    if item_url:
        mode = 'processSearch("%s")' % item_url
    else:
        mode = 'pass'
    addDir(name, item_url, mode, '')


def addSearchNav(item):
    item_url = extractHref(item)
    mode = 'processSearch("http://sou.kuwo.cn%s")' % item_url
    addNav(item, mode)


# 标签
boardMusic = {'tag': (None, {'class':'itemUl'}), 'vect':addBoardMusic}
boardMusicList = {'tag': (None, {'id':'container'}), 'vect':addBoardMusicList, 'child': boardMusic}
board = {'tag':('a',{}), 'vect':addBoard}
boardPage = {'tag':('ul',{'class':['borLr', 'chartList']}), 'child': board}

artistMusic = {'tag': ('li', {'class': 'clearfix'}), 'vect': addMusic}
artistMusicNav = {'tag': ('a', {}), 'vect': addArtistMusicNav}
artistMusicNavPage = {'tag': ('div', {'class': 'page'}), 'child': artistMusicNav}
artistMusicPage = [artistMusic, artistMusicNavPage]
artistListItem = {'tag': ('li', {}), 'vect': addArtistList}
artistList = {'tag': ('ul', {'class': ['singer_pic_list', 'singer_name_list']}), 'child': artistListItem}
artistNav = {'tag': ('a', {}), 'vect': addArtistNav}
artistNavPage = {'tag': ('div', {'class': 'page'}), 'child': artistNav}
artistListPage = [artistList, artistNavPage]
artistCategory = {'tag': ('div', {'class': 'top'}), 'vect': addArtistCategory}
artistPage = {'tag': ('div', {'class': 'singer'}), 'child': artistCategory}

hotMusic = {'tag': ('script', {}), 'vect': addHotMusic}
hotMusicList = {'tag': ('li', {}), 'vect': addHotMusicList}
hotMusicListPage = {'tag': ('ul', {'class': 'singer_list clearfix'}), 'child': hotMusicList}
hotList = {'tag': ('li', {}), 'vect': addHotList}
hotPage = {'tag': ('div', {'class': 'hotlist'}), 'vect': addH1Banner, 'child': hotList}

albumMusic = {'tag': ('li', {}), 'vect': addMusic}
albumMusicList = {'tag': ('div', {'class': 'm_list'}), 'vect': addAlbumMusicList, 'child': albumMusic}
album = {'tag': (None, {'class': 'music clearfix'}), 'vect': addAlbum, 'child': None}
albumNav = {'tag': ('a', {}), 'vect': addAlbumNav}
albumNavPage = {'tag': ('div', {'class': 'page'}), 'child': albumNav}
albums = [album, albumNavPage]
albumList = {'tag': ('li', {}), 'vect': addAlbumList, 'child': None}
albumPage = {'tag': (None, {'class': 'sdlist clearfix'}), 'vect': addH1Banner, 'child': albumList}

playlistMusic = {'tag': ('script', {}), 'vect': addPlaylistMusic}
playlistAlbum = {'tag': ('div', {'class': 'albumItem'}), 'vect': addPlaylistAlbum}
playlistBanner = {'tag': ('p', {'class': ['mTitBg', 'titYh', "titYh titLr"]}), 'vect': addPlaylist}
playlistPage = {'tag': ('div', {'class': 'mw300'}), 'child': playlistBanner}

searchArtist = {'tag': ('div', {'class': 'hotSinger'}), 'vect': addSearch, 'child': artistListItem}
searchMusic = {'tag': ('div', {'class': 'm_list'}), 'vect': addSearch, 'child': albumMusic}
searchAlbumItem = {'tag': ('li', {}), 'vect': addAlbum}
searchAlbum = {'tag': ('div', {'class': 'album'}), 'vect': addSearch, 'child': searchAlbumItem}
searchNav = {'tag': ('a', {}), 'vect': addSearchNav}
searchNavPage = {'tag': ('div', {'class': 'page'}), 'child': searchNav}
searchList = [searchArtist, searchMusic, searchAlbum, searchNavPage]


#   main program goes here ######################
# Choose ChineseKeyboard if script.module.keyboard.chinese is installed.
try:
    import ChineseKeyboard
    search = searchChineseKeyboard
except:
    search = searchDefaultKeyboard


print "argv0 %s" % sys.argv[0]
print "argv1 %s" % sys.argv[1]
print "argv2 %s" % sys.argv[2]

pluginhandle = int(sys.argv[1])
params = get_params(sys.argv[2])
mode = params.get('mode', None)
if mode:
    exec(mode)
else:
    # params['url'] = URL_BASE
    addDir('搜索', '', 'search()')
    addDir('排行榜', 'http://yinyue.kuwo.cn/billboard_%E9%9B%AA%E7%A2%A7%E6%98%8E%E6%98%9F%E6%A6%9C.htm', 'processWebPage(boardPage)')
    addDir('歌手', 'http://www.kuwo.cn/mingxing/', 'processWebPage(artistPage)')
    addDir('分类', 'http://yinyue.kuwo.cn/category.htm', 'processWebPage(hotPage)')
    addDir('专辑', 'http://www.kuwo.cn/album/', 'processWebPage(albumPage)')
    addDir('淘歌单', 'http://fang.kuwo.cn/p/st/PlCat', 'processWebPage(playlistPage)');
    endDir()
