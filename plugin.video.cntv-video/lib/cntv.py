#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from json import loads
from common import get_html, r1, match1


class CNTV():
    def video_from_vid(self, vid, **kwargs):
        api = 'http://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid='
        html = get_html(api + vid)
        info = loads(html)
        title = info['title']
        video = info['video']

        alternatives = [x for x in video.keys() if 'hapters' in x]
        res = ['lowChapters',
               'chapters',
               'chapters2',
               'chapters3',
               'chapters4']

        level = kwargs.get('level', 0)
        level = min(level, len(alternatives) - 1)

        chapters = video[alternatives[level]]
        urls = [x['url'] for x in chapters]
        ext = r1(r'\.([^.]+)$', urls[0])
        assert ext in ('flv', 'mp4')
        return urls

    def vid_from_url(self, url, **kwargs):
        html = get_html(url)
        if re.match(r'http://tv\.cntv\.cn/video/(\w+)/(\w+)', url):
            id = match1(url, r'http://tv\.cntv\.cn/video/\w+/(\w+)')
        elif re.match(r'http://tv\.cctv\.com/\d+/\d+/\d+/\w+.shtml', url):
            id = r1(r'var guid = "(\w+)"', html)
        elif re.match(r'http://\w+\.cntv\.cn/(\w+/\w+/(classpage/video/)?)?\d+/\d+\.shtml', url) or \
            re.match(r'http://\w+.cntv.cn/(\w+/)*VIDE\d+.shtml', url) or \
            re.match(r'http://(\w+).cntv.cn/(\w+)/classpage/video/(\d+)/(\d+).shtml', url) or \
            re.match(r'http://\w+.cctv.com/\d+/\d+/\d+/\w+.shtml', url) or \
            re.match(r'http://\w+.cntv.cn/\d+/\d+/\d+/\w+.shtml', url):
            id = r1(r'videoCenterId","(\w+)"', html)
        elif re.match(r'http://xiyou.cntv.cn/v-[\w-]+\.html', url):
            id = r1(r'http://xiyou.cntv.cn/v-([\w-]+)\.html', url)
        else:
            return None

        return id

    def video_from_url(self, url, **kwargs):
        vid = self.vid_from_url(url)
        return self.video_from_vid(vid, **kwargs)


site = CNTV()
video_from_url = site.video_from_url
