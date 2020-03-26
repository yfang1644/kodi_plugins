#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
if sys.version[0]=='3':
    from urllib.parse import urlencode, quote_plus, parse_qsl
else:
    from urllib import urlencode, quote_plus
    from urlparse import parse_qsl
from json import loads
from common import get_html, match1

origin = [10901, 4100201] # some VIP availablePLAYER_PLATFORMS = [11, 2, 1]
PLAYER_PLATFORMS = [10901, 4100201] # some VIP availablePLAYER_PLATFORMS = [11, 2, 1]
PLAYER_VERSION = '3.2.19.333'


def qq_get_final_url(url, vid, fmt_id, filename, fvkey, platform):
    params = {
        'appver': PLAYER_VERSION,
        'otype': 'json',
        'platform': platform,
        'filename': filename,
        'vid': vid,
        'format': fmt_id,
    }

    content = get_html('http://vv.video.qq.com/getkey?' + urlencode(params))
    data = loads(match1(content, r'QZOutputJson=(.+);$'))

    vkey = data.get('key', fvkey)
    if vkey:
        url = '{}{}?vkey={}'.format(url, filename, vkey)
    else:
        url = None
    vip = data.get('msg') == 'not pay'

    return url, vip

class QQ():

    name = u"腾讯视频 (QQ)"
    vip = None

    def get_streams_info(self, vid, profile='shd'):
        for PLAYER_PLATFORM in PLAYER_PLATFORMS[:]:
            params = {
                'otype': 'json',
                'platform': PLAYER_PLATFORM,
                'vid': vid,
                'defnpayver': 1,
                'appver': PLAYER_VERSION,
                'defn': profile,
            }

            content = get_html('http://vv.video.qq.com/getinfo?' + urlencode(params))
            data = loads(match1(content, r'QZOutputJson=(.+);$'))

            if 'msg' in data:
                assert data['msg'] not in ('vid is wrong', 'vid status wrong'), 'wrong vid'
                PLAYER_PLATFORMS.remove(PLAYER_PLATFORM)
                continue

            if PLAYER_PLATFORMS and \
                    profile == 'shd' and \
                    '"name":"shd"' not in content and \
                    '"name":"fhd"' not in content:
                for infos in self.get_streams_info(vid, 'hd'):
                    yield infos
                return
            break

        assert 'msg' not in data, data['msg']
        video = data['vl']['vi'][0]
        fn = video['fn']
        td = float(video['td'])
        fvkey = video.get('fvkey')
        self.vip = video['drm']

        # Priority for range fetch.
        cdn_url_1 = cdn_url_2 = cdn_url_3 = None
        for cdn in video['ul']['ui']:
            cdn_url = cdn['url']
            if 'vip' in cdn_url:
                continue
            # 'video.dispatch.tc.qq.com' supported keep-alive link.
            if cdn_url.startswith('http://video.dispatch.tc.qq.com/'):
                cdn_url_3 = cdn_url
            # IP host.
            elif match1(cdn_url, '(^http://[0-9\.]+/)'):
                if not cdn_url_2:
                    cdn_url_2 = cdn_url
            elif not cdn_url_1:
                cdn_url_1 = cdn_url
        cdn_url = cdn_url_1 or cdn_url_2 or cdn_url_3

        _num_clips = video['cl']['fc']

        for fmt in data['fl']['fi']:
            fmt_id = fmt['id']
            size = fmt['fs']

            fns = fn.split('.')
            fmt_id_num = int(fmt_id)
            fmt_id_prefix = None
            num_clips = 0

            if fmt_id_num > 100000:
                fmt_id_prefix = 'm'
            elif fmt_id_num > 10000:
                fmt_id_prefix = 'p'
                num_clips = _num_clips or 1
            if fmt_id_prefix:
                fmt_id_name = fmt_id_prefix + str(fmt_id_num % 10000)
                if fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
                    fns[1] = fmt_id_name
                else:
                    fns.insert(1, fmt_id_name)
            elif fns[1][0] in ('p', 'm') and not fns[1].startswith('mp'):
                del fns[1]

            urls =[]

            if num_clips == 0:
                filename = '.'.join(fns)
                url, vip = qq_get_final_url(cdn_url, vid, fmt_id, filename, fvkey, PLAYER_PLATFORM)
                if vip:
                    self.vip = vip
                elif url:
                    urls.append(url)
            else:
                fns.insert(-1, '1')
                for idx in range(1, num_clips+1):
                    fns[-2] = str(idx)
                    filename = '.'.join(fns)
                    url, vip = qq_get_final_url(cdn_url, vid, fmt_id, filename, fvkey, PLAYER_PLATFORM)
                    if vip:
                        self.vip = vip
                        break
                    elif url:
                        urls.append(url)

            yield urls, size

    def video_from_vid(self, vid, **kwargs):
        global PLAYER_PLATFORMS
        PLAYER_PLATFORMS = origin[:]
        videos = {}
        for _ in range(2):
            for urls, size in self.get_streams_info(vid):
                if urls:
                    videos[size] = urls
            break

        s = sorted(videos)
        level = kwargs.get('level', -1)
        if level > len(s): level = -1
        return  videos[s[level]]

    def video_from_url(self, url, **kwargs):
        vid = match1(url, 'https?://.*/(\w+)\.html')

        if vid and match1(url, '(^https?://film\.qq\.com)'):
            url = 'https://v.qq.com/x/cover/%s.html' % vid

        if not vid or len(vid) != 11:
            html = get_html(url)
            vid = match1(html,
                         '&vid=(\w+)',
                         'vid:\s*[\"\'](\w+)',
                         'vid\s*=\s*[\"\']\s*(\w+)',
                         '"vid":"(\w+)"')
            vid = vid[0]
        return self.video_from_vid(vid, **kwargs)


site = QQ()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid
