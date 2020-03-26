#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
if sys.version[0] == '3':
    from urllib.parse import urlencode, quote_plus, parse_qsl
else:
    from urllib import urlencode, quote_plus
    from urlparse import parse_qsl
import time
from json import loads
from common import get_html, urlopen, match1, fake_headers

from ctypes import c_int
import hashlib
import random
import struct
import hmac
import base64
####################

#default stream defines
stream_code_to_id = {
    'mp5hd3': 'BD',
    'mp4hd3': 'BD',
    'mp4hd3v2': 'BD',
    'hd3'   : 'BD',
    'mp5hd2': 'TD',
    'mp4hd2': 'TD',
    'mp4hd2v2': 'TD',
    'hd2'   : 'TD',
    'mp5hd' : 'HD',
    'mp4hd' : 'HD',
    'mp4'   : 'HD',
    'flvhd' : 'SD',
    'flv'   : 'SD',
    'mp4sd' : 'SD',
    '3gphd' : 'LD'
}
id_to_container = {
    'BD' : 'flv',
    'TD' : 'flv',
    'HD' : 'mp4',
    'SD' : 'flv',
    'LD' : 'mp4'
}


def add_header(key, value):
    global fake_headers
    fake_headers[key] = value

def fetch_cna():
    url = 'https://gm.mmstat.com/yt/ykcomment.play.commentInit?cna='
    req = urlopen(url)
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
    ref_youku = 'https://v.youku.com'
    ref_tudou = 'https://video.tudou.com'

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
            ('0503', self.ref_youku, self.ckey_default),
            ('0590', self.ref_youku, self.ckey_default),
            ('0505', self.ref_tudou, self.ckey_default),
            #('0502', self.ckey_mobile),
        )

    def video_from_vid(self, vid, **kwargs):
        # Extract stream with the best quality
        info = {}
        utid = fetch_cna()
        for ccode, ref, ckey in self.params:
            add_header("referer", ref)
            if len(ccode) > 4:
               _utid = generateUtdid()
            else:
               _utid = utid
            params = {
                'vid': vid,
                'ccode': ccode,
                'utid': _utid,
                'ckey': ckey,
                'client_ip': '192.168.1.1',
                'client_ts': int(time.time()),
            }
            data = None
            while data is None:
                e1 = 0
                e2 = 0
                data = loads(get_html('https://ups.youku.com/ups/get.json?' + urlencode(params)))
                e1 = data['e']['code']
                e2 = data['data'].get('error')
                if e2:
                    e2 = e2['code']
                if e1 == 0 and e2 in (-2002, -2003):
                    from getpass import getpass
                    data = None
                    params['password'] = getpass('Input password:')
            if e1 == 0 and not e2:
                break

        assert e1 == 0, data['e']['desc']
        data = data['data']
        assert 'stream' in data, data['error']['note']

        audio_lang = 'default'
        if 'dvd' in data and 'audiolang' in data['dvd']:
            for l in data['dvd']["audiolang"]:
                if l['vid'].startswith(vid):
                    audio_lang = l['langcode']
                    break

        streams = data['stream']
        for s in streams:
            if not audio_lang == s['audio_lang']:
                continue
            t = stream_code_to_id[s['stream_type']]
            urls = []
            for u in s['segs']:
                if u['key'] != -1:
                    if 'cdn_url' in u:
                        urls.append(u['cdn_url'])
                else:
                    print("VIP video, ignore unavailable seg: {}".format(s['segs'].index(u)))
            if len(urls) == 0:
                urls = [s['m3u8_url']]
                c = 'm3u8'
            else:
                c = id_to_container[t]
            size = int(s['size'])
            info[size] = urls
        videos = sorted(info)
        level = kwargs.get('level', 0)
        level = min(level, len(videos)-1)
        urls = info[videos[level]]
        return urls

    def vid_from_url(self, url):
        add_header("Cookie", '__ysuid=%d' % time.time())

        """Extracts video ID from URL.
        """
        vid = match1(url.split('//', 1)[1],
                     '^v[^\.]?\.[^/]+/v_show/id_([a-zA-Z0-9=]+)',
                     '^player[^/]+/(?:player\.php/sid|embed)/([a-zA-Z0-9=]+)',
                     '^static.+loader\.swf\?VideoIDS=([a-zA-Z0-9=]+)',
                     '^(?:new-play|video)\.tudou\.com/v/([a-zA-Z0-9=]+)')

        if not vid:
            html = get_html(url)
            vid = match1(html, r'videoIds?[\"\']?\s*[:=]\s*[\"\']?([a-zA-Z0-9=]+)')

        vid = vid[0]
        if vid.isdigit():
            vid = base64.b64encode(b'%d' % (int(vid) * 4))
            if not isinstance(vid, str):
                vid = vid.decode()
            vid = 'X' + vid
        return vid

    def get_playlist_id_from_url(url):
        """Extracts playlist ID from URL.
        """
        return match1(url, r'youku\.com/albumlist/show\?id=([a-zA-Z0-9=]+)')

    def video_from_url(self, url, **kwargs):
        vid = self.vid_from_url(url)
        urls = self.video_from_vid(vid, **kwargs)
        return urls

site = Youku()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid

