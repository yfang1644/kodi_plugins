#!/usr/bin/env python
# -*- coding: utf-8 -*-

from json import loads
import time
from random import random
import urlparse
import re
from common import get_html, r1

'''
Changelog:
    1. http://tv.sohu.com/upload/swf/20150604/Main.swf
        new api
'''


def set_proxy(proxy):
    proxy_handler = request.ProxyHandler({
        'http': '%s:%s' % proxy,
        'https': '%s:%s' % proxy,
    })
    opener = request.build_opener(proxy_handler)
    request.install_opener(opener)


def unset_proxy():
    proxy_handler = request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    request.install_opener(opener)


# DEPRECATED in favor of set_proxy() and unset_proxy()
def set_http_proxy(proxy):
    if proxy is None:     # Use system default setting
        proxy_support = request.ProxyHandler()
    elif proxy == '':     # Don't use any proxy
        proxy_support = request.ProxyHandler({})
    else:                 # Use proxy
        proxy_support = request.ProxyHandler({'http': '%s' % proxy, 'https': '%s' % proxy})
    opener = request.build_opener(proxy_support)
    request.install_opener(opener)


class Sohu():

    v_api1 = 'http://hot.vrs.sohu.com/vrs_flash.action?vid=%s'
    v_api2 = 'http://my.tv.sohu.com/play/videonew.do?vid=%s&referer=http://my.tv.sohu.com'

    def real_url(self, host, vid, new, clipURL, ck):
        url = 'http://'+host+'/?prot=9&prod=flash&pt=1&file='+clipURL+'&new='+new +'&key='+ck+'&vid='+str(vid)+'&uid='+str(int(time.time()*1000))+'&t='+str(random())+'&rb=1'
        try:
            return loads(get_html(url))['url']
        except:
            return ''

    def video_from_url(self, url, **kwargs):
        if re.match(r'http://share.vrs.sohu.com', url):
            vid = r1('id=(\d+)', url)
        else:
            html = get_html(url)
            vid = r1(r'\Wvid\s*[\:=]\s*[\'"]?(\d+)[\'"]?', html)
        assert vid

        return video_from_vid(self, vid, **kwargs)

    def video_from_vid(self, vid, **kwargs):
        vidlist = ['oriVid', 'superVid', 'highVid', 'norVid', 'relativeId']
        level = kwargs.get('level', 0)
        qtyp = vidlist[level]

        #if re.match(r'http://tv.sohu.com/', url):
            # if extractor_proxy:
            #     set_proxy(tuple(extractor_proxy.split(":")))
        try:
            info = loads(get_html(self.v_api1 % vid))

            if 'data' in info:
                hqvid = info['data'][qtyp]
            else:
                hqvid = info[qtyp]
            if hqvid != 0 and hqvid != vid:
                info = loads(get_html(self.v_api1 % hqvid))
            # if extractor_proxy:
            #     unset_proxy()
        except:
            info = loads(get_html(self.v_api2 % vid))

        host = info['allot']
        prot = info['prot']
        tvId = info['tvid']
        data = info['data']
        title = data['tvName']
        size = sum(map(int, data['clipsBytes']))
        urls = []
        assert len(data['clipsURL']) == len(data['clipsBytes']) == len(data['su'])
        for new, clip, ck, in zip(data['su'], data['clipsURL'], data['ck']):
            clipURL = urlparse.urlparse(clip).path
            url = self.real_url(host, vid, new, clipURL, ck)
            if url:
                urls.append(url + '|RANGE=')
            # assert data['clipsURL'][0].endswith('.mp4')

        return urls

site = Sohu()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
