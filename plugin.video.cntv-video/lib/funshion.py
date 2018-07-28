#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from json import loads
from common import get_html, r1
import base64
from urlparse import urlparse, urljoin

class KBaseMapping:
    def __init__(self, base=62):
        self.base = base
        mapping_table = [str(num) for num in range(10)]
        for i in range(26):
            mapping_table.append(chr(i + ord('a')))
        for i in range(26):
            mapping_table.append(chr(i + ord('A')))

        self.mapping_table = mapping_table[:self.base]

    def mapping(self, num):
        res = []
        while num > 0:
            res.append(self.mapping_table[num % self.base])
            num = num // self.base
        return ''.join(res[::-1])

class Funshion():
    stream_types = [
        'sdvd', 'sdvd_h265', 'hd', 'hd_h265',
        'dvd', 'dvd_h265', 'tv', 'tv_h265'
    ]
    a_mobile_url = 'http://m.fun.tv/implay/?mid=302555'
    video_ep = 'http://pv.funshion.com/v7/video/play/?id={}&cl=mweb&uc=111'
    media_ep = 'http://pm.funshion.com/v7/media/play/?id={}&cl=mweb&uc=111'
    coeff = None

    # Helper functions.
    #----------------------------------------------------------------------
    def get_coeff(self, magic_list):
        magic_set = set(magic_list)
        no_dup = []
        for item in magic_list:
            if item in magic_set:
                magic_set.remove(item)
                no_dup.append(item)
        # really necessary?

        coeff = [0, 0, 0, 0]
        for num_pair in no_dup:
            idx = int(num_pair[-1])
            val = int(num_pair[:-1], 16)
            coeff[idx] = val

        return coeff

    def search_dict(self, a_dict, target):
        for key, val in a_dict.items():
            if val == target:
                return key

    def fetch_magic(self, url):
        magic_list = []
        page = get_html(url)
        src = re.findall(r'src="(.+?)"', page)
        js = [path for path in src if path.endswith('.js')]

        host = 'http://' + urlparse(url).netloc
        js_path = [urljoin(host, rel_path) for rel_path in js]

        for p in js_path:
            if 'mtool' in p or 'mcore' in p:
                js_text = get_html(p)
                hit = re.search(r'\(\'(.+?)\',(\d+),(\d+),\'(.+?)\'\.split\(\'\|\'\),\d+,\{\}\)', js_text)

                code = hit.group(1)
                base = hit.group(2)
                size = hit.group(3)
                names = hit.group(4).split('|')

                mapping = KBaseMapping(base=int(base))
                sym_to_name = {}
                for no in range(int(size), 0, -1):
                    no_in_base = mapping.mapping(no)
                    val = names[no] if no < len(names) and names[no] else no_in_base
                    sym_to_name[no_in_base] = val

                moz_ec_name = self.search_dict(sym_to_name, 'mozEcName')
                push = self.search_dict(sym_to_name, 'push')
                patt = '{}\.{}\("(.+?)"\)'.format(moz_ec_name, push)
                ec_list = re.findall(patt, code)
                [magic_list.append(sym_to_name[ec]) for ec in ec_list]

        return magic_list

    def get_cdninfo(self, hashid):
        url = 'http://jobsfe.funshion.com/query/v1/mp4/{}.json'.format(hashid)
        meta = loads(get_html(url, decoded=False).decode('utf8'))
        return meta['playlist'][0]['urls']

    def funshion_decrypt(self, a_bytes, coeff):
        res_list = []
        pos = 0
        while pos < len(a_bytes):
            a = ord(a_bytes[pos])
            if pos == len(a_bytes) - 1:
                res_list.append(a)
                pos += 1
            else:
                b = ord(a_bytes[pos + 1])
                m = a * coeff[0] + b * coeff[2]
                n = a * coeff[1] + b * coeff[3]
                res_list.append(m & 0xff)
                res_list.append(n & 0xff)
                pos += 2
    
        return  str(bytearray(res_list))

    def funshion_decrypt_str(self, a_str, coeff):
        if len(a_str) == 28 and a_str[-1] == '0':
            data_bytes = base64.b64decode(a_str[:27] + '=')
            clear = self.funshion_decrypt(data_bytes, coeff)
            return binascii.hexlify(clear.encode('utf8')).upper()

        data_bytes = base64.b64decode(a_str[2:])
        x = self.funshion_decrypt(data_bytes, coeff)
        return self.funshion_decrypt(data_bytes, coeff)

    def checksum(self, sha1_str):
        if len(sha1_str) != 41:
            return False
        if not re.match(r'[0-9A-Za-z]{41}', sha1_str):
            return False
        sha1 = sha1_str[:-1]
        if (15 & sum([int(char, 16) for char in sha1])) == int(sha1_str[-1], 16):
            return True
        return False

    def dec_playinfo(self, info, coeff):
        res = None
        clear = self.funshion_decrypt_str(info['infohash'], coeff)
        if self.checksum(clear):
            res = dict(hashid=clear[:40], token=self.funshion_decrypt_str(info['token'], coeff))
        else:
            clear = self.funshion_decrypt_str(info['infohash_prev'], coeff)
            if self.checksum(clear):
                res = dict(hashid=clear[:40], token=self.funshion_decrypt_str(info['token_prev'], coeff))

        return res

    #----------------------------------------------------------------------
    def video_from_vid(self, vid, **kwargs):
        if self.coeff is None:
            magic_list = self.fetch_magic(self.a_mobile_url)
            self.coeff = self.get_coeff(magic_list)

        ep_url = self.video_ep if 'single_video' in kwargs else self.media_ep
        url = ep_url.format(vid)
        meta = loads(get_html(url))

        streams = meta['playlist']
        maxlevel = len(streams)
        level = kwargs.get('level', 0)
        if level >= maxlevel: level = maxlevel-1
        stream = streams[level]
        definition = stream['code']
        for s in stream['playinfo']:
            codec = 'h' + s['codec'][2:]    # h.264 -> h264
            for st in self.stream_types:
                s_id = '{}_{}'.format(definition, codec)
                if codec == 'h264':
                    s_id = definition
                if s_id == st:
                    clear_info = self.dec_playinfo(s, self.coeff)
                    cdn_list = self.get_cdninfo(clear_info['hashid'])
                    base_url = cdn_list[0]
                    token = base64.b64encode(clear_info['token'].encode('utf8'))
                    video_url = '{}?token={}&vf={}'.format(base_url, token, s['vf'])
                    return [video_url]

    # Logics for single video until drama
    #----------------------------------------------------------------------
    def video_from_url(self, url, **kwargs):
        vid = r1(r'https://www.fun.tv/vplay/v-(\w+)', url)
        if vid:
            return self.video_from_vid(vid, single_video=True, **kwargs)
        else:
            vid = r1(r'https://www.fun.tv/vplay/.*v-(\w+)', url)
            epid = r1(r'https://www.fun.tv/vplay/.*g-(\w+)', url)
            url = 'http://pm.funshion.com/v5/media/episode?id={}&cl=mweb&uc=111'.format(vid)
            html = get_html(url)
            meta = loads(html)
            if vid:
                return self.video_from_vid(vid, **kwargs)

site = Funshion()
video_from_url = site.video_from_url
