#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import simplejson
from common import get_html


class QQ():

    def video_from_vid(self, vid, **kwargs):
        info_api = 'http://h5vv.video.qq.com/getinfo?vid=%s'
        info_api += '&defnpayver=1&appVer=3.0.52'
        info_api += '&defaultfmt=auto&defn=%s'
        info_api += '&otype=json&show1080p=1&isHLS=0&charge=0'
        info_api += '&sdtfrom=v1001&host=v.qq.com'
        platform = '&platform=11'
        RESOLUTION = ['sd', 'hd', 'shd', 'fhd']

        level = kwargs.get('level', 0)

        jspage = get_html(info_api % (vid, RESOLUTION[level]) + platform)
        jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
        jsdata = simplejson.loads(jspage)

        if jsdata['exem'] < 0:   # try again
            platform = '&platform=10901'
            jspage = get_html(info_api % (vid, RESOLUTION[level]) + platform)
            jspage = jspage[jspage.find('=')+1:-1]   # remove heading and tail
            jsdata = simplejson.loads(jspage)

        types = jsdata['fl']['fi']
        level = min(level, len(types) - 1)
        typeid = types[level]['id']    # typeid: 10203 (int)
        format_sl = types[level]['sl']   # sl
        js = jsdata['vl']['vi'][0]
        fvkey = js['fvkey']

        title = js['ti']               # title in chinese
        filename = js['fn']           # filename 't0019fi7ura.p203.mp4'
        fc = js['cl']['fc']          # file counter
        preurl = js['ul']['ui']

        server = preurl[0]['url']
        urls = []
        root = 'http://h5vv.video.qq.com/getkey?otype=json&sdtfrom=v1001&host=v.qq.com&vid=' + vid + platform
        lenfc = fc + 1
        if fc == 0:
            lenfc = 2
        for i in range(1, lenfc):
            file = filename.split('.')
            if fc != 0:
                file.insert(2, str(i))
                file[1] = 'p' + str(typeid % 10000)
            file = '.'.join(file)
            url = root + '&format=%d&filename=%s' % (typeid, file)
            html = get_html(url)
            jspage = html[html.find('=')+1:-1]   # remove heading and tail
            jspage = simplejson.loads(jspage)
            key = jspage.get('key', fvkey)
            app = '?vkey=%s&type=mp4' % key
            urls.append(server + file + app)

        return urls

    def video_from_url(self, url, **kwargs):
        http = get_html(url)
        http = re.sub('\r|\n|\t', '', http)
        vid = re.compile('var VIDEO_INFO.+?vid:(.+?),').findall(http)
        vid = re.sub(' ', '', vid[0])
        vid = vid.strip('"')

        return self.video_from_vid(vid, **kwargs)
