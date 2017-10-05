#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import time
from random import randrange
from json import loads
from common import get_html, r1


class IQiyi():
    name = '爱奇艺 (Iqiyi)'

    ids = ['4k','BD', 'TD', 'HD', 'SD', 'LD']
    vd_2_id = {10: '4k', 19: '4k', 5:'BD', 18: 'BD', 14: 'HD', 21: 'HD', 2: 'HD', 4: 'TD', 17: 'TD', 96: 'LD', 1: 'SD'}
    id_2_profile = {'4k':'4k', 'BD': '1080p','TD': '720p', 'HD': '540p', 'SD': '360p', 'LD': '210p'}

    def get_macid(self):
        '''获取macid,此值是通过mac地址经过算法变换而来,对同一设备不变'''
        macid=''
        chars = 'abcdefghijklnmopqrstuvwxyz0123456789'
        size = len(chars)
        for i in range(32):
            macid += list(chars)[randrange(size)]
        return macid

    def get_vf(self, url_params):
        '''计算关键参数vf'''
        sufix=''
        for j in range(8):
            for k in range(4):
                v4 = 13 * (66 * k + 27 * j) % 35
                if ( v4 >= 10 ):
                    v8 = v4 + 88
                else:
                    v8 = v4 + 49
                sufix += chr(v8)
        url_params += sufix
        m = hashlib.md5()
        m.update(url_params.encode('utf-8'))
        vf = m.hexdigest()
        return vf

    def getVMS(self, tvid, vid):
        host = 'http://cache.video.qiyi.com'
        src = '/vps?tvid=' + tvid
        src += '&vid=' + vid
        src += '&v=0&qypid=%s_12' % tvid
        src += '&src=01012001010000000000'
        src += '&t=%d' %  (time.time() * 1000)
        src += '&k_tag=1&rs=1&k_uid=' + self.get_macid()
        req_url = host + src + '&vf=' + self.get_vf(src)
        html = get_html(req_url)
        return loads(html)

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

    def video_from_vid(self, tvId, videoId, **kwargs):
        vps_data = self.getVMS(tvId, videoId)
        if vps_data["code"] != 'A00000':  # can\'t play this video!!
            return None

        url_prefix = vps_data['data']['vp']['du']
        stream = vps_data['data']['vp']['tkl'][0]
        vs_array = stream['vs']

        level = kwargs.get('level', 0)
        level = min(level , len(vs_array)-1)

        vs = vs_array[level]
        bid = vs['bid']
        fs_array = vs['fs']
        real_urls = []
        for seg_info in fs_array:
            url = url_prefix + seg_info['l']
            json_data = loads(get_html(url))
            down_url = json_data['l']
            real_urls.append(down_url)
        return real_urls

    def video_from_url(self, url, **kwargs):
        tvId, videoId = self.vid_from_url(url)
        if tvId is not None and videoId is not None:
            return self.video_from_vid(tvId, videoId, **kwargs)


site = IQiyi()
video_from_vid = site.video_from_vid
video_from_url = site.video_from_url
