#!/usr/bin/env python

from common import get_html, r1, match1
from json import loads
import re
import base64
import time

def rc4(key, data):
    c = list(range(256))
    g = 0
    for j in range(256):
        g = (g + c[j] + ord(key[j % len(key)])) & 0xff
        c[j], c[g] = c[g], c[j]

    g = j = 0
    f = ''
    for m in range(len(data)):
        j = (j + 1) & 0xff
        g = (g + c[j]) & 0xff
        c[j], c[g] = c[g], c[j]

        t = data[m] if isinstance(data[m], int) else ord(data[m])
        f += chr(t ^ c[(c[j] + c[g]) & 0xff])
    return f


class ACfun():
    def get_srt_json(self, id):
        url = 'http://danmu.aixifan.com/V2/%s' % id
        return get_html(url)

    def youku_acfun_proxy(self, vid, sign, ref):
        endpoint = 'http://player.acfun.cn/flash_data?vid={}&ct=85&ev=3&sign={}&time={}'
        url = endpoint.format(vid, sign, str(int(time.time() * 1000)))
        json_data = loads(get_html(url, headers=dict(referer=ref)))['data']
        enc_text = base64.b64decode(json_data)
        dec_text = rc4(b'8bdc7e1a', enc_text).decode('utf8')
        youku_json = loads(dec_text)

        yk_streams = {}
        for stream in youku_json['stream']:
            tp = stream['stream_type']
            yk_streams[tp] = [], stream['total_size']
            if stream.get('segs'):
                for seg in stream['segs']:
                    yk_streams[tp][0].append(seg['url'])
            else:
                yk_streams[tp] = stream['m3u8'], stream['total_size']

        return yk_streams

    def video_from_vid(self, vid, **kwargs):
        """str, str, str, bool, bool ->None
    
        Download Acfun video by vid.
    
        Call Acfun API, decide which site to use, and pass the job to its
        extractor.
        """
    
        #first call the main parasing API
        info = loads(get_html('http://www.acfun.tv/video/getVideo.aspx?id=' + vid))
    
        sourceType = info['sourceType']
    
        #decide sourceId to know which extractor to use
        sourceId = info.get('sourceId', '')
        # danmakuId = info['danmakuId']
    
        #call extractor decided by sourceId
        if sourceType == 'sina':
            sina_download_by_vid(sourceId)
        elif sourceType == 'youku':
            youku_download_by_vid(sourceId, **kwargs)
        elif sourceType == 'tudou':
            tudou_download_by_iid(sourceId)
        elif sourceType == 'qq':
            qq_download_by_vid(sourceId)
        elif sourceType == 'letv':
            letvcloud_download_by_vu(sourceId, '2d8c027396')
        elif sourceType == 'zhuzhan':
            #As in Jul.28.2016, Acfun is using embsig to anti hotlink so we need to pass this
    #In Mar. 2017 there is a dedicated ``acfun_proxy'' in youku cloud player
    #old code removed
            url = 'http://www.acfun.cn/v/ac' + vid
            yk_streams = self.youku_acfun_proxy(info['sourceId'], info['encode'], url)
            seq = ['mp4hd3', 'mp4hd2', 'mp4hd', 'flvhd', 'm3u8_flv']
            for t in seq:
                if yk_streams.get(t):
                    preferred = yk_streams[t]
                    break
    
            return preferred[0]
        else:
            raise NotImplementedError(sourceType)
    
    
    def video_from_url(self, url, **kwargs):
        assert re.match(r'http://[^\.]*\.*acfun\.[^\.]+/\D/\D\D(\d+)', url)
        html = get_html(url)
    
        title = r1(r'data-title="([^"]+)"', html)
        assert title
        if match1(url, r'_(\d+)$'): # current P
            title = title + " " + r1(r'active">([^<]*)', html)
    
        vid = r1('data-vid="(\d+)"', html)
        up = r1('data-name="([^"]+)"', html)
        p_title = r1('active">([^<]+)', html)
        title = '%s (%s)' % (title, up)
        if p_title:
            title = '%s - %s' % (title, p_title)
        return self.video_from_vid(vid, **kwargs)

site = ACfun()
video_from_url = site.video_from_url
