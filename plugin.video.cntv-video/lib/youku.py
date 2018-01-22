#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ssl
import time
import urllib2 as request
from json import loads
from common import get_html, match1

####################
cookies = None

def fetch_cna():
    url = 'http://gm.mmstat.com/yt/ykcomment.play.commentInit?cna='
    req = request.urlopen(url)
    return req.info()['Set-Cookie'].split(';')[0].split('=')[1]


class Youku():
    name = "优酷 (Youku)"

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
        self.ccode = '0514'
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

        api_url = 'https://ups.youku.com/ups/get.json?vid={}&ccode={}&client_ip=192.168.1.1&utid={}&client_ts={}'.format(self.vid, self.ccode, fetch_cna(), int(time.time()))
        data = loads(get_html(
            api_url,
            headers={'Referer': 'http://static.youku.com/'}
            ))
        assert data['e']['code'] == 0, data['e']['desc']
        data = data['data']
        try:
            self.title = data['video']['title']
        except:
            self.title = 'XXXXXXXXXX'

        streams = data['stream']

        stream_types = dict([(i['id'], i) for i in self.stream_types])
        audio_lang = streams[0]['audio_lang']

        if self.level > 0:
            self.level = min(len(streams)-1, self.level)

        m3u8 = streams[self.level]['m3u8_url']
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
