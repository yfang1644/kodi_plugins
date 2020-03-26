#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import re
from json import loads
from os.path import dirname
from random import choice
if sys.version[0]=='3':
    from urllib.parse import urlsplit, quote_plus
    maketrans = bytes.maketrans
    bytearray2str = bytearray.decode
    from urllib.request import build_opener, HTTPCookieProcessor, install_opener
else:
    from urlparse import urlsplit
    from urllib import quote_plus
    from string import maketrans
    bytearray2str = str
    from urllib2 import build_opener, HTTPCookieProcessor, install_opener
from common import get_html, match1
import base64
import uuid
import time

class MGTV():
    def generate_did_tk2(self):
        did = str(uuid.uuid4())
        s = 'pno=1030|ver=0.3.0301|did={0}|clit={1}'.format(did, int(time.time()))
        if not isinstance(s, bytes):
            s = s.encode()
        e = bytearray(base64.b64encode(s).translate(maketrans(b'+/=', b'_~-')))
        e.reverse()
        return did, str(e)

    def vid_from_url(self, url, **kwargs):
        """Extracts video ID from URL.
        """
        vid = match1(url, 'https?://www.mgtv.com/b/\d+/(\d+).html')
        if vid is None:
            html = get_html(url)
            vid = match1(html, 'vid.*(\d+)')
        return vid

    def get_mgtv_real_url(self, m3u_url, **kwargs):
        """str->list of str
        Give you the real URLs."""
        split = urlparse.urlsplit(m3u_url)

        base_url = "{scheme}://{netloc}{path}/".format(scheme=split[0],
                                                       netloc=split[1],
                                                       path=dirname(split[2]))

        # get the REAL M3U url, maybe to be changed later?
        content = get_html(m3u_url)
        segment_list = []
        segments_size = 0
        for i in content.split():
            if not i.startswith('#'):  # not the best way, better we use the m3u8 package
                segment_list.append(base_url + i)
                # use ext-info for fast size calculate
            elif i.startswith('#EXT-MGTV-File-SIZE:'):
                segments_size += int(i[i.rfind(':')+1:])

        return segment_list

    def video_from_vid(self, vid, **kwargs):
        handlers = [HTTPCookieProcessor()]
        install_opener(build_opener(*handlers))
        did, tk2 = self.generate_did_tk2()
        api_info_url = 'https://pcweb.api.mgtv.com/player/video?tk2={0}&video_id={1}&type=pch5'.format(tk2, vid)
        html = get_html(api_info_url)
        content = loads(html)

        title = content['data']['info']['title']
        pm2 = content['data']['atc']['pm2']

        api_source_url = 'https://pcweb.api.mgtv.com/player/getSource?video_id={0}&pm2={1}&tk2={2}&type=pch5'.format(vid, pm2, tk2)
        html = get_html(api_source_url)
        content = loads(html)
        streams = content['data']['stream']
        domains = content['data']['stream_domain']
        domain = choice(domains)

        level = kwargs.get('level', 0)
    
        if level >= 0:
            level = min(level, len(streams)-1)
        url = streams[level]['url']

        url = domain + url
        content = loads(get_html(url))
        url = content['info']
        return [url + '|Referer="https://www.mgtv.com"']

    def video_from_url(self, url, **kwargs):
        vid = self.vid_from_url(url)
        m3u_url = self.video_from_vid(vid, **kwargs)
        return m3u_url


site = MGTV()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
