#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from common import get_html, match1
from json import loads
import time
import re
import hashlib
if sys.version[0] == '3':
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
else:
    from urllib2 import Request, urlopen
    from urllib import urlencode

def get_location(url, headers={}):
    response = urlopen(Request(url, headers))
    # urllib will follow redirections and it's too much code to tell urllib
    # not to do that
    return response.geturl()

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

    prepareurl = {}   
    def parse_cid_playurl(self, xml):
        from xml.dom.minidom import parseString
        urls = []
        size = 0
        doc = parseString(xml.encode('utf-8'))
        qlt = doc.getElementsByTagName('quality')[0].firstChild.nodeValue
        aqlts = doc.getElementsByTagName('accept_quality')[0].firstChild.nodeValue.split(',')   
        for durl in doc.getElementsByTagName('durl'):
            urls.append('https' + durl.getElementsByTagName('url')[0].firstChild.nodeValue[4:]) 
            size += int(durl.getElementsByTagName('size')[0].firstChild.nodeValue)
        return urls, size, qlt, aqlts

    def video_from_vid(self, vid, qn=0, **kwargs):
        self.vid = vid
        if int(qn) > 80: return
        api_url = self.get_api_url(qn)

        html = get_html(api_url)
        code = match1(html, '<code>([^<])')
        assert not code, "can't play this video: {}".format(match1(html, 'CDATA\[([^\]]+)'))

        urls, size, qlt, aqlts = self.parse_cid_playurl(html)
        self.prepareurl[size] = urls

        if qn == 0:
            aqlts.remove(qlt)
            for aqlt in aqlts:
                self.video_from_vid(vid, qn=aqlt, **kwargs)

        videos = sorted(self.prepareurl)
        level = kwargs.get('level', 0)
        level = min(len(videos), level)

        return self.prepareurl[videos[level]]

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
    url = ''
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

    def get_api_url(self, qn=0):
        skey = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'
        data = urlencode([
            ('appkey', 'iVGUTjsxvpLeuDCf'),
            ('cid', self.vid),
            ('platform', 'html5'),
            ('player', 0),
            ('qn', qn)
        ])
        encrypt = hashlib.md5(data + skey).hexdigest()
        return 'https://interface.bilibili.com/v2/playurl?' + data + '&sign=' + encrypt

    def prepare_list(self):
        html = get_html(self.url)
        video_list = matchall(html, ['<option value=\'([^\']*)\''])
        if video_list:
            return ['http://www.bilibili.com'+v for v in video_list]

site = BiliVideo()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
