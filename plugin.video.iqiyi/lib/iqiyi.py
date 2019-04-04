#!/usr/bin/python
# -*- coding: utf-8 -*-

import hashlib
import time
from random import randrange
from json import loads
from common import get_html, r1
from urllib import urlencode


class IQiyi():
    name = '爱奇艺 (Iqiyi)'
    stream_types = [
        {'id': '4k', 'container': 'm3u8', 'video_profile': '4k'},
        {'id': 'BD', 'container': 'm3u8', 'video_profile': '1080p'},
        {'id': 'TD', 'container': 'm3u8', 'video_profile': '720p'},
        {'id': 'TD_H265', 'container': 'm3u8', 'video_profile': '720p H265'},
        {'id': 'HD', 'container': 'm3u8', 'video_profile': '540p'},
        {'id': 'HD_H265', 'container': 'm3u8', 'video_profile': '540p H265'},
        {'id': 'SD', 'container': 'm3u8', 'video_profile': '360p'},
        {'id': 'LD', 'container': 'm3u8', 'video_profile': '210p'},
    ]
     
    ids = ['4k','BD', 'TD', 'HD', 'SD', 'LD']
    vd_2_id = {10: '4k', 19: '4k', 5:'BD', 18: 'BD', 14: 'HD', 21: 'HD', 2: 'HD', 4: 'TD', 17: 'TD', 96: 'LD', 1: 'SD'}
    id_2_profile = {'4k':'4k', 'BD': '1080p','TD': '720p', 'HD': '540p', 'SD': '360p', 'LD': '210p'}
    idsize= {'4k':9, 'BD': 8,'TD': 7, 'HD': 6, 'SD': 5, 'LD': 4}

    def get_macid(self):
        '''获取macid,此值是通过mac地址经过算法变换而来,对同一设备不变'''
        macid=''
        chars = 'abcdefghijklnmopqrstuvwxyz0123456789'
        size = len(chars)
        for i in xrange(32):
            macid += list(chars)[randrange(size)]
        return macid

    def get_vf(self, url_params):
        '''计算关键参数vf'''
        #sufix=''
        #for j in xrange(8):
        #    for k in xrange(4):
        #        v4 = (13 * (66 * k + 27 * j)) % 35
        #        v8 = v4 + (88 if v4 >= 10 else 49)
        #        sufix += chr(v8)
        url_params += '1j2k2k3l3l4m4m5n5n6o6o7p7p8q8q9r'
        m = hashlib.md5()
        m.update(url_params.encode('utf-8'))
        vf = m.hexdigest()
        return vf

    def getVMS1(self, tvid, vid):
        t = int(time.time() * 1000)
        src = '76f90cbd92f94a2e925d83e8ccd22cb7'
        key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
        m = hashlib.md5()
        m.update(str(t) + key + vid)
        sc = m.hexdigest()
        vmsreq = 'https://cache.m.iqiyi.com/tmts/{0}/{1}/?t={2}&sc={3}&src={4}'.format(tvid,vid,t,sc,src)
        return loads(get_html(vmsreq))

    def getVMS2(self, tvid, vid):
        host = 'https://cache.video.iqiyi.com'
        tm = int(time.time() * 1000)
        params = {
            'tvid': tvid,
            'vid': vid,
            'v': 0,
            'qypid': '{}_12'.format(tvid),
            'src': '01012001010000000000',
            't': tm,
            'k_tag': 1,
            'k_uid': self.get_macid(),
            'rs': 1,
        }
        src = '/vps?{}'.format(urlencode(params))
        req_url = host + src + '&vf=' + self.get_vf(src)
        return loads(get_html(req_url))

    def vid_from_url(self, url, **kwargs):
        link = get_html(url)
        tvId = r1(r'#curid=(.+)_', url) or \
                r1(r'tvid=([^&]+)', url) or \
                r1(r'data-player-tvid="([^"]+)"', link) or \
                r1(r'tv(?:i|I)d=(.+?)\&', link) or \
                r1(r'param\[\'tvid\'\]\s*=\s*"(.+?)"', link)
        videoId = r1(r'#curid=.+_(.*)$', url) or \
                r1(r'vid=([^&]+)', url) or \
                r1(r'data-player-videoid="([^"]+)"', link) or \
                r1(r'vid=(.+?)\&', link) or \
                r1(r'param\[\'vid\'\]\s*=\s*"(.+?)"', link)

        if tvId is not None and videoId is not None:
            return tvId, videoId

    def video_from_vid(self, tvId, videoId, **kwargs):
        level = kwargs.get('level', 0)
        m3umode = kwargs.get('m3u8')
        if m3umode is not None:
            info = self.getVMS1(tvId, videoId)
            assert info['code'] == 'A00000', 'can\'t play this video!!'

            streams = []
            for stream in info['data']['vidl']:
                stream_id = self.vd_2_id[stream['vd']]
                if stream_id in self.stream_types:
                    continue
                stream_profile = self.idsize[stream_id]
                streams.append((stream_profile, stream['m3u']))

            streams.sort()
            level = min(level, len(streams) - 1)
            real_urls = [streams[level][1]]
        else:
            info = self.getVMS2(tvId, videoId)
            assert info['code'] == 'A00000', 'can\'t play this video!!'
            
            url_prefix = info['data']['vp']['du']
            stream = info['data']['vp']['tkl'][0]
            vs_array = stream['vs']

            level = min(level , len(vs_array)-1)

            vs = vs_array[level]
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
