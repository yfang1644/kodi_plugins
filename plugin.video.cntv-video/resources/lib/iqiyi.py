#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import hashlib
import time
from random import random
import simplejson
from common import get_html, r1


class IQiyi():

    def getVMS(self, tvid, vid):
        t = int(time.time() * 1000)
        src = '76f90cbd92f94a2e925d83e8ccd22cb7'
        key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
        sc = hashlib.md5(str(t) + key + vid).hexdigest()
        vmsreq = 'http://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid, vid, t, sc, src)

        return simplejson.loads(get_html(vmsreq))

    def vid_from_url(self, url, **kwargs):
        link = get_html(url)
        tvId = r1(r'#curid=(.+)_', url) or \
                r1(r'tvid=([^&]+)', url) or \
                r1(r'data-player-tvid="([^"]+)"', link)
        videoId = r1(r'#curid=.+_(.*)$', url) or \
                r1(r'vid=([^&]+)', url) or \
                r1(r'data-player-videoid="([^"]+)"', link)

        if tvId is not None and videoId is not None:
            return tvId, videoId

    def video_from_url(self, url, **kwargs):
        tvId, videoId = self.vid_from_url(url)
        info = self.getVMS(tvId, videoId)
        print '-----------------', tvId, videoId, info
        if info['code'] == 'A00000':
            vs = info['data']['vidl']
            level = kwargs.get('level', 0)

            level = min(level, len(vs) - 1)

            video_links = vs[level]['m3u']
            return video_links
