#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import simplejson
from os.path import dirname
import urlparse
from common import get_html, match1


class MGTV():
    def vid_from_url(self, url, **kwargs):
        """Extracts video ID from URL.
        """
        vid = match1(url, 'http://www.mgtv.com/b/\d+/(\d+).html')
        if not vid:
            vid = match1(url, 'http://www.mgtv.com/hz/bdpz/\d+/(\d+).html')
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
        api_endpoint = 'http://pcweb.api.mgtv.com/player/video?video_id='
        html = get_html(api_endpoint + vid)
        content = simplejson.loads(html)
        stream = content['data']['stream']

        # title = content['data']['info']['title']
        domain = content['data']['stream_domain'][0]
        level = kwargs.get('level', 0)

        url = content['data']['stream'][level]['url']

        url = domain + re.sub(r'(\&arange\=\d+)', '', url)  # Un-Hum
        content = simplejson.loads(get_html(url))
        url = content['info']

        return url

    def video_from_url(self, url, **kwargs):
        vid = self.vid_from_url(url)
        m3u_url = self.video_from_vid(vid, **kwargs)
        return m3u_url
