#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import re
from json import loads
from xml.dom.minidom import parseString
from common import get_html, match1

appkey='f3bb208b3d081dc8'
SECRETKEY_MINILOADER = '1c15888dc316e05a15fdd0a02ed6584f'


class BiliVideo():
    name = u'哔哩哔哩 (Bilibili)'
    supported_stream_profile = [u'流畅', u'高清', u'超清']

    def parse_cid_playurl(self, xml):
        urls = []
        doc = parseString(xml.encode('utf-8'))
        for durl in doc.getElementsByTagName('durl'):
            urls.append(durl.getElementsByTagName('url')[0].firstChild.nodeValue)
        return urls

    #https://www.bilibili.com/video/av3851533
    def video_from_url(self, url, **kwargs):
        level = kwargs.get('level', 0)  # set default to best
        level += 1
        self.url = url
        self.vid = None
        fake_headers={'Referer': 'http://www.bilibili.com'}

        if "#page=" in self.url:
            page_index = match1(self.url, '#page=(\d+)')
            av_id = match1(self.url, '\/(av\d+)')
            self.url = 'http://www.bilibili.com/{}/index_{}.html'.format(av_id, page_index)
        if not self.vid:
            html = get_html(self.url, headers=fake_headers)
            self.vid = match1(html, 'cid=\"*(\d+)')
            title = match1(html, '<title>([^<]+)').strip(u"_完结动画_番剧_bilibili_哔哩哔哩")
            if not self.vid:
                eid = match1(self.url, 'anime/v/(\d+)') or \
                        match1(self.url, 'play#(\d+)') or \
                        match1(html, 'anime/v/(\d+)')
                if eid:
                    html = get_html('http://bangumi.bilibili.com/web_api/episode/{}.json'.format(eid))
                    Episode_info = loads(html)['result']['currentEpisode']
                    self.vid = Episode_info['danmaku']
                    self.title += ' ' + Episode_info['indexTitle'] + '.  ' + Episode_info['longTitle']

        assert self.vid, "can't play this video: {}".format(url)

        pdata = 'cid={}&from=miniplay&player=1&quality={}{}'.format(self.vid, level, SECRETKEY_MINILOADER)
        sign_this = hashlib.md5(pdata.encode('utf-8')).hexdigest()
        api_url = 'http://interface.bilibili.com/playurl?cid={}&player=1&quality={}&from=miniplay&sign={}'.format(self.vid, level, sign_this)
        html = get_html(api_url, headers=fake_headers)
        urls = self.parse_cid_playurl(html)

        return urls

site = BiliVideo()
video_from_url = site.video_from_url

print video_from_url("https://www.bilibili.com/video/av3851533")
