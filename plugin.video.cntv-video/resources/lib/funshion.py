#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import simplejson
from common import get_html, r1


class Funshion():
    #----------------------------------------------------------------------
    def get_title_by_vid(self, vid):
        """vid->str
        Single video vid to title."""
        html = get_html('http://pv.funshion.com/v5/video/profile?id={vid}&cl=aphone&uc=5'.format(vid=vid))
        c = simplejson.loads(html)
        return c['name']

    #----------------------------------------------------------------------
    def get_title_by_id(self, single_episode_id, drama_id):
        """single_episode_id, drama_id->str
        This is for full drama.
        Get title for single drama video."""
        html = get_html('http://pm.funshion.com/v5/media/episode?id={id}&cl=aphone&uc=5'.format(id=drama_id))
        c = simplejson.loads(html)

        for i in c['episodes']:
            if i['id'] == str(single_episode_id):
                return c['name'] + ' - ' + i['name']

    #----------------------------------------------------------------------
    def drama_id_to_vid(self, episode_id):
        """int->[(int,int),...]
        id: 95785
        ->[('626464', '1'), ('626466', '2'), ('626468', '3'),...
        Drama ID to vids used in drama.

        **THIS VID IS NOT THE SAME WITH THE ONES USED IN SINGLE VIDEO!!**
        """
        html = get_html('http://pm.funshion.com/v5/media/episode?id={episode_id}&cl=aphone&uc=5'.format(episode_id=episode_id))
        c = simplejson.loads(html.encode('utf-8'))

        #{'definition': [{'name': '流畅', 'code': 'tv'}, {'name': '标清', 'code': 'dvd'}, {'name': '高清', 'code': 'hd'}], 'retmsg': 'ok', 'total': '32', 'sort': '1', 'prevues': [], 'retcode': '200', 'cid': '2', 'template': 'grid', 'episodes': [{'num': '1', 'id': '624728', 'still': None, 'name': '第1集', 'duration': '45:55'}, ], 'name': '太行山上', 'share': 'http://pm.funshion.com/v5/media/share?id=201554&num=', 'media': '201554'}

        return [(i['id'], i['num']) for i in c['episodes']]

    # Helper functions.
    #----------------------------------------------------------------------
    def select_url_from_video_api(self, html, **kwargs):
        """str(html)->str(url)

        Choose the best one.

        Used in both single and drama download.

        code definition:
        {'tv': 'liuchang',
         'dvd': 'biaoqing',
         'hd': 'gaoqing',
         'sdvd': 'chaoqing'}"""
        c = simplejson.loads(html)
        #{'retmsg': 'ok', 'retcode': '200', 'selected': 'tv', 'mp4': [{'filename': '', 'http': 'http://jobsfe.funshion.com/query/v1/mp4/7FCD71C58EBD4336DF99787A63045A8F3016EC51.json', 'filesize': '96748671', 'code': 'tv', 'name': '流畅', 'infohash': '7FCD71C58EBD4336DF99787A63045A8F3016EC51'}...], 'episode': '626464'}
        video_dic = {}
        for i in c['mp4']:
            video_dic[i['code']] = i['http']

        level = kwargs.get('level', 0)
        quality_preference_list = ['tv', 'dvd', 'hd', 'sdvd']
        quality = quality_preference_list[level]

        url = video_dic[quality]
        html = get_html(url)
        c = simplejson.loads(html)
        #'{"return":"succ","client":{"ip":"107.191.**.**","sp":"0","loc":"0"},"playlist":[{"bits":"1638400","tname":"dvd","size":"555811243","urls":["http:\\/\\/61.155.217.4:80\\/play\\/1E070CE31DAA1373B667FD23AA5397C192CA6F7F.mp4",...]}]}'
        return [i['urls'][0] for i in c['playlist']]

    #----------------------------------------------------------------------
    def video_from_id(self, vid_id_tuple, **kwargs):
        """single_episode_id, drama_id->None
        Secondary wrapper for single drama video download.
        """
        (vid, id) = vid_id_tuple
        # title = self.get_title_by_id(vid, id)
        html = get_html('http://pm.funshion.com/v5/media/play/?id={vid}&cl=aphone&uc=5'.format(vid=vid))
        url_list = self.select_url_from_video_api(html, **kwargs)

        return url_list

    #Logics for drama until helper functions
    #----------------------------------------------------------------------
    def drama_from_url(self, url, **kwargs):
        """str->None
        url = 'http://www.fun.tv/vplay/g-95785/'
        """
        id = r1(r'http://www.fun.tv/vplay/.*g-(\d+)', url)
        video_list = self.drama_id_to_vid(id)

        vid = r1(r'http://www.fun.tv/vplay/.*v-(\d+)', url)

        urls = self.video_from_id((vid, id), **kwargs)
        # id is for drama, vid not the same as the ones used in single video
        return urls

    #----------------------------------------------------------------------
    def video_from_vid(self, vid, **kwargs):
        """vid->None
        Secondary wrapper for single video download.
        """
        # title = self.get_title_by_vid(vid)
        html = get_html('http://pv.funshion.com/v5/video/play/?id={vid}&cl=aphone&uc=5'.format(vid=vid))
        url_list = self.select_url_from_video_api(html)
        return url_list

    # Logics for single video until drama
    #----------------------------------------------------------------------
    def video_from_url(self, url, **kwargs):
        """lots of stuff->None
        Main wrapper for single video download.
        """
        if re.match(r'http://www.fun.tv/vplay/.*v-(\w+)', url):
            match = re.search(r'http://www.fun.tv/vplay/.*v-(\d+)(.?)', url)
            vid = match.group(1)
            return self.video_from_vid(vid, **kwargs)

    #----------------------------------------------------------------------
    def videos_from_url(self, url, **kwargs):
        if re.match(r'http://www.fun.tv/vplay/v-(\w+)', url):
            return self.video_from_url(ur, **kwargsl)      # single video
        elif re.match(r'http://www.fun.tv/vplay/.*g-(\w+)', url):
            return self.drama_from_url(url)        # whole drama
        else:
            return
