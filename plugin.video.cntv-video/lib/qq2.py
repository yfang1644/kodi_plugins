#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import simplejson
from random import random, randrange
import base64
import struct
import uuid
import os
from common import get_html, match1

PLAYER_PLATFORM = 1
PLAYER_VERSION = '3.2.18.286'


class QQ():

    name = u"腾讯视频 (QQ)"

    supported_stream_types = ['sd', 'hd', 'mp4', 'shd']
    stream_2_profile = {
        'msd':u'急速',
        'sd': u'标清',
        'flv': u'高清flv',
        'hd': u'高清',
        'mp4': u'高清mp4',
        'shd': u'超清'}
    stream_2_id = {
        'msd':'LD',
        'sd': 'SD',
        'flv': 'HD',
        'hd': 'HD',
        'mp4': 'HD',
        'shd': 'TD'}
    stream_ids = ['LD', 'SD', 'HD', 'TD']

    def __init__(self):
        self.title = ''
        self.stream_types = []
        self.streams = {}

    def qq_get_params(self, fmt_name, type_name, br, params):
    
        form = urllib.urlencode(params)
        print ('http://vv.video.qq.com/getkey?' + form)
        html = get_html('http://vv.video.qq.com/getkey?' + form)
        json = html[html.find('=')+1:-1]
        jsdata = simplejson.loads(json)
        vkey = jsdata['key']
        level = jsdata['level']
        sp = jsdata['sp']
    
        params = {
            'stdfrom': 'v1090',
            'type': type_name,
            'vkey': vkey,
            'level': level,
            'platform': PLAYER_PLATFORM,
            'br': br,
            'fmt': fmt_name,
            'sp': sp,
        }
        return params

    def get_stream_info(self, vid, profile):
        player_pid = uuid.uuid4().hex.upper()

        params = {
            'fp2p': 1,
            'pid': player_pid,
            'otype': 'json',
            'defn': profile,
            'platform': PLAYER_PLATFORM,
            'fhdswitch': 0,
            'charge': 0,
            'vid': vid,
            'defnpayver': 1,
            'encryptVer': "",
            'speed': randrange(512, 1024),
            'ran': random(),
            'appver': PLAYER_VERSION,
            # 'defaultfmt': profile,
            # 'utype': -1,
            # 'vids': vid,
            # 'ckey' : ''
        }

        form = urllib.urlencode(params)
        print ('http://vv.video.qq.com/getinfo?' + form)
        html = get_html('http://vv.video.qq.com/getinfo?' + form)
        json = html[html.find('=')+1:-1]
        jsdata = simplejson.loads(json)
        js = jsdata['vl']['vi'][0]

        videos = jsdata['fl']['fi']
        fmt_id = None
        fmt_name = None
        fmt_br = None
        for fmt in videos:
            sl = int(fmt['sl'])
            if sl:
                fmt_id = fmt['id']
                fmt_name = fmt['name']
                fmt_br = fmt['br']

        self.title = js['ti']
        filename = js['fn']
        cdn = js['ul']['ui'][0]
        cdn_url = cdn['url']
        filetype = int(cdn['dt'])
        vt = cdn['vt']

        if filetype == 1:
            type_name = 'flv'
        elif filetype == 2:
            type_name = 'mp4'
        else:
            type_name = 'unknown'

        num_clips = js['cl']['fc']

        fns = filename.split('.')
        #may have preformence issue when info_only

        items = num_clips if num_clips else 1
        urls = []

        for idx in range(1, items + 1):
            if num_clips:
                filename = '%s.%s.%d.%s' % (fns[0], fns[1], idx, fns[2])
            params = {
                'ran': random(),
                'appver': PLAYER_VERSION,
                'otype': 'json',
                'encryptVer': '',
                'platform': PLAYER_PLATFORM,
                'filename': filename,
                'vid': vid,
                'vt': vt,
                'charge': 0,
                'format': fmt_id,
                'ckey': ''
            }
            clip_url = '%s%s' % (cdn_url, filename)
            params = self.qq_get_params(fmt_name, type_name, fmt_br, params)
            form = urllib.urlencode(params)
            urls += [clip_url + '?' + form]
        return fmt_name, type_name, urls

    def video_from_vid(self, vid, **kwargs):
        for stream in self.supported_stream_types:
            fmt_name, type_name, urls = self.get_stream_info(vid, stream)
            stream_id = self.stream_2_id[fmt_name]
            stream_profile = self.stream_2_profile[fmt_name]
            if not stream_id in self.stream_types:
                self.stream_types.append(stream_id)
                self.streams[stream_id] = {
                    'container': type_name,
                    'video_profile': stream_profile,
                    'src' : urls}
        self.stream_types = sorted(self.stream_types, key=self.stream_ids.index)
        print self.streams
        level = kwargs.get('level', -1)
        if level > 0:
            level = min(len(self.stream_types)-1, level)
        type = self.stream_types[level]
        return self.streams[type]['src']
    
    def video_from_url(self, url, **kwargs):
        html = get_html(url)
        vid = match1(html, 'vid:\s*\"([^\"]+)')
        
        return self.video_from_vid(vid, **kwargs)

    def prepare_list(self):
        html = get_html(self.url)
        vids = [a.strip('"') for a in match1(html, '\"vid\":\[([^\]]+)').split(',')]
        return vids


site = QQ()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
urls = video_from_url('https://v.qq.com/x/cover/6g806tfg1d6kdzi.html')
