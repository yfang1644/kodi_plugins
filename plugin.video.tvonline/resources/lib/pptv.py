#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import gzip
import StringIO


UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent_IE = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'

SEGSIZE = 500
PPTV_WEBPLAY_XML = 'http://web-play.pptv.com/'
FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'


# PPTV video quality values
# Note: Blue ray video is currently only available to VIP users, so pity
PPTV_VIDEO_QUALITY_VALS = ('normal', 'high', 'super', '')

dbg = False
dbglevel = 3


def log(description, level=0):
    if dbg and dbglevel > level:
        print description


def GetHttpData(url, agent=UserAgent_IE, referer=''):
    req = urllib2.Request(url)
    req.add_header('User-Agent', agent)
    if len(referer) > 0:
        req.add_header('Referer', referer)
    try:
        response = urllib2.urlopen(req)
        httpdata = response.read()
        if response.headers.get('content-encoding') == 'gzip':
            httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
        charset = response.headers.getparam('charset')
        response.close()
    except:
        print 'GetHttpData Error: %s' % url
        return ''
    match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
    if len(match) > 0:
        charset = match[0]
    if charset:
        charset = charset.lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
    return httpdata


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


def parseDOM(html, name=u"", attrs={}, ret=False):
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
        seg1 = re.sub('%3D', '=', seg1)
        seg1 = re.sub('%26', '&', seg1)
        piece.append(seg1)
        start += during

    return piece


def GetPPTVVideoURL_Flash(url, quality):
    data = GetHttpData(url)
    # get video ID
    vid = CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*,').findall(data))
    if len(vid) <= 0:
        return []

    # get data
    data = GetHttpData(PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&ft=' + str(quality) + '&version=4&type=web.fpp')

    # get current file name and index
    rid = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'channel', ret='rid'))
    cur = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file', ret='cur'))

    if len(rid) <= 0 or len(cur) <= 0:
        return []

    dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs={'ft': cur.encode('utf-8')}))
    if len(dt) <= 0:
        return []

    # get server and file key
    sh = CheckValidList(parseDOM(dt, 'sh'))
    f_key = CheckValidList(parseDOM(dt, 'key'))
    if len(sh) <= 0:
        return []

    # get segment list
    dragdata = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dragdata', attrs={'ft': cur.encode('utf-8')}))
    if len(dragdata) <= 0:
        return []
    frid = re.compile('rid="(.+?)"').findall(dragdata)
    sgms = parseDOM(dragdata, 'sgm', ret='no')
    if len(sgms) <= 0:
        return []

    # STOP HERE!... FLVCD server is dead
    # get key from flvcd.com, sorry we can't get it directly by now
    parser_url1 = FLVCD_PARSER_PHP + '?format=' + PPTV_VIDEO_QUALITY_VALS[int(cur.encode('utf-8'))] + '&kw=' + url

    flvcd_sc_base = CheckValidList(re.compile('\|for\|([^\|]*)\|createSc\|').findall(data))
    if len(flvcd_sc_base) <= 0:
        return []

    forms = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'form', attrs={'name': 'mform'}))
    if len(forms) <= 0:
        return []
    downparseurl = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'form', attrs={'name': 'mform'}, ret='action'))
    # get hidden values in form
    input_names = parseDOM(forms.encode('utf-8'), 'input', attrs={'type': 'hidden'}, ret='name')
    input_values = parseDOM(forms.encode('utf-8'), 'input', attrs={'type': 'hidden'}, ret='value')
    if min(len(input_names), len(input_names)) <= 0:
        return []

    input_dicts = dict(zip(input_names, input_values))
    if 'msKey' in input_dicts and 'tt' in input_dicts:
        tmp_tt = int(input_dicts["tt"])
        input_dicts["sc"] = flvcd_sc_input(flvcd_sc_base, input_dicts["msKey"], tmp_tt)

    parser_url2 = downparseurl + '?' + urllib.urlencode(input_dicts)
    data = GetHttpData(parser_url2)
    flvcd_id = CheckValidList(re.compile('xdown\.php\?id=(\d+)').findall(data))
    if len(flvcd_id) <= 0:
        return []

    parser_url3 = FLVCD_DIY_URL + flvcd_id + '.htm'
    data = GetHttpData(parser_url3)
    key = CheckValidList(re.compile('<U>.*&(key=[^&\n]*)').findall(data))
    if len(key) <= 0:
        return []

    url_list = []
    # add segments of video
    for sgm in sgms:
        url_list.append('http://' + sh.encode('utf-8') + '/' + sgm.encode('utf-8') + '/' + rid.encode('utf-8') + '?type=fpp&' + key + '&k=' + f_key.encode('utf-8'))
    return url_list


def GetPPTVVideoURL(url, quality):
    domain = CheckValidList(re.compile('^http://(.*\.pptv\.com)/.*$').findall(url))

    if len(domain) <= 0:
        return []          # not in pptv

    data = GetHttpData(url)
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

    # get sports iPad live URL
    ipadurl = CheckValidList(re.compile('["\']pbar_video_(\d+)["\']').findall(data))
    if len(ipadurl) > 0:
        return [PPTV_WEBPLAY_XML + 'web-m3u8-' + ipadurl + '.m3u8?type=m3u8.web.pad&o=' + domain]

    # try to get iPad non-live video URL
    vid = CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*,').findall(data))
    if len(vid) <= 0 or len(kk) <= 0:
        return []

    # get data
    ipadurl = PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&version=4&type=m3u8.web.pad'
    if len(kk) > 0:
        ipadurl += '&kk=' + kk
    data = GetHttpData(ipadurl)

    # get quality
    tmp = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file'))
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

    dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs={'ft': cur.encode('utf-8')}))
    if len(dt) <= 0:
        return []

    # get server and file key
    sh = CheckValidList(parseDOM(dt, 'sh'))
    f_key = CheckValidList(parseDOM(dt, 'key'))
    if len(sh) <= 0:
        return []

    rid = CheckValidList(re.compile('([^\.]*)\.').findall(rid))
    httpurl = ['http://' + sh + '/' + rid + '.m3u8?type=m3u8.web.pad&k=' + f_key]

    dur = re.compile('<channel .+dur="(\d+)".+>').findall(data)
    duration = int(dur[0])
    # Segment a long mv
    if duration and int(duration) > SEGSIZE:
        httpurl = Segmentation(httpurl[0], duration)
        return httpurl

    # Last resort
    return GetPPTVVideoURL_Flash(url, quality)
