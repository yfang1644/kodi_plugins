#!/usr/bin/env python

from xml.dom.minidom import parseString
from json import loads
from common import get_html, match1, r1

class Tudou():

    def tudou_download_by_iid(self, iid, title, **kwargs):
        data = loads(get_html('http://www.tudou.com/outplay/goto/getItemSegs.action?iid=%s' % iid))
        temp = max([data[i] for i in data if 'size' in data[i][0]], key=lambda x:sum([part['size'] for part in x]))
        vids, size = [t["k"] for t in temp], sum([t["size"] for t in temp])

        urls = []
        for vid in vids:
            for i in parseString(get_html('http://ct.v2.tudou.com/f?id=%s' % vid)).getElementsByTagName('f'):
                urls.append(i.firstChild.nodeValue.strip())

        return urls

    def tudou_download_by_id(self, id, title, **kwargs):
        html = get_html('http://www.tudou.com/programs/view/%s/' % id)

        iid = r1(r'iid\s*[:=]\s*(\S+)', html)
        try:
            title = r1(r'kw\s*[:=]\s*[\'\"]([^\n]+?)\'\s*\n', html).replace("\\'", "\'")
        except AttributeError:
            title = ''
        return self.tudou_download_by_iid(iid, title, **kwargs)

    def video_from_url(self, url, **kwargs):
        # Embedded player
        id = r1(r'.tudou.com/v/([^/]+)/', url)
        if id:
            return self.tudou_download_by_id(id, title='')
    
        html = get_html(url)
        try:
            title = r1(r'\Wkw\s*[:=]\s*[\'\"]([^\n]+?)\'\s*\n', html).replace("\\'", "\'")
            assert title
            title = unescape_html(title)
        except AttributeError:
            title = match1(html, r'id=\"subtitle\"\s*title\s*=\s*\"([^\"]+)\"')
            if title is None:
                title = ''
    
        vcode = r1(r'vcode\s*[:=]\s*\'([^\']+)\'', html)
        if vcode is None:
            vcode = match1(html, r'viden\s*[:=]\s*\"([\w+/=]+)\"')
        if vcode:
            print "vcode", vcode
            from youku import Youku
            return Youku().video_from_vid(vcode, **kwargs)
    
        iid = r1(r'iid\s*[:=]\s*(\d+)', html)
        if not iid:
            return self.tudou_download_playlist(url, **kwargs)
        else:
            return self.tudou_download_by_iid(iid, title, **kwargs)

    def parse_plist(self, url):
        html = get_html(url)
        lcode = r1(r"lcode:\s*'([^']+)'", html)
        plist_info = loads(get_html('http://www.tudou.com/crp/plist.action?lcode=' + lcode))
        return ([(item['kw'], item['iid']) for item in plist_info['items']])

    def tudou_download_playlist(url, **kwargs):
        videos = self.parse_plist(url)
        for i, (title, id) in enumerate(videos):
            print('Processing %s of %s videos...' % (i + 1, len(videos)))
            self.tudou_download_by_iid(id, title, **kwargs)

site = Tudou()
video_from_url = site.video_from_url

#print video_from_url('http://video.tudou.com/v/XMzE3OTYyNjE0MA==.html?spm=a2h28.8313471.pl.dlink_1_21')
