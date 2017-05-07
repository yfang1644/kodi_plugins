#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import hashlib
import time
from random import random
import simplejson
from common import get_html


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
        tvId = re.compile('data-player-tvid="(.+?)"', re.DOTALL).findall(link)
        videoId = re.compile('data-player-videoid="(.+?)"', re.DOTALL).findall(link)
        if (len(tvId) > 0) and (len(videoId) > 0):
            return tvId[0], videoId[0]

    def video_from_url(self, url, **kwargs):
        tvId, videoId = self.vid_from_url(url)
        info = self.getVMS(tvId, videoId)
        if info['code'] == 'A00000':
            vs = info['data']['vidl']
            level = kwargs.get('level', 0)

            video_links = vs[level]['m3u']
            return video_links
