#!/usr/bin/env python
# -*- coding: utf-8 -*-

from common import get_html
from json import loads
import time
import re
import hashlib
from urllib2 import urlopen, Request

def get_location(url, headers={}):
    response = urlopen(Request(url, headers))
    # urllib will follow redirections and it's too much code to tell urllib
    # not to do that
    return response.geturl()

def match1(text, *patterns):
    for pattern in patterns:
        try:
            match = re.search(pattern, text)
        except(TypeError):
            match = re.search(pattern, str(text))
        if match:
            return match.group(1)


def matchall(text, patterns):
    ret = []
    for pattern in patterns:
        try:
            match = re.findall(pattern, text)
        except(TypeError):
            match = re.findall(pattern, str(text))
        ret += match
    return ret

class BiliBase():
    supported_stream_profile = [u'流畅', u'高清', u'超清']
    profile_2_type = {u'超清': 'TD', u'高清': 'HD', u'流畅' :'SD'}
    headers = {'Referer': 'https://www.bilibili.com'}

    def parse_cid_playurl(self, xml):
        from xml.dom.minidom import parseString
        urls = []
        doc = parseString(xml.encode('utf-8'))
        ext = doc.getElementsByTagName('format')[0].firstChild.nodeValue
        for durl in doc.getElementsByTagName('durl'):
            u = durl.getElementsByTagName('url')[0].firstChild.nodeValue
        #    urls.append(u + '|referer=https://www.bilibili.com')
            urls.append(u)
        return urls, ext

    def video_from_vid(self, vid, **kwargs):
        level = kwargs.get('level', 0)
        self.vid = vid
        api_url = self.get_api_url(level + 1)
        html = get_html(api_url, headers=self.headers)
        code = match1(html, '<code>([^<])')
        assert not code, "can't play this video: {}".format(match1(html, 'CDATA\[([^\]]+)'))
        urls, ext = self.parse_cid_playurl(html)
        if ext == 'hdmp4':
            ext = 'mp4'

        return urls

    def video_from_url(self, url, **kwargs):
        self.url = url
        self.vid = ''
        self.vid, title = self.get_vid_title()
        assert self.vid, "can't play this video: {}".format(self.url)
        return self.video_from_vid(self.vid, **kwargs)


class BiliBan(BiliBase):
    name = u'哔哩哔哩 番剧 (Bilibili Bangumi)'

    def get_vid_title(self):
        self.url = get_location(self.url, headers=self.headers)
        html = get_html(self.url, headers=self.headers)
        title = match1(html, '<h1 title="([^"]+)', '<title>([^<]+)').strip()

        if "movie" in self.url:
            aid = match1(html, 'aid=(\d+)', 'aid=\"(\d+)')
            form = {"movie_aid" : aid}
            vid = loads(get_html("https://bangumi.bilibili.com/web_api/get_source", data=urlencode(form)))["result"]["cid"]
        else:
            eid = match1(self.url, 'anime/v/(\d+)', 'play#(\d+)', 'ep(\d+)') or match1(html, 'anime/v/(\d+)')
            Episode_info = loads(get_content('http://bangumi.bilibili.com/web_api/episode/{}.json'.format(eid)))['result']['currentEpisode']
            vid = Episode_info['danmaku']
            title = title + ' ' + Episode_info['indexTitle'] + '.  ' + Episode_info['longTitle']

        return vid, title

    def get_api_url(self, q):
        if "movie" in self.url:
            mod = "movie"
        else:
            mod = "bangumi"
        ts = str(int(time.time()))
        params_str = 'cid={}&module={}&player=1&quality={}&ts={}'.format(self.vid, mod, q, ts)
        SEC2 = '9b288147e5474dd2aa67085f716c560d'
        chksum = hashlib.md5(params_str + SEC2).hexdigest()
        bangumi_api_url = 'http://bangumi.bilibili.com/player/web_api/playurl?'
        return bangumi_api_url + params_str + '&sign=' + chksum

    def prepare_list(self):
        sid = match1(html, 'var season_id = "(\d+)";')
        j_ = get_content("http://bangumi.bilibili.com/jsonp/seasoninfo/{}.ver".format(sid))
        s_data = loads(j_)
        urls = [e['webplay_url'] for e in sorted(s_data['result']['episodes'], key=lambda e: e['index'])]
        return urls


class BiliVideo(BiliBase):
    name = u'哔哩哔哩 (Bilibili)'

    def get_vid_title(self):
        if "#page=" in self.url:
            page_index = match1(self.url, '#page=(\d+)')
            av_id = match1(self.url, '\/(av\d+)')
            self.url = 'http://www.bilibili.com/{}/index_{}.html'.format(av_id, page_index)
        if not self.vid:
            html = get_html(self.url, headers=self.headers)
            vid = match1(html, 'cid=(\d+)', 'cid=\"(\d+)')
            title = match1(html, '<h1 title="([^"]+)', '<title>([^<]+)').strip()

        return vid, title

    def get_api_url(self, q):
        SECRETKEY_MINILOADER = '1c15888dc316e05a15fdd0a02ed6584f'
        sign_this = hashlib.md5('cid={}&from=miniplay&player=1&quality={}{}'.format(self.vid, q, SECRETKEY_MINILOADER)).hexdigest()
        return 'http://interface.bilibili.com/playurl?cid={}&player=1&quality={}&from=miniplay&sign={}'.format(self.vid, q, sign_this)

    def prepare_list(self):
        html = get_html(self.url)
        video_list = matchall(html, ['<option value=\'([^\']*)\''])
        if video_list:
            return ['http://www.bilibili.com'+v for v in video_list]

site = BiliVideo()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
