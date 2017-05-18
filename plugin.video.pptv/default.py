#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import gzip
import StringIO
import datetime
import time
import socket
from random import random
import urlparse
import simplejson

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


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def urlopen_with_retry(*args, **kwargs):
    for i in range(10):
        try:
            return urllib2.urlopen(*args, **kwargs)
        except socket.timeout:
            pass


def get_html(url, headers={'User-Agent': UserAgent_IPAD}, decoded=True):
    """Gets the content of a URL via sending a HTTP GET request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """

    req = urllib2.Request(url, headers=headers)
    response = urlopen_with_retry(req)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.headers.get('Content-Encoding')
    if content_encoding == 'gzip':
        data = gzip.GzipFile(fileobj=StringIO.StringIO(data)).read()

    # Decode the response body
    if decoded:
        match = re.compile('<meta.+?charset=["]*(.+?)"').findall(data)
        if len(match):
            charset = match[0]
            data = data.decode(charset)
        else:
            data = data.decode('utf-8', 'ignore')

    return data


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


def GetPPTVVideoList(url, only_filter=False):
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
                print '==========================', name, link
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
        tmp = get_html(PPTV_SUBJECT_LIST + 'date=' + datetime.datetime.now().strftime('%Y-%m-%d') + '&type=' + PPTV_LIVE_TYPES[url])
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
        if 'page' in params.keys():
            pages_attr['selected_page'] = int(params['page'][0])
        else:
            pages_attr['selected_page'] = 1
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


def GetPPTVVideoURL_Flash(url, quality):
    data = get_html(url)
    # get video ID
    vid = re.compile('"id"\s*:\s*(\d+)\s*,').findall(data)
    if len(vid) <= 0:
        return []

    # get data
    data = get_html(PPTV_WEBPLAY_XML + 'webplay3-0-' + vid[0] + '.xml&ft=' + str(quality) + '&version=4&type=web.fpp')

    # get current file name and index
    rid = CheckValidList(parseDOM(data, 'channel', ret='rid'))
    cur = CheckValidList(parseDOM(data, 'file', ret='cur'))

    if len(rid) <= 0 or len(cur) <= 0:
        return []

    dt = CheckValidList(parseDOM(data, 'dt', attrs={'ft': cur}))
    if len(dt) <= 0:
        return []

    # get server and file key
    sh = CheckValidList(parseDOM(dt, 'sh'))
    f_key = CheckValidList(parseDOM(dt, 'key'))
    if len(sh) <= 0:
        return []

    # get segment list
    dragdata = CheckValidList(parseDOM(data, 'dragdata', attrs={'ft': cur}))
    if len(dragdata) <= 0:
        return []
    frid = re.compile('rid="(.+?)"').findall(dragdata)
    sgms = parseDOM(dragdata, 'sgm', ret='no')
    if len(sgms) <= 0:
        return []

    # STOP HERE!... FLVCD server is dead
    # get key from flvcd.com, sorry we can't get it directly by now
    parser_url1 = FLVCD_PARSER_PHP + '?format=' + PPTV_VIDEO_QUALITY_VALS[int(cur)] + '&kw=' + url

    flvcd_sc_base = CheckValidList(re.compile('\|for\|([^\|]*)\|createSc\|').findall(data))
    if len(flvcd_sc_base) <= 0:
        return []

    forms = CheckValidList(parseDOM(data, 'form', attrs={'name': 'mform'}))
    if len(forms) <= 0:
        return []
    downparseurl = CheckValidList(parseDOM(data, 'form', attrs={'name': 'mform'}, ret='action'))
    # get hidden values in form
    input_names = parseDOM(forms, 'input', attrs={'type': 'hidden'}, ret='name')
    input_values = parseDOM(forms, 'input', attrs={'type': 'hidden'}, ret='value')
    if min(len(input_names), len(input_names)) <= 0:
        return []

    input_dicts = dict(zip(input_names, input_values))
    if 'msKey' in input_dicts and 'tt' in input_dicts:
        tmp_tt = int(input_dicts["tt"])
        input_dicts["sc"] = flvcd_sc_input(flvcd_sc_base, input_dicts["msKey"], tmp_tt)

    parser_url2 = downparseurl + '?' + urllib.urlencode(input_dicts)
    data = get_html(parser_url2)
    flvcd_id = CheckValidList(re.compile('xdown\.php\?id=(\d+)').findall(data))
    if len(flvcd_id) <= 0:
        return []

    parser_url3 = FLVCD_DIY_URL + flvcd_id + '.htm'
    data = get_html(parser_url3)
    key = CheckValidList(re.compile('<U>.*&(key=[^&\n]*)').findall(data))
    if len(key) <= 0:
        return []

    url_list = []
    # add segments of video
    for sgm in sgms:
        url_list += ['http://' + sh + '/' + sgm + '/' + rid + '?type=fpp&' + key + '&k=' + f_key]
    return url_list


def constructKey(arg):

    def str2hex(s):
        r = ""
        for i in s[:8]:
            t = hex(ord(i))[2:]
            if len(t) == 1:
                t = "0" + t
            r += t
        for i in range(16):
            r += hex(int(15*random()))[2:]
        return r

    # ABANDONED  Because SERVER_KEY is static
    def getkey(s):
        # returns 1896220160
        l2 = [i for i in s]
        l4 = 0
        l3 = 0
        while l4 < len(l2):
            l5 = l2[l4]
            l6 = ord(l5)
            l7 = l6 << ((l4 % 4) * 8)
            l3 = l3 ^ l7
            l4 += 1
        return l3
        pass

    def rot(k, b): ## >>> in as3
        if k >= 0:
            return k >> b
        elif k < 0:
            return (2**32+k) >> b
        pass

    def lot(k, b):
        return (k << b) % (2**32)

    #  WTF?
    def encrypt(arg1, arg2):
        delta = 2654435769
        l3 = 16
        l4 = getkey(arg2)        # 1896220160
        l8 = [i for i in arg1]
        l10 = l4
        l9 = [i for i in arg2]
        l5 = lot(l10, 8) | rot(l10, 24)    # 101056625
        # assert l5==101056625
        l6 = lot(l10, 16) | rot(l10, 16)    # 100692230
        # assert 100692230==l6
        l7 = lot(l10, 24) | rot(l10, 8)
        # assert 7407110==l7
        l11 = ""
        l12 = 0
        l13 = ord(l8[l12]) << 0
        l14 = ord(l8[l12+1]) << 8
        l15 = ord(l8[l12+2]) << 16
        l16 = ord(l8[l12+3]) << 24
        l17 = ord(l8[l12+4]) << 0
        l18 = ord(l8[l12+5]) << 8
        l19 = ord(l8[l12+6]) << 16
        l20 = ord(l8[l12+7]) << 24

        l21 = (((0 | l13) | l14) | l15) | l16
        l22 = (((0 | l17) | l18) | l19) | l20

        l23 = 0
        l24 = 0
        while l24 < 32:
            l23 = (l23 + delta) % (2**32)
            l33 = (lot(l22, 4) + l4) % (2**32)
            l34 = (l22 + l23) % (2**32)
            l35 = (rot(l22, 5) + l5) % (2**32)
            l36 = (l33 ^ l34) ^ l35
            l21 = (l21 + l36) % (2**32)
            l37 = (lot(l21, 4) + l6) % (2**32)
            l38 = (l21 + l23) % (2**32)
            l39 = (rot(l21, 5)) % (2**32)
            l40 = (l39 + l7) % (2**32)
            l41 = ((l37 ^ l38) % (2**32) ^ l40) % (2**32)
            l22 = (l22 + l41) % (2**32)

            l24 += 1

        l11 += chr(rot(l21, 0) & 0xff)
        l11 += chr(rot(l21, 8) & 0xff)
        l11 += chr(rot(l21, 16) & 0xff)
        l11 += chr(rot(l21, 24) & 0xff)
        l11 += chr(rot(l22, 0) & 0xff)
        l11 += chr(rot(l22, 8) & 0xff)
        l11 += chr(rot(l22, 16) & 0xff)
        l11 += chr(rot(l22, 24) & 0xff)

        return l11

    loc1 = hex(int(arg))[2:]+(16 - len(hex(int(arg))[2:]))*"\x00"
    SERVER_KEY = "qqqqqww"+"\x00"*9
    res = encrypt(loc1, SERVER_KEY)
    return str2hex(res)


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def video_from_id(id):
    api = PPTV_WEBPLAY_XML + 'web-m3u8-%s.m3u8?type=m3u8.web.pad'
    api = PPTV_WEBPLAY_XML + 'webplay3-0-%s.xml?type=web.fpp'
    xml = get_html(api % id)

    #vt=3 means vod mode vt=5 means live mode
    host = r1(r'<sh>([^<>]+)</sh>', xml)
    k = r1(r'<key expire=[^<>]+>([^<>]+)</key>', xml)
    rid = r1(r'rid="([^"]+)"', xml)
    title = r1(r'nm="([^"]+)"', xml)

    st = r1(r'<st>([^<>]+)</st>', xml)[:-4]
    st = time.mktime(time.strptime(st)) - 60

    key = constructKey(st)

    pieces = re.findall('<sgm no="(\d+)"[^<>]+fs="(\d+)"', xml)
    numbers, fs = zip(*pieces)
    urls = ["http://{}/{}/{}?key={}&fpp.ver=1.3.0.4&k={}&type=web.fpp".format(host, i, rid, key, k) for i in range(max(map(int, numbers)) + 1)]

    return urls


def video_from_url(url, quality):
    assert re.match(r'http://v.pptv.com/show/(\w+)\.html$', url)
    html = get_html(url)
    id = r1(r'webcfg\s*=\s*{"id":\s*(\d+)', html)
    assert id

    return video_from_id(id)


def GetPPTVVideoURL(url, quality):
    # check whether is PPTV video
    domain = CheckValidList(re.compile('^http://(.*\.pptv\.com)/.*$').findall(url))
    if len(domain) <= 0:
        xbmcgui.Dialog().ok(__addonname__, '视频地址无效, 可能不是PPTV视频!')
        return []

    data = get_html(url)
    # new key for query XML
    kk = CheckValidList(re.compile('&kk=([^"\']*)["\'],').findall(data))

    # try to directly get iPad live video URL
    ipadurl = CheckValidList(re.compile(',\s*["\']ipadurl["\']\s*:\s*["\']([^"\']*)["\']').findall(data))

    if len(ipadurl) > 0:
        ipadurl = re.sub('\\\/', '/', ipadurl)
        # remove unneeded character if needed
        ipadurl = ipadurl.replace('}', '')
        if ipadurl.find('?type=') < 0:
            ipadurl += '?type=m3u8.web.pad'
        if len(kk) > 0:
            ipadurl += '&kk=' + kk
        ipadurl += '&o=' + domain
        return [ipadurl]


    return None

    # get sports iPad live URL
    ipadurl = CheckValidList(re.compile('["\']pbar_video_(\d+)["\']').findall(data))
    if len(ipadurl) > 0:
        return [PPTV_WEBPLAY_XML + 'web-m3u8-' + ipadurl + '.m3u8?type=m3u8.web.pad&o=' + domain]

    # try to get iPad non-live video URL
    if 'true' == __addon__.getSetting('ipad_video'):
        vid = CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*,').findall(data))
        if len(vid) <= 0:
            return []

        if len(kk) <= 0:
            return []

        # get data
        ipadurl = PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&version=4&type=m3u8.web.pad'
        if len(kk) > 0:
            ipadurl += '&kk=' + kk
        data = get_html(ipadurl)

        # get quality
        tmp = CheckValidList(parseDOM(data, 'file'))
        if len(tmp) <= 0:
            return []
        items = parseDOM(tmp, 'item', ret='rid')
        if len(items) <= 0:
            return []

        if quality >= len(items):
            # if specified quality is not in qualities list, use the last existing one
            quality = len(items) - 1

        rid = items[quality]
        cur = str(quality)

        if len(rid) <= 0 or len(cur) <= 0:
            return []

        dt = CheckValidList(parseDOM(data, 'dt', attrs={'ft': cur}))
        if len(dt) <= 0:
            return []

        # get server and file key
        sh = CheckValidList(parseDOM(dt, 'sh'))
        f_key = CheckValidList(parseDOM(dt, 'key'))
        if len(sh) <= 0:
            return []

        rid = CheckValidList(re.compile('([^\.]*)\.').findall(rid))
        httpurl = 'http://' + sh + '/' + rid + '.m3u8?type=m3u8.web.pad&k=' + f_key

        dur = re.compile('<channel .+dur="(\d+)".+>').findall(data)
        duration = int(dur[0])
        # Segment a long mv
        if duration and int(duration) > SEGSIZE:
            httpurl = Segmentation(httpurl[0], duration)
        return httpurl

    else:
        return GetPPTVVideoURL_Flash(url, quality)


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
        links += parseDOM(chl, 'a', ret='href')
        names += parseDOM(chl, 'a')

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
            '[COLOR FFFF0000]上一页[/COLOR] - 第 %d 页' % (pages_attr['selected_page'] - 1),
            '[COLOR FFFF0000]下一页[/COLOR] - 第 %d 页' % (pages_attr['selected_page'] + 1),
            '[COLOR FFFF0000]最后一页[/COLOR] - 第 %d 页' % (pages_attr['last_page'])
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
        u += '&name=' + urllib.quote_plus(title)
        u += '&thumb=' + urllib.quote_plus(i['image'])
        liz = xbmcgui.ListItem(title, thumbnailImage=i['image'])
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, is_dir)

    # show page switcher list
    if pages_attr:
        for page_link, page_str in zip(page_links, page_strs):
            if len(page_link) > 0:
                u = sys.argv[0] + '?url=' + page_link
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

    ppurls = GetPPTVVideoURL(url, quality)
    if ppurls is None:
        ppurls = video_from_url(url, quality)

    if ppurls and len(ppurls) > 0:
        playlist = xbmc.PlayList(1)
        playlist.clear()
        for i in range(0, len(ppurls)):
            title = name + ' 第 %d/%d' % (i + 1, len(ppurls)) + ' 节'
            liz = xbmcgui.ListItem(title, thumbnailImage=thumb)
            liz.setInfo(type="Video", infoLabels={"Title": title})
            playlist.add(ppurls[i], liz)
        xbmc.Player().play(playlist)
    else:
        xbmcgui.Dialog().ok(__addonname__, '无法获取视频地址!')


def listFilter(params):
    url = params['url']
    level = 0
    dialog = xbmcgui.Dialog()
    while True:
        filter_list = GetPPTVVideoList(url, True)
        # show last filter
        if level >= len(filter_list) - 1:
            level = -1
        content = [i['name'] for i in filter_list[level]['options']]
        sel = dialog.select(filter_list[level]['label'], content)
        url = filter_list[level]['options'][sel]['link']
        # reach last filter, just list specified videos
        if level < 0:
            params['url'] = url
            pret = GetPPTVVideoList(url)
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
    list_ret = GetPPTVVideoList(url)
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
