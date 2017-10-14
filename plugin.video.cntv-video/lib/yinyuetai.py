#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from json import loads
from common import get_html

def match1(text, *patterns):
    """Scans through a string for substrings matched some patterns (first-subgroups only).
    Args:
        text: A string to be scanned.
        patterns: Arbitrary number of regex patterns.
    Returns:
        When matches, returns first-subgroups from first match.
        When no matches, return None
    """

    for pattern in patterns:
        try:
            match = re.search(pattern, text)
        except(TypeError):
            match = re.search(pattern, str(text))
        if match:
            return match.group(1)

class YinYueTai():
    name = u'YinYueTai (音乐台)'
    ids = ['BD', 'TD', 'HD', 'SD' ]
    types_2_id = {'hc' :'SD', 'hd':'HD', 'he': 'TD', 'sh': 'BD'}
    types_2_profile = {'hc': '标清', 'hd': '高清', 'he': '超清','sh': '原画'}
    api = 'http://ext.yinyuetai.com/main/get-h-mv-info?json=true&videoId=%s'
    list = 'http://m.yinyuetai.com/mv/get-simple-playlist-info?playlistId=%s'

    def video_from_vid(self, vid, **kwargs):
        data = loads(get_html(self.api % vid))
        assert not data['error'], 'some error happens'

        video_data = data['videoInfo']['coreVideoInfo']

        title = video_data['videoName']
        artist = video_data['artistNames']
    
        level = kwargs.get('level', -1)
        videos = video_data['videoUrlModels']
        if level > len(videos):
            level = len(videos) - 1

        #for s in video_data['videoUrlModels']:
        #    stream_id = self.types_2_id[s['qualityLevel']]
        #    stream_profile = self.types_2_profile[s['qualityLevel']]
        #    streams = {'container': 'flv', 'video_profile': stream_profile, 'src' : [s['videoUrl']], 'size': s['fileSize']}
        return [videos[level]['videoUrl']]

        #info.stream_types = sorted(info.stream_types, key = self.ids.index)
        #return info

    def video_from_url(self, url, **kwargs):
        vid = match1(url, 'http://\w+.yinyuetai.com/video/(\d+)', 'http://\w+.yinyuetai.com/video/h5/(\d+)')
        return self.video_from_vid(vid, **kwargs)

    def videolist_from_url(self, url, **kwargs):

        list_id = match1(url, 'http://\w+.yinyuetai.com/playlist/(\d+)')
        playlist_data = loads(get_html(self.list % list_id))

        videos = playlist_data['playlistInfo']['videos']
        # TODO
        # I should directly use playlist data instead to request by vid... to be update
        return [v['playListDetail']['videoId'] for v in videos]

site = YinYueTai()
video_from_url = site.video_from_url
video_from_vid = site.video_from_vid


#u = 'http://www.yinyuetai.com/video/3054350'
#print video_from_url(u,level=1)
