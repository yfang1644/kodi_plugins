#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ssl
import time
import urllib2 as request
from urllib import urlencode
from json import loads
from common import get_html, match1

from ctypes import c_int
import hashlib
import random
import struct
import hmac
import base64
####################
cookies = None

def fetch_cna():
    url = 'https://gm.mmstat.com/yt/ykcomment.play.commentInit?cna='
    req = request.urlopen(url)
    cookies = req.info()['Set-Cookie']
    cna = match1(cookies, "cna=([^;]+)")
    return cna if cna else "oqikEO1b7CECAbfBdNNf1PM1"

def hashCode(str):
    res = c_int(0)
    if not isinstance(str, bytes):
        str = str.encode()
    for i in bytearray(str):
        res = c_int(c_int(res.value * 0x1f).value + i)
    return res.value

def generateUtdid():
    timestamp = int(time.time()) - 60 * 60 * 8
    i31 = random.randint(0, (1 << 31) - 1)
    imei = hashCode(str(i31))
    msg = struct.pack('!2i2bi', timestamp, i31, 3, 0, imei)
    key = b'd6fc3a4a06adbde89223bvefedc24fecde188aaa9161'
    data = hmac.new(key, msg, hashlib.sha1).digest()
    msg += struct.pack('!i', hashCode(base64.standard_b64encode(data)))
    return base64.standard_b64encode(msg)

class Youku():
    name = "优酷 (Youku)"
    ckey_default = "DIl58SLFxFNndSV1GFNnMQVYkx1PP5tKe1siZu/86PR1u/Wh1Ptd+WOZsHHWxysSfAOhNJpdVWsdVJNsfJ8Sxd8WKVvNfAS8aS8fAOzYARzPyPc3JvtnPHjTdKfESTdnuTW6ZPvk2pNDh4uFzotgdMEFkzQ5wZVXl2Pf1/Y6hLK0OnCNxBj3+nb0v72gZ6b0td+WOZsHHWxysSo/0y9D2K42SaB8Y/+aD2K42SaB8Y/+ahU+WOZsHcrxysooUeND"
    ckey_mobile = "7B19C0AB12633B22E7FE81271162026020570708D6CC189E4924503C49D243A0DE6CD84A766832C2C99898FC5ED31F3709BB3CDD82C96492E721BDD381735026"

    # Last updated: 2015-11-24
    stream_types = [
        {'id': 'mp4hd3', 'alias-of' : 'hd3'},
        {'id': 'hd3',    'container': 'flv', 'video_profile': '1080P'},
        {'id': 'mp4hd2', 'alias-of' : 'hd2'},
        {'id': 'hd2',    'container': 'flv', 'video_profile': '超清'},
        {'id': 'mp4hd',  'alias-of' : 'mp4'},
        {'id': 'mp4',    'container': 'mp4', 'video_profile': '高清'},
        {'id': 'flvhd',  'container': 'flv', 'video_profile': '标清'},
        {'id': 'flv',    'container': 'flv', 'video_profile': '标清'},
        {'id': '3gphd',  'container': '3gp', 'video_profile': '标清（3GP）'},
    ]

    def __init__(self, *args):
        # Found in http://g.alicdn.com/player/ykplayer/0.5.28/youku-player.min.js
        # grep -oE '"[0-9a-zA-Z+/=]{256}"' youku-player.min.js
        self.params = (
            ('0103010102', self.ckey_mobile),
            ('0516', self.ckey_default),
            ('0517', self.ckey_default)
        )

        self.title = ''

    def video_from_vid(self, vid, **kwargs):
        self.level = kwargs.get('level', -1)
            # Extract stream with the best quality
        self.vid = vid

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))

        # Hot-plug cookie handler
        ssl_context = request.HTTPSHandler(
            context=ssl.SSLContext(ssl.PROTOCOL_TLSv1))
        cookie_handler = request.HTTPCookieProcessor()
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            proxy = parse_host(kwargs['extractor_proxy'])
            proxy_handler = request.ProxyHandler({
                'http': '%s:%s' % proxy,
                'https': '%s:%s' % proxy,
            })
        else:
            proxy_handler = request.ProxyHandler({})
        if not request._opener:
            opener = request.build_opener(proxy_handler)
            request.install_opener(opener)
        for handler in (ssl_context, cookie_handler, proxy_handler):
            request._opener.add_handler(handler)
        request._opener.addheaders = [('Cookie','__ysuid={}'.format(time.time()))]

        if self.vid is None:
            self.download_playlist_by_url(self.url, **kwargs)
            exit(0)

        for ccode, ckey in self.params:
            api_url = 'https://ups.youku.com/ups/get.json?'
            _utid = generateUtdid() if len(ccode)>4 else fetch_cna()
            params = {
                'vid': self.vid,
                'ccode': ccode,
                'utid': _utid,
                'ckey': ckey,
                'client_ip': '192.168.1.1',
                'client_ts': int(time.time()),
            }
            
            data = loads(get_html(
                api_url + urlencode(params),
                headers={'Referer': 'https://v.youku.com'}
                ))

            if data['e']['code'] == 0 and 'stream' in data['data']:
                break

        data = data['data']
        self.title = data['video'].get('title')

        streams = data['stream']

        stream_types = dict([(i['id'], i) for i in self.stream_types])
        audio_lang = streams[0]['audio_lang']

        if self.level > 0:
            self.level = min(len(streams)-1, self.level)

        m3u8 = streams[self.level].get('m3u8_url')
        return [m3u8]
        # m3u8_url is complete, but mp4 not
        urls = []
        for s in streams[self.level].get('segs', ''):
            u = s.get('cdn_url')
            if u:
                urls += [u]
            else:
                break
        return urls

    def vid_from_url(self, url):
        """Extracts video ID from URL.
        """
        return match1(url, r'youku\.com/v_show/id_([a-zA-Z0-9=]+)') or \
          match1(url, r'player\.youku\.com/player\.php/sid/([a-zA-Z0-9=]+)/v\.swf') or \
          match1(url, r'loader\.swf\?VideoIDS=([a-zA-Z0-9=]+)') or \
          match1(url, r'player\.youku\.com/embed/([a-zA-Z0-9=]+)')

    def get_playlist_id_from_url(url):
        """Extracts playlist ID from URL.
        """
        return match1(url, r'youku\.com/albumlist/show\?id=([a-zA-Z0-9=]+)')

    def video_from_url(self, url, **kwargs):
        vid = self.vid_from_url(url)
        urls = self.video_from_vid(vid, **kwargs)
        return urls

    def video_title(self):
        if self.title is not None:
            return self.title
        else:
            return 'XXXXXXXXXX'

site = Youku()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
video_title = site.video_title
