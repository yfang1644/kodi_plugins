#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import simplejson
from common import get_html, r1


HOST_URL = 'http://www.tudou.com'

class Tudou():
    def video_from_iid(self, iid, **kwargs):
        url = 'http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s'
        html = get_html(url % iid)
        data = simplejson.loads(html)

        keys = data.keys()

        for key in keys:
            if data[key][0].get('size'):
                vids = [t['k'] for t in data[key]]
                break

        urls = []
        for vid in vids:
            html = get_html('http://cnc.v2.tudou.com/f?id=%d&jp=1' % vid)
            y = re.compile('<f.+?>(http.+?)<\/f>').findall(html)
            if len(y) < 1:
                break
            y = y[0].replace('&amp;', '&')
            urls.append(y.strip())
        return urls

    def video_from_id(self, id, **kwargs):
        html = get_html('http://www.tudou.com/programs/view/%s/' % id)

        iid = r1(r'iid\s*[:=]\s*(\S+)', html)
        return self.video_from_iid(iid, **kwargs)

    def parse_plist(url):
        html = get_html(url)
        lcode = r1(r"lcode:\s*'([^']+)'", html)
        plist_info = simplejson.loads(get_html('http://www.tudou.com/crp/plist.action?lcode=' + lcode))
        return ([(item['kw'], item['iid']) for item in plist_info['items']])

    def download_playlist(self, url, **kwargs)
        videos = parse_plist(url)
        urls = []
        for i, (title, id) in enumerate(videos):
            print('Processing %s of %s videos...' % (i + 1, len(videos)))
            urls += self.video_from_iid(id)

    def video_from_url(self, url, **kwargs):
        # Embedded player
        id = r1(r'http://www.tudou.com/v/([^/]+)/', url)
        if id:
            return self.video_from_id(id, **kwargs)

        html = get_html(url)

        vcode = r1(r'vcode\s*[:=]\s*\'([^\']+)\'', html)
        if vcode is None:
            vcode = match1(html, r'viden\s*[:=]\s*\"([\w+/=]+)\"')
        if vcode:
            from youku import video_from_vid
            return video_from_vid(vcode, **kwargs)

        iid = r1(r'iid\s*[:=]\s*(\d+)', html)
        if not iid:
            return self.download_playlist(url)
        else:
            return self.video_from_iid(iid, **kwargs)

