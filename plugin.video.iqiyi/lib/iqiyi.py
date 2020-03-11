#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if sys.version[0] == '3':
    from urllib.parse import urlencode
else:
    from urllib import urlencode
import hashlib
import time
from random import randrange
from json import loads
from common import get_html, r1


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
    vd_2_id = {10:'4k', 19:'4k', 5:'BD', 18:'BD', 21:'HD_H265', 2:'HD', 4:'TD', 17:'TD_H265', 96:'LD', 1:'SD', 14:'TD', '75':'LDD'}
    id_2_profile = {'4k':'4k', 'BD':'1080p','TD':'720p', 'HD':'540p', 'SD':'360p', 'LD':'210p', 'HD_H265':'540p H265', 'TD_H265':'720p H265', 'LDD': '540p'}
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
        vf = hashlib.md5(url_params.encode('utf-8')).hexdigest()
        return vf

    def getVMS1(self, tvid, vid):
        tm = int(time.time() * 1000)
        key = 'd5fb4bd9d50c4be6948c97edd7254b0e'
        host = 'http://cache.m.iqiyi.com'
        sc = hashlib.md5(str(tm) + key + vid).hexdigest()
        params = {
            'src': '76f90cbd92f94a2e925d83e8ccd22cb7',
            'sc': sc,
            't': tm
        }
        src = '/tmts/{}/{}/?{}'.format(tvid, vid, urlencode(params))
        req_url = '{}{}'.format(host, src)
        return loads(get_html(req_url))

    def getVMS2(self, tvid, vid):
        host = 'http://cache.video.iqiyi.com'
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

    def cmd5x(self, s):
        # the param src below uses salt h2l6suw16pbtikmotf0j79cej4n8uw13
        #    01010031010000000000
        #    01010031010010000000
        #    01080031010000000000
        #    01080031010010000000
        #    03020031010000000000
        #    03020031010010000000
        #    03030031010000000000
        #    03030031010010000000
        #    02020031010000000000
        #    02020031010010000000
        m = hashlib.md5()
        m.update(s + 'h2l6suw16pbtikmotf0j79cej4n8uw13')
        return m.hexdigest()

    def getdash(self, tvid, vid, bid=500):
        tm = int(time.time() * 1000)
        host = 'https://cache.video.iqiyi.com'
        params = {
            'tvid': tvid,
            'bid': bid,
            'vid': vid,
            'src': '01010031010000000000',
            'vt': 0,
            'rs': 1,
            'uid': '',
            'ori': 'pcw',
            'ps': 0,
            'tm': tm,
            'qd_v': 1,
            'k_uid': self.get_macid(),
            'pt': 0,
            'd': 0,
            's': '',
            'lid': '',
            'cf': '',
            'ct': '',
            'authKey': self.cmd5x('0{}{}'.format(tm, tvid)),
            'k_tag': 1,
            'ost': 0,
            'ppt': 0,
            'locale': 'zh_cn',
            'pck': '',
            'k_err_retries': 0,
            'ut': 0
        }
        src = '/dash?{}'.format(urlencode(params))
        vf = self.cmd5x(src)
        req_url = '{}{}&vf={}'.format(host, src, vf)
        html = get_html(req_url)
        return loads(html)

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
                try:
                    stream_id = self.vd_2_id[stream['vd']]
                except:
                    continue
                if stream_id in self.stream_types:
                    continue
                stream_profile = self.id_2_profile[stream_id]
                u = stream.get('m3u')
                if u is None:
                    u = stream.get('m3utx')
                streams.append((stream_profile, u))

            streams.sort()
            level = min(level, len(streams) - 1)
            real_urls = [streams[level][1]]
            return real_urls
            m3u8_file = kwargs.get('m3u8file')

            with open(m3u8_file, "wb") as m3u8File:
                #m3u8File.write()
                m3u8File.close()

        else:
            try:
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
            except:
                bb = (100, 200, 300, 500)
                if level >= len(bb): level = len(bb) - 1
                bid = bb[level]
                dash_data = self.getdash(tvId, videoId, bid)
                assert dash_data['code'] == 'A00000', 'can\'t play this video!!'
                url_prefix = dash_data['data']['dd']
                streams = dash_data['data']['program']['video']
                for stream in streams:
                    if 'fs' in stream:
                        _bid = stream['bid']
                        container = stream['ff']
                        fs_array = stream['fs']
                        size = stream['vsize']
                        break
                push_stream_bid(_bid, container, fs_array, size)
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
