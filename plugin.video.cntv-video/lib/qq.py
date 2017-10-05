#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlencode
from json import loads
from random import random, randrange
import uuid
from common import get_html, match1

PLAYER_PLATFORM = 1          # default
PLAYER_PLATFORM = 10901      # some VIP available but slow
PLAYER_PLATFORM = 11         # ok, but limited
PLAYER_VERSION = '3.2.18.286'


class QQ():

    name = u"腾讯视频 (QQ)"

    supported_stream_types = ['sd', 'hd', 'mp4', 'shd', 'fhd']
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
        self.fvkey = None
        self.stream_types = None

    def qq_get_params(self, fmt_name, type_name, br, params):

        form = urlencode(params)
        html = get_html('http://vv.video.qq.com/getkey?' + form)
        json = html[html.find('=')+1:-1]
        jsdata = loads(json)
        vkey = jsdata.get('key', self.fvkey)
        level = jsdata.get('level', '')
        sp = jsdata.get('sp', '')
    
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

    def video_from_vid(self, vid, **kwargs):
        level = kwargs.get('level', -1)

        player_pid = uuid.uuid4().hex.upper()
        profile = 'sd'
        for x in range(2):
            params = {
                'fp2p': 1,
                'pid': player_pid,
                'otype': 'json',
                'defn': profile,
                'show1080p': 1,
                'isHLS': 0,
                'platform': PLAYER_PLATFORM,
                'fhdswitch': 0,
                'charge': 0,
                'vid': vid,
                'defnpayver': 1,
                'encryptVer': '',
                'speed': randrange(512, 1024),
                'ran': random(),
                'appver': PLAYER_VERSION,
                'defaultfmt': profile,
                'utype': -1,
                'vids': vid,
                'ckey' : ''
            }

            form = urlencode(params)
            html = get_html('http://vv.video.qq.com/getinfo?' + form)
            json = html[html.find('=')+1:-1]
            jsdata = loads(json)
            js = jsdata['vl']['vi'][0]

            videos = jsdata['fl']['fi']
            self.stream_types = [x['name'] for x in videos]
            if level >= 0:
                level = min(len(self.stream_types) -1 , level)

            profile = videos[level]['name']

        fmt_id = videos[level]['id']
        fmt_name = videos[level]['name']
        fmt_br = videos[level]['br']

        self.title = js['ti']
        self.fvkey = js.get('fvkey') 
        filename = js['fn']
        cdn = js['ul']['ui']
        index = randrange(len(cdn))
        cdn = cdn[index]
        cdn_url = cdn['url']
        filetype = int(cdn['dt'])
        vt = cdn['vt']

        if filetype == 1:
            type_name = 'flv'
        elif filetype == 2:
            type_name = 'mp4'
        else:
            type_name = 'unknown'

        #may have preformence issue when info_only
        num_clips = js['cl']['fc']
        items = num_clips if num_clips else 1

        correctfn = js['cl']['ci'][0]['keyid']   # some format id mismatched
        correctid = correctfn.split('.')[1]
        fmt_id = correctid
        urls =[]

        fns = filename.split('.')
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
            params = self.qq_get_params(fmt_name, type_name, fmt_br, params)
            form = urlencode(params)
            urls += [cdn_url + filename + '?' + form]

        return urls

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
#urls = video_from_url('https://v.qq.com/x/cover/z95vg0q79gz2cde.html')
