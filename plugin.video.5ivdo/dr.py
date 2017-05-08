#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import re
import sys
import gzip
import StringIO
import urlparse
import cookielib
from random import random
import base64
import time
try:
    import simplejson
except ImportError:
    import json as simplejson

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

RUNFLAG = 0

def GetHttpData(url):
    global RUNFLAG
    if (RUNFLAG == 0):
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [('Cookie', '__ysuid={0}'.format(time.time()))]
        urllib2.install_opener(opener)
        RUNFLAG = RUNFLAG + 1

    req = urllib2.Request(url)
    req.add_header('User_Agent', 'Mozilla/5.0 (X11; Linux x86_64) {0}{1}'.
                       format('AppleWebKit/537.36 (KHTML, like Gecko) ',
                              'Chrome/28.0.1500.71 Safari/537.36'))
    if (url.find('play.youku.com') != -1):
        req.add_header('referer', 'http://static.youku.com')
    response = urllib2.urlopen(req)
    httpdata = response.read()
    if response.headers.get('content-encoding') == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('<meta http-equiv="[Cc]ontent-[Tt]ype" content="text/html; charset=(.+?)"').findall(httpdata)
    if len(match) <= 0:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if len(match) > 0:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')
    return httpdata


class IFENG_DR:
    def GetPlayList(self, vid):
        url = 'http://vxml.ifengimg.com/video_info_new/' + vid[34:35]+'/'+vid[34:36] + '/' + vid +'.xml'
        link = GetHttpData(url)
        lst = re.compile('<video mediaType="mp4".+?VideoPlayUrl="(.+?)">').findall(link)
        return 'SINGLE', lst[len(lst)-1]


class DENG_DR:
    def GetPlayList(self, vid):
        url = 'http://www.5ivdo.com/deng.php?ckid='+vid
        link = GetHttpData(url)
        lst = re.compile('<file><\!\[CDATA\[(http.+?)\]\]></file>').findall(link)
        return 'SINGLE', lst[0]


class YOUKU_DR:
    f_code_1 = 'becaf9be'
    f_code_2 = 'bf7e5f01'

    def __init__(self):
        return

    def trans_e(self, a, c):
        b = range(256)
        f = 0
        result = ''
        h = 0
        while h < 256:
            f = (f + b[h] + ord(a[h % len(a)])) % 256
            b[h], b[f] = b[f], b[h]
            h += 1
        q = f = h = 0
        while q < len(c):
            h = (h + 1) % 256
            f = (f + b[h]) % 256
            b[h], b[f] = b[f], b[h]
            if isinstance(c[q], int):
                result += chr(c[q] ^ b[(b[h] + b[f]) % 256])
            else:
                result += chr(ord(c[q]) ^ b[(b[h] + b[f]) % 256])
            q += 1
        return result

    def selResolution(self, streamtypes):
        for i in range(0, len(streamtypes)):
            if streamtypes[i] == 'mp4':
                return streamtypes[i]
        # return 'mp4'
        return streamtypes[0]

    def getFileIDMixString(self, seed):
        mixed = []
        source = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ/\:._-1234567890")
        seed = float(seed)
        for i in range(len(source)):
            seed = (seed * 211 + 30031) % 65536
            index = int(seed / 65536 * len(source))
            mixed.append(source[index])
            source.remove(source[index])
        return mixed

    def getFileId(self, fileId, seed):
        mixed = self.getFileIDMixString(seed)
        ids = fileId.split('*')
        realId = []
        for i in range(0, len(ids)-1):
            realId.append(mixed[int(ids[i])])
        return ''.join(realId)

    def get_sid(self, ep):
        e_code = self.trans_e(self.f_code_1, base64.b64decode(ep))
        return e_code.split('_')

    def generate_ep(self, fileid, sid, token):
        ep = urllib.quote(base64.b64encode(
            ''.join(self.trans_e(
                self.f_code_2,
                '%s_%s_%s' % (sid, fileid, token)))),
            '~()*!.\''
            )
        return ep

    def GetPlayList(self, vid):
        urls = []
        stypes = ['mp4hd2', 'mp4hd', 'flvhd']
        url  = 'http://play.youku.com/play/get.json?vid=%s&ct=12' % vid
        json_response = simplejson.loads(GetHttpData(url))
        movdat = json_response['data']
        oip = movdat['security']['ip']
        ep  = movdat['security']['encrypt_string']
        sid, token = self.get_sid(ep)
        url = 'http://play.youku.com/play/get.json?vid=%s&ct=10' % vid
        json_response = simplejson.loads(GetHttpData(url))
        movdat = json_response['data']
        stream=movdat['stream'][0]
        for t in stypes:
            for s in movdat['stream']:
                if s['stream_type'] == t:
                    stream = s
                    break
        segs = stream['segs']

        for no in range(len(segs)):
            k = segs[no]['key']
            fileid = segs[no]['fileid']
            ep = self.generate_ep(fileid, sid, token)
            query = urllib.urlencode(dict(
                ctype=12, ev =1, K=k, ep=urllib.unquote(ep), oip=oip, token=token, yxon = 1
             ))
            u = 'http://k.youku.com/player/getFlvPath/sid/{sid}_00/st/{container}/fileid/{fileid}?{q}'.format(
                    sid       = sid,
                    container = 'flv' , #resolution_map[resolution],
                    fileid    = fileid,
                    q         = query
            )
#            urls.append(u)
            urls += [i['server'] for i in simplejson.loads(GetHttpData(u))]
        return 'MULTI', urls


# http://hot.vrs.sohu.com/vrs_flash.action?vid=2339874
class SOHU_DR:
    def __init__(self):
        return

    def real_url(self, host, vid, tvid, new, clipURL, ck):
        url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ ck+'&vid='+str(vid)+'&uid='+str(int(time.time()*1000))+'&t='+str(random())+'&rb=1'
        link = GetHttpData(url)
        return simplejson.loads(link)['url']

    def get_hqvid(self, ppage):
        match = re.compile('"norVid":(.+?),"highVid":(.+?),"superVid":(.+?),"oriVid":(.+?), ').search(ppage)
        if match:
            if match.group(4) != '0':
                return match.group(4)
            if match.group(3) != '0':
                return match.group(3)
            if match.group(2) != '0':
                return match.group(2)
            if match.group(1) != '0':
                return match.group(1)
        else:
            return 'ERROR'

    def GetPlayList(self, pvid):
        link = GetHttpData('http://hot.vrs.sohu.com/vrs_flash.action?vid='+pvid)
        hqvid = self.get_hqvid(link)
        if hqvid == 'ERROR':
            return 'ERROR', ''
        if hqvid != pvid:
            link = GetHttpData('http://hot.vrs.sohu.com/vrs_flash.action?vid='+hqvid)
        info = simplejson.loads(link)
        host = info['allot']
        tvid = info['tvid']
        urls = []
        data = info['data']
#        assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
        for new, clip, ck, in zip(data['su'], data['clipsURL'], data['ck']):
            clipURL = urlparse.urlparse(clip).path
            urls.append(self.real_url(host, hqvid, tvid, new, clipURL, ck)+'|Range=')
        return 'MULTI', urls


class PPTV_DR:
    def __init__(self):
        return

    def CheckValidList(self, val):
        return (len(val) > 0 and val[0] or '')

    def _getDOMAttributes(self, match, name, ret):
        lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
        ret = []
        for tmp in lst:
            cont_char = tmp[0]
            if cont_char in "'\"":
                if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
                    tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]
            if tmp.rfind(cont_char, 1) > -1:
                tmp = tmp[1:tmp.rfind(cont_char)]
            else:
                if tmp.find(" ") > 0:
                    tmp = tmp[:tmp.find(" ")]
                elif tmp.find("/") > 0:
                    tmp = tmp[:tmp.find("/")]
                elif tmp.find(">") > 0:
                    tmp = tmp[:tmp.find(">")]
            ret.append(tmp.strip())
        if len(ret) <= 0:
            ret.append('')
        return ret

    def _getDOMElements(self, item, name, attrs):
        lst = []
        for key in attrs:
            lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
            if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
                lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)
            if len(lst) == 0:
                lst = lst2
                lst2 = []
            else:
                test = range(len(lst))
                test.reverse()
                for i in test:  # Delete anything missing from the next list.
                    if not lst[i] in lst2:
                        del(lst[i])
        if len(lst) == 0 and attrs == {}:
            lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
            if len(lst) == 0:
                lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)
        return lst

    def _getDOMContent(self, html, name, match, ret):  # Cleanup
        endstr = u"</" + name  # + ">"
        start = html.find(match)
        end = html.find(endstr, start)
        pos = html.find("<" + name, start + 1)
        while pos < end and pos != -1:  # Ignore too early </endstr> return
            tend = html.find(endstr, end + len(endstr))
            if tend != -1:
                end = tend
            pos = html.find("<" + name, pos + 1)
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
        return result

    def parseDOM(self, html, name=u"", attrs={}, ret=False):
        if isinstance(html, str): # Should be handled
            html = [html]
        elif isinstance(html, unicode):
            html = [html]
        elif not isinstance(html, list):
            return u""
        if not name.strip():
            return u""
        ret_lst = []
        for item in html:
            temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
            for match in temp_item:
                item = item.replace(match, match.replace("\n", " "))
            lst = self._getDOMElements(item, name, attrs)
            if isinstance(ret, str):
                lst2 = []
                for match in lst:
                    lst2 += self._getDOMAttributes(match, name, ret)
                lst = lst2
            else:
                lst2 = []
                for match in lst:
                    temp = self._getDOMContent(item, name, match, ret).strip()
                    item = item[item.find(temp, item.find(match)) + len(temp):]
                    lst2.append(temp)
                lst = lst2
            ret_lst += lst
        return ret_lst

    def GetPlayList(self, ppid):
        purl = 'http://v.pptv.com/show/%s.html' % ppid
        data = GetHttpData(purl)
        kk = self.CheckValidList(re.compile('&kk=([^"\']*)["\'], ').findall(data))
        vid = self.CheckValidList(re.compile('"id"\s*:\s*(\d+)\s*, ').findall(data))
        PPTV_WEBPLAY_XML = 'http://web-play.pptv.com/'
        ipadurl = PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&version=4&type=m3u8.web.pad' + '&kk=' + kk
        data = GetHttpData(ipadurl)
        tmp = self.CheckValidList(self.parseDOM(unicode(data, 'utf-8', 'ignore'), 'file'))
        if len(tmp) <= 0:
            return 'ERROR', 'A'
        items = self.parseDOM(tmp, 'item', ret='rid')
        if len(items) <= 0:
            return 'ERROR', 'B'
        quality = 1
        if quality >= len(items):
            quality = len(items) - 1
        rid = items[quality]
        cur = str(quality)
        if len(rid) <= 0 or len(cur) <= 0:
            return 'ERROR', 'C'
        dt = self.CheckValidList(self.parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs={'ft': cur.encode('utf-8')}))
        if len(dt) <= 0:
            return 'ERROR', 'D'
        sh = self.CheckValidList(self.parseDOM(dt, 'sh'))
        f_key = self.CheckValidList(self.parseDOM(dt, 'key'))
        if len(sh) <= 0:
            return 'ERROR', 'F'
        rid = self.CheckValidList(re.compile('([^\.]*)\.').findall(rid))
        return 'M3U8', 'http://' + sh.encode('utf-8') + '/' + rid.encode('utf-8') + '.m3u8?type=m3u8.web.pad&k=' + f_key.encode('utf-8')


def work(purl):
    ips = purl.split(',')
    if ips[0] == 'DR_YOUKU':
        itype, iurl = YOUKU_DR().GetPlayList(ips[1])
    elif ips[0] == 'DR_SOHU':
        itype, iurl = SOHU_DR().GetPlayList(ips[1])
    elif ips[0] == 'DR_PPTV':
        itype, iurl = PPTV_DR().GetPlayList(ips[1])
    elif ips[0] == 'DR_IFENG':
        itype, iurl = IFENG_DR().GetPlayList(ips[1])
    elif ips[0] == 'DR_DENG':
        itype, iurl = DENG_DR().GetPlayList(ips[1])
    else:
        itype = 'ERROR'
        iurl = ''
    return itype, iurl

def version():
    return '20161125'
