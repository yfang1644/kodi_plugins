#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import time
from random import random
import urlparse
import simplejson
from common import get_html
from pptv import video_from_url

# Plugin constants
__addon__     = xbmcaddon.Addon()
__addonid__   = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent_IE = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'

SEGSIZE = 900
PPTV_LIST = 'http://list.pptv.com/'
PPTV_WEBPLAY_XML = 'http://web-play.pptv.com/'
PPTV_TV_LIST = 'http://live.pptv.com/list/tv_list'
PPTV_META_JSON = 'http://svcdn.pptv.com/show/v2/meta.json'
PPTV_PLAYLIST_JSON = 'http://svcdn.pptv.com/show/v2/playlist.json'
FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'
PPTV_SEARCH_URL = 'http://search.pptv.com/s_video?kw='
PPTV_TV_AREA_URL = 'http://live.pptv.com/api/tv_list?area_id='
PPTV_SUBJECT_LIST = 'http://live.pptv.com/api/subject_list?'


# PPTV video qualities
PPTV_VIDEO_NORMAL = 0
PPTV_VIDEO_HD = 1
PPTV_VIDEO_FHD = 2
PPTV_VIDEO_BLUER = 3

# PPTV video quality values
# Note: Blue ray video is currently only available to VIP users, so pity
PPTV_VIDEO_QUALITY_VALS = ('normal', 'high', 'super', '')

PPTV_EM_QUALITY_VALS = ('收费', '超清', '蓝光', 'VIP', '登录', '独家', '首播', '最新', '直播')

PPTV_TV_AREAS = 35
PPTV_LIVE_TYPES = {'http://live.pptv.com/list/sports_program/': '35',
                   'http://live.pptv.com/list/game_program/': '5',
                   'http://live.pptv.com/list/finance/': '47'}

##### Common functions #####

dbg = False
dbglevel = 3


def log(description, level=0):
    if dbg and dbglevel > level:
        print description


def _getDOMContent(html, name, match, ret):  # Cleanup
    log("match: " + match, 3)

    endstr = u"</" + name  # + ">"

    start = html.find(match)
    end = html.find(endstr, start)
    pos = html.find("<" + name, start + 1)

    log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

    while pos < end and pos != -1:  # Ignore too early </endstr> return
        tend = html.find(endstr, end + len(endstr))
        if tend != -1:
            end = tend
        pos = html.find("<" + name, pos + 1)
        log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

    log("start: %s, len: %s, end: %s" % (start, len(match), end), 3)
    if start == -1 and end == -1:
        result = u""
    elif start > -1 and end > -1:
        result = html[start + len(match):end]
    elif end > -1:
        result = html[:end]
    elif start > -1:
        result = html[start + len(match):]

    if ret:
        endstr = html[end:html.find(">", html.find(endstr)) + 1]
        result = match + result + endstr

    log("done result length: " + str(len(result)), 3)
    return result


def _getDOMAttributes(match, name, ret):
    log("", 3)
    lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
    ret = []
    for tmp in lst:
        cont_char = tmp[0]
        if cont_char in "'\"":
            log("Using %s as quotation mark" % cont_char, 3)

            # Limit down to next variable.
            if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

            # Limit to the last quotation mark
            if tmp.rfind(cont_char, 1) > -1:
                tmp = tmp[1:tmp.rfind(cont_char)]
        else:
            log("No quotation mark found", 3)
            if tmp.find(" ") > 0:
                tmp = tmp[:tmp.find(" ")]
            elif tmp.find("/") > 0:
                tmp = tmp[:tmp.find("/")]
            elif tmp.find(">") > 0:
                tmp = tmp[:tmp.find(">")]

        ret.append(tmp.strip())

    log("Done: " + repr(ret), 3)
    if len(ret) <= 0:
        ret.append('')
    return ret


def _getDOMElements(item, name, attrs):
    log("", 3)
    lst = []
    for key in attrs:
        lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
        if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
            lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

        if len(lst) == 0:
            log("Setting main list " + repr(lst2), 5)
            lst = lst2
            lst2 = []
        else:
            log("Setting new list " + repr(lst2), 5)
            test = range(len(lst))
            test.reverse()
            for i in test:  # Delete anything missing from the next list.
                if not lst[i] in lst2:
                    log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 3)
                    del(lst[i])

    if len(lst) == 0 and attrs == {}:
        log("No list found, trying to match on name only", 3)
        lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
        if len(lst) == 0:
            lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

    log("Done: " + str(type(lst)), 3)
    return lst


def parseDOM(html, name='', attrs={}, ret=False):
    log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)

    if isinstance(html, str): # Should be handled
        html = [html]
    elif isinstance(html, unicode):
        html = [html]
    elif not isinstance(html, list):
        log("Input isn't list or string/unicode.")
        return u""

    if not name.strip():
        log("Missing tag name")
        return u""

    ret_lst = []
    for item in html:
        temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
        for match in temp_item:
            item = item.replace(match, match.replace("\n", " "))

        lst = _getDOMElements(item, name, attrs)

        if isinstance(ret, str):
            log("Getting attribute %s content for %s matches " % (ret, len(lst)), 3)
            lst2 = []
            for match in lst:
                lst2 += _getDOMAttributes(match, name, ret)
            lst = lst2
        else:
            log("Getting element content for %s matches " % len(lst), 3)
            lst2 = []
            for match in lst:
                log("Getting element content for %s" % match, 4)
                temp = _getDOMContent(item, name, match, ret).strip()
                item = item[item.find(temp, item.find(match)) + len(temp):]
                lst2.append(temp)
            lst = lst2
        ret_lst += lst

    log("Done: " + repr(ret_lst), 3)
    return ret_lst


def CheckValidList(val):
    return (len(val) > 0 and val[0] or '')
##### Common functions end #####


def GetPPTVVideoList(url, thispage, only_filter=False):
    data = get_html(url)

    filter_list = []
    # get common video filters like: type/year/location...

    tmp = parseDOM(data, 'div', attrs={'class': 'sear-menu'})
    if len(tmp) > 0:
        filters = parseDOM(tmp[0], 'dt')
        dd = parseDOM(tmp[0], 'dd')
        for k in range(len(filters)):
            links = parseDOM(dd[k], 'a', ret='href')
            names = parseDOM(dd[k], 'a')
            label = re.sub('^按', '', filters[k].encode('utf-8'))
            # remove dummy string after colon
            pos = label.find('：')
            if pos > 0:
                label = label[0:pos+3]
            # ugly, try two different class to get selected one
            selected_name = CheckValidList(parseDOM(dd[k], 'a', attrs={'class': 'all'})).encode('utf-8')
            # select first type if can't get selected one
            if len(selected_name) <= 0 and len(names) > 0:
                selected_name = names[0].encode('utf-8')
            filter_list.append({
                'label': label,
                'selected_name': selected_name,
                'options': [{'link': i.encode('utf-8'), 'name': j.encode('utf-8')} for i, j in zip(links, names)]
            })

    # get special video filters like: update time
    tmp = parseDOM(data, 'div', attrs={'class': 'sort-result-container'})
    if len(tmp) > 0:
        s_dict = {'label': '排序', 'selected_name': '', 'options': []}
        filters = parseDOM(tmp[0], 'li')
        sclass = parseDOM(tmp[0], 'li', ret='class')
        for i, j in zip(filters, sclass):
            sname = CheckValidList(parseDOM(i, 'a')).encode('utf-8')
            slink = CheckValidList(parseDOM(i, 'a', ret='href')).encode('utf-8')
            if j == 'now':
                s_dict['selected_name'] = sname
            s_dict['options'].append({'link': slink, 'name': sname})
        filter_list.append(s_dict)

    # whether just need to get filter
    if only_filter:
        return filter_list

    # get non-live videos
    video_list = []
    videos = parseDOM(data, 'a', attrs={'class': 'ui-list-ct'})
    video_names = parseDOM(data, 'a', attrs={'class': 'ui-list-ct'}, ret='title')
    video_links = parseDOM(data, 'a', attrs={'class': 'ui-list-ct'}, ret='href')
    for i in range(len(videos)):
        tmp = CheckValidList(parseDOM(videos[i], 'p', attrs={'class': 'ui-pic'}))
        spcs = []
        # get mask
        mask = CheckValidList(parseDOM(videos[i], 'span', attrs={'class': 'msk-txt'})).encode('utf-8')
        mask.strip()
        # get video quality
        em_class = CheckValidList(parseDOM(tmp, 'em', ret='class')).encode('utf-8')
        if len(em_class) > 0:
            em_class = CheckValidList(re.compile('cover ico_(\d+)').findall(em_class))
            if len(em_class) > 0:
                spcs.append('[' + PPTV_EM_QUALITY_VALS[int(em_class) - 1] + ']')
        # get video updates
        if len(mask) > 0:
            spcs.append('(' + mask + ')')
        video_list.append({
            'link': video_links[i].encode('utf-8'),
            'name': video_names[i].encode('utf-8'),
            'image': CheckValidList(parseDOM(videos[i], 'img', ret='data-src2')).encode('utf-8'),
            'isdir': 1,
            'spc': ' '.join(spcs)
        })

    # get TV list
    if url == PPTV_TV_LIST:
        for i in range(PPTV_TV_AREAS):
            tmp = get_html(PPTV_TV_AREA_URL + str(i + 1))
            tmp = re.sub('^\s*\(', '', tmp)
            tmp = re.sub('\)\s*$', '', tmp)
            try:
                pptmp = simplejson.loads(tmp)
            except:
                continue
            channel = parseDOM(pptmp['html'], 'td', attrs={'class': 'show_channel'})
            playing = parseDOM(pptmp['html'], 'td', attrs={'class': 'show_playing'})

            for i, j in zip(channel, playing):
                name = CheckValidList([t for t in parseDOM(i, 'a') if t.find('<img') < 0]).encode('utf-8')
                image = CheckValidList(parseDOM(i, 'img', ret='src')).encode('utf-8')
                link = CheckValidList(parseDOM(j, 'a', ret='href')).encode('utf-8')
                if len(parseDOM(j, 'span', attrs={'class': 'titme'})) <= 0:
                    spc = ''
                else:
                    spc = parseDOM(j, 'span')[-1].encode('utf-8')
                video_list.append({
                    'link': link,
                    'name': name,
                    'image': image,
                    'isdir': 0,
                    'spc': (len(spc) > 0 and '(' + spc + ')' or '')
                })
    elif url in PPTV_LIVE_TYPES:
        tmp = get_html(PPTV_SUBJECT_LIST + 'date=' + time.strftime('%Y-%m-%d', time.localtime()) + '&type=' + PPTV_LIVE_TYPES[url])
        tmp = re.sub('\s*\(', '', tmp)
        tmp = re.sub('\)\s*$', '', tmp)
        pptmp = simplejson.loads(tmp)
        stime = parseDOM(pptmp['html'], 'td', attrs={'class': 'show_time'})
        ssort = parseDOM(pptmp['html'], 'td', attrs={'class': 'show_sort'})
        stitle = parseDOM(pptmp['html'], 'div', attrs={'class': 'show_box'})
        for i, j, k in zip(stime, ssort, stitle):
            sname = parseDOM(j, 'a')
            slist = parseDOM(k, 'div', attrs={'class': 'studio_list'})
            if len(sname) > 0 and len(slist) > 0:
                name = sname[-1].encode('utf-8')
                image = CheckValidList(parseDOM(j, 'img', ret='src')).encode('utf-8')
                link = re.sub('".*$', '', CheckValidList(parseDOM(slist[0], 'a', ret='href'))).encode('utf-8')
                spc = i.encode('utf-8') + ' ' + re.sub('\n.*', '', re.sub('<[^>]*>', '', k)).encode('utf-8')
                video_list.append({
                    'link': link,
                    'name': name,
                    'image': image,
                    'isdir': 0,
                    'spc': (len(spc) > 0 and '(' + spc + ')' or '')
                })

    # get page lists
    page = CheckValidList(parseDOM(data, 'p', attrs={'class': 'pageNum'})).encode('utf-8')

    pages_attr = {}
    if len(page) > 0:
        pages_attr['last_page'] = int(CheckValidList(re.compile('.*/\s*(\d+)').findall(page)))
        params = urlparse.parse_qs(urlparse.urlparse(url).query)

        thispage = params.get('page', [1])
        pages_attr['selected_page'] = int(thispage[0])
        tmp = re.sub('&page=\d+', '', url)
        if pages_attr['selected_page'] > 1:
            pages_attr['prev_page_link'] = tmp + '&page=' + str(pages_attr['selected_page'] - 1)
        else:
            pages_attr['prev_page_link'] = ''
        if pages_attr['selected_page'] < pages_attr['last_page']:
            pages_attr['next_page_link'] = tmp + '&page=' + str(pages_attr['selected_page'] + 1)
        else:
            pages_attr['next_page_link'] = ''
        # get first and last page
        pages_attr['first_page_link'] = tmp + '&page=1'
        pages_attr['last_page_link'] = tmp + '&page=' + str(pages_attr['last_page'])

    return (filter_list, video_list, pages_attr)


def GetPPTVEpisodesList(params):
    name = params['name']
    url = params['url']
    thumb = params['thumb']

    # check whether is VIP video
    if re.match('^http://.*vip\.pptv\.com/.*$', url):
        xbmcgui.Dialog().ok(__addonname__, '暂时无法观看PPTV VIP视频!')
        return []

    data = get_html(url)

    # get channel ID
    cid = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']id["\']\s*:\s*(\d+)\s*,').findall(data))
    pid = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']pid["\']\s*:\s*["\']?\s*(\d+)["\']?\s*,').findall(data))
    channel_id = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']channel_id["\']\s*:\s*["\']?\s*(\d+)["\']?\s*,').findall(data))
    cat_id = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']cat_id["\']\s*:\s*["\']?\s*(\d+)["\']?\s*,').findall(data))

    ppi_url = 'http://tools.aplusapi.pptv.com/get_ppi'
    html = get_html(ppi_url)
    data = re.compile('\((.+)\)').findall(html)
    try:
        jsdata = simplejson.loads(data[0])
        ppi_cookie = jsdata['ppi']
        api_url = 'http://apis.web.pptv.com/show/videoList?from=web&version=1.0.0&format=jsonp&cb=videolist_request&pid=%s&cat_id=%s'
        html = get_html(api_url % (pid, cat_id),
                        headers={'Cookie': 'ppi=' + ppi_cookie})
        data = re.compile('\((.+)\)').findall(html)
        jsdata = simplejson.loads(data[0])
        ppvideos = jsdata['data']['list']
        video_list = []
        for video in ppvideos:
            video_list.append({
                'link': video['url'].encode('utf-8'),
                'name': video['title'].encode('utf-8'),
                'image': video['capture'].encode('utf-8'),
                'isdir': -1,
                'spc': ''
            })
        return video_list
    except:
        pass

    if len(cid) > 0 or len(pid) > 0 or len(channel_id) > 0:
        video_list = []

        tmpid = (len(cid) > 0 and cid or channel_id)
        tmp = get_html(PPTV_META_JSON + '?cid=' + tmpid)
        pptmp = simplejson.loads(tmp)
        if pptmp['err'] != 0 or 'count' in pptmp['data']:
            tmp = get_html(PPTV_PLAYLIST_JSON + '?pindex=1&psize=' + str('count' in pptmp['data'] and pptmp['data']['count'] or 500) + '&sid=' + (int(pid) <= 0 and tmpid or pid))
            ppvideos = simplejson.loads(tmp)
            for video in ppvideos['data']['videos']:
                link = re.sub('\[URL\]', video['url'], ppvideos['data']['urlFormat'])
                image = re.sub('\[SN\]', str(video['sn']), ppvideos['data']['picUrlFormat'])
                image = re.sub('\[PIC\]', str(video['cid']), image)
                video_list.append({
                    'link': link.encode('utf-8'),
                    'name': video['title'].encode('utf-8'),
                    'image': image.encode('utf-8'),
                    'isdir': -1,
                    'spc': ''
                })
            return video_list

    # no channel ID, maybe only contain one video link
    tmp = CheckValidList(parseDOM(data, 'p', attrs={'class': 'btn_play'}))
    if len(tmp) > 0:
        links = parseDOM(tmp, 'a', ret='href')
        return [{'link': i,
                 'name': name,
                 'image': thumb,
                 'isdir': 0,
                 'spc': ''} for i in links]
    else:
        return None


# generate sc_input for flvcd parser
def flvcd_sc_input(sc_base, sc_in, sc_time):
    sc_t = int(sc_time / 600000)
    sc_out = ""

    for i in range(0, len(sc_in)):
        j = (ord(sc_in[i]) ^ ord(sc_base[i]) ^ sc_t) % ord('z')
        c = ''
        if j < ord('0'):
            c = chr(ord('0') + j % 9)
        elif j >= ord('0') and j <= ord('9'):
            c = chr(j)
        elif j > ord('9') and j < ord('A'):
            c = '9'
        elif j >= ord('A') and j <= ord('Z'):
            c = chr(j)
        elif j > ord('Z') and j < ord('a'):
            c = 'Z'
        elif j >= ord('z') and j <= ord('z'):
            c = chr(j)
        else:
            c = 'z'
        sc_out += c
    return sc_out


# Cut m3u8 into each 300 seconds (5 minutes)
def Segmentation(httpurl, duration):
    piece = []
    during = SEGSIZE
    start = 0
    while start < duration:
        if start + during > duration:
            during = duration - start
        seg1 = re.sub('m3u8\?type=m3u8',
                      'ts?start=%d&during=%d&type=m3u8'%(start, during), httpurl)
        #seg1 = re.sub('%3D', '=', seg1)
        #seg1 = re.sub('%26', '&', seg1)
        piece.append(seg1)
        start += during

    return piece


def GetPPTVSearchList(url, matchnameonly=None):
    video_list = []
    data = get_html(url)
    tmp = parseDOM(data, 'div', attrs={'class': "scon cf"})
    for sres in tmp:
        spcs = []
        slink = parseDOM(sres, 'div', attrs={'class': 'bpic fl'})
        if len(slink) <= 0:
            continue

        # get real name
        sname = CheckValidList(re.compile('title="([^\"]*)"').findall(slink[0].encode('utf-8')))
        links = parseDOM(slink[0], 'a', ret='href')
        if len(sname) <= 0 or len(links) <= 0:
            continue

        # whether need to only match specified video name
        if matchnameonly and sname == matchnameonly:
            return CheckValidList(links).encode('utf-8')

        images = parseDOM(sres, 'img', ret='src')
        # check whether has child
        child = parseDOM(sres, 'ul', attrs={'class': 'dlist2 cf'}, ret='class')
        # get video updates
        tinfos = parseDOM(slink[0], 'span', attrs={'class': 'msk-txt'})
        spcs.extend(['(' + re.sub('<\?.*$', '', i.encode('utf-8').strip()) + ')' for i in tinfos])
        video_list.append({
            'link': CheckValidList(links).encode('utf-8'),
            'name': sname,
            'image': CheckValidList(images).encode('utf-8'),
            'isdir': (len(child) > 0 and 1 or 1),
            'spc': ' '.join(spcs)
        })

    # find nothing for specified video name
    if matchnameonly:
        return ''
    return video_list

##### PPTV functions end #####


def listRoot():
    # show search entry
    u = sys.argv[0] + '?mode=search'
    liz = xbmcgui.ListItem('[COLOR FF00FFFF]<按此进行搜索...>[/COLOR]')
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False)

    links = [PPTV_TV_LIST]
    names = [u'全国电视台']

    data = get_html(PPTV_LIST)
    chl = CheckValidList(parseDOM(data, 'div', attrs={'class': 'detail_menu'}))
    if len(chl) > 0:
        links = parseDOM(chl, 'a', ret='href')
        names = parseDOM(chl, 'a')

    data = get_html('http://www.pptv.com')
    chl = CheckValidList(parseDOM(data, 'div', attrs={'class': 'morech cf'}))
    if len(chl) > 0:
        links += parseDOM(chl, 'a', ret='href')
        names += parseDOM(chl, 'a')

    for i, j in zip(links, names):
        u = sys.argv[0] + '?url=' + i + '&mode=videolist&name=' + j
        liz = xbmcgui.ListItem(j)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def listVideo(params, list_ret):
    name = params['name']
    url = params.get('url')
    filter_list, video_list, pages_attr = list_ret
    u = ''
    total_items = len(video_list) + 2

    # show name and page index
    title = '[COLOR FFFF0000]当前:[/COLOR] ' + name + ' (第'
    if pages_attr:
        title += str(pages_attr['selected_page']) + '/' + str(pages_attr['last_page'])
        # contribute first/previous/next/last page link and name
        page_links = [
            pages_attr['first_page_link'],
            pages_attr['prev_page_link'],
            pages_attr['next_page_link'],
            pages_attr['last_page_link']]
        page_strs = [
            '[COLOR FFFF0000]第一页[/COLOR] - 第 1 页',
            '[COLOR FFFF0000]上一页[/COLOR] - 第 %s 页' % (pages_attr['selected_page'] - 1),
            '[COLOR FFFF0000]下一页[/COLOR] - 第 %s 页' % (pages_attr['selected_page'] + 1),
            '[COLOR FFFF0000]最后一页[/COLOR] - 第 %s 页' % (pages_attr['last_page'])
            ]
        # increate extra page items length
        total_items += len([i for i in page_links if len(i) > 0])
    else:
        title += '1/1'
    title += '页)'

    # show filter conditions if needed
    if filter_list and len(filter_list) > 0:
        tmp = ['[COLOR FF00FF00]' + i['label'] + '[/COLOR]' + i['selected_name'] for i in filter_list]
        title += ' [' + '/'.join(tmp) + '] (按此选择)'
        u = sys.argv[0] + '?url=' + url + '&mode=filterlist&name=' + name
    # add first item
    liz = xbmcgui.ListItem(title)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)

    # show video list
    playlist = xbmc.PlayList(1)
    playlist.clear()

    number = 0
    for i in video_list:
        title = i['name']
        if len(i['spc']) > 0:
            title += ' ' + i['spc']
        is_dir = False
        # check whether is an episode target
        if (i['isdir'] > 0) or ((i['isdir'] < 0) and (not re.match('^http://v\.pptv\.com/show/.*$', i['link']))):
            is_dir = True
        u = sys.argv[0] + '?url=' + i['link']
        u += '&mode=' + (is_dir and 'episodelist' or 'playvideo')
        u += '&name=%d.' % number + urllib.quote_plus(title)
        u += '&thumb=' + urllib.quote_plus(i['image'])
        liz = xbmcgui.ListItem(title, thumbnailImage=i['image'])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, is_dir)
        playlist.add(i['link'], liz)
        number += 1

    # show page switcher list
    if pages_attr:
        for page_link, page_str in zip(page_links, page_strs):
            if len(page_link) > 0:
                u = sys.argv[0] + '?url=' + urllib.quote_plus(page_link)
                u += '&mode=videolist&name=' + urllib.quote_plus(name)
                liz = xbmcgui.ListItem(page_str)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True)

    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playVideo(params):
    name = params['name']
    url = params['url']
    thumb = params['thumb']

    quality = int(__addon__.getSetting('movie_quality'))
    # if live page without video link, try to get video link from search result
    #if re.match('^http://live\.pptv\.com/list/tv_program/.*$', url):
    #    url = GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(name), name)
    playmode = __addon__.getSetting('video_vplaycont')

    playlist = xbmc.PlayList(0)
    playlist.clear()

    playlistA = xbmc.PlayList(1)
    psize = playlistA.size()
    tmp = name.split('.')
    v_pos = int(tmp[0])
    name = '.'.join(tmp[1:])

    for x in range(v_pos, psize):
        p_item = playlistA.__getitem__(x)
        p_url = p_item.getfilename(x)
        p_list = p_item.getdescription(x)
        li = p_item
        li.setInfo(type="Video", infoLabels={"Title": p_list})

        ppurls = video_from_url(p_url, level=quality)
        if ppurls and len(ppurls) > 0:
            for i in range(0, len(ppurls)):
                title = p_list + ' 第 %d/%d' % (i + 1, len(ppurls)) + ' 节'
                liz = xbmcgui.ListItem(title, thumbnailImage=thumb)
                liz.setInfo(type='Video', infoLabels={'Title': title})
                playlist.add(ppurls[i], liz)
        else:
            # xbmcgui.Dialog().ok(__addonname__, '无法获取视频地址!')
            continue

        if x == v_pos:
            xbmc.Player(0).play(playlist)
        if playmode == 'false':
            break


def listFilter(params):
    url = params['url']
    page = params.get('page')
    level = 0
    dialog = xbmcgui.Dialog()
    while True:
        filter_list = GetPPTVVideoList(url, page, True)
        # show last filter
        if level >= len(filter_list) - 1:
            level = -1
        content = [i['name'] for i in filter_list[level]['options']]
        sel = dialog.select(filter_list[level]['label'], content)
        url = filter_list[level]['options'][sel]['link']
        # reach last filter, just list specified videos
        if level < 0:
            params['url'] = url
            pret = GetPPTVVideoList(url, page)
            listVideo(params, pret)
            return
        level += 1


def searchPPTV():
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        key = keyboard.getText()
        if len(key) > 0:
            u = sys.argv[0] + '?mode=searchlist&key=' + key
            xbmc.executebuiltin('Container.Update(%s)' % u)


def listSubMenu(params):
    url = params['url']
    page = params.get('page')
    list_ret = GetPPTVVideoList(url, page)
    listVideo(params, list_ret)


def listEpisode(params):
    video_list = GetPPTVEpisodesList(params)
    if video_list is None:
        playVideo(params)
    else:
        listVideo(params, (None, video_list, None))


def searchResult(params):
    key = params['key']
    video_list = GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(key))
    params['name'] = '搜索结果 - ' + params.get('key', '')
    listVideo(params, (None, video_list, None))


# main programs goes here #########################################
params = sys.argv[2][1:]
params = dict(urllib2.urlparse.parse_qsl(params))

mode = params.get('mode')

runlist = {
    None: 'listRoot()',
    'videolist': 'listSubMenu(params)',
    'episodelist': 'listEpisode(params)',
    'playvideo': 'playVideo(params)',
    'filterlist': 'listFilter(params)',
    'search': 'searchPPTV()',
    'searchlist': 'searchResult(params)'
}

exec(runlist[mode])
