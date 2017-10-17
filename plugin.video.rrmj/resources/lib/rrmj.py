#!/usr/bin/python
# -*- coding: utf-8 -*-

from urllib import urlencode
from json import loads, dumps
import time
import hashlib
from common import get_html
from random import randrange

SERVER = "https://api.rr.tv"

SECRET_KEY = "clientSecret=08a30ffbc8004c9a916110683aab0060"
TOKEN = [
    '5028f46f37d2414a9c61e8e3a24a4b8b',
    '485f80c4ce6b4d65a221aedbf55a413f',
    'b5d8b8790e1145d6bdffdcb9d9286351',
    '8237122af9a24fc696f1d286e63e3784',
    '0cd2626c822d49d5a27c4424a299dbaa',
    'a65cb45354614c23bf3e30ca12e043d3',
    '8e575ee9b50643368d1c0792eb1a3f22',
    '1d71c7d377bc4b81b0c607b622b84b4b',
    '79e7dc7de5814908bc11e62972b6b819',
    '6b6cfdd3e90843c0a0914425638db7ef',
]

FAKE_HEADERS = {
    "clientType": "android_RRMJ",
    "clientVersion": "3.6.3",
    "deviceId": "861134030056129",
    "token": TOKEN[0],
    "signature": '',
    "t": '',
    "Authentication": "RRTV 470164b995ea4aa5a53f9e5cbceded472:IxIYBj:LPWfRb:I9gvePR5R2N8muXD7NWPCj"
}


def createKey():
    constantStr = "yyets"
    c = str(int(time.time())) + "416"
    return caesarEncryption(constantStr + c, 3)


def caesarEncryption(source, offset):
    dic = "abcdefghijklmnopqrstuvwxyz0123456789"
    length = len(dic)
    result = ""
    for ch in source:
        i = dic.find(ch)
        result += dic[(i + offset) % length]
    return result


class RenRenMeiJu(object):
    """docstring for RenRenMeiJu"""

    def __init__(self):
        self._header = FAKE_HEADERS
        #self.get_token()
        self._header.update(a=key_id)

    def get_json(self, api, data=None, pretty=False):
        headers = self.header
        headers.update(b=SERVER+api)
        s = loads(get_html(SERVER+api, data=data, headers=headers))
        if pretty:
            print headers
            print dumps(s, sort_keys=True,
                             indent=4, separators=(',', ': '))
        return s

    @property
    def header(self):
        self._header.update(d=str(int(time.time())) + "416")
        return self._header

    def search(self, page=1, rows=12, **kwargs):
        API = '/v3plus/video/search'
        kwargs["page"] = page
        kwargs["rows"] = rows
        return self.get_json(API, data=urlencode(kwargs))

    def get_album(self, albumId=2):
        API = '/v3plus/video/album'
        return self.get_json(API, data=urlencode(dict(albumId=albumId)))

    def index_info(self):
        API = '/v3plus/video/indexInfo'
        return self.get_json(API)

    def video_detail(self, seasonId, userId=0, **kwargs):
        API = '/v3plus/season/detail'
        kwargs["seasonId"] = seasonId
        kwargs["token"] = self._header['token']
        return self.get_json(API, data=urlencode(kwargs))

    def hot_word(self):
        API = '/v3plus/video/hotWord'
        return self.get_json(API)

    def get_token(self):
        API = '/user/platReg'
        dic = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        dic += "abcdefghijklmnopqrstuvwxyz0123456789"
        name = ''
        for x in range(0,8):
            name += dic[randrange(62)]

        MD5 = hashlib.md5()
        MD5.update(name)

        body = {
            'usid': MD5.hexdigest(),
            'platformName': 'qq',
            'nickName': name,
            'userName': name,
            'securityCode': ''
        }
        data = self.get_json(API, data=urlencode(body))
        FAKE_HEADERS['token']= data['data']['user']['token']


class RRMJResolver(RenRenMeiJu):

    def get_by_sid(self, seasonId, episodeSid, quality):
        API = "/video/findM3u8ByEpisodeSidAuth"
        url = SERVER + API
        headers = self.header
        l2 = str(int(time.time()) * 1000 - 28800000)
        headers['t'] = l2
        s7 = "episodeSid=%squality=%sclientType=%sclientVersion=%st=%s%s" % (
            episodeSid, quality, headers['clientType'],
            headers['clientVersion'], l2, SECRET_KEY)
        MD5 = hashlib.md5()
        MD5.update(s7)
        signature = MD5.hexdigest()
        headers['signature'] = signature
        post_data = 'episodeSid=%s&quality=%s&seasonId=%s&token=%s' % (
            episodeSid, quality, 0, headers['token'])
        ppp = get_html(url, data=post_data, headers=headers)
        data = loads(ppp)
        if data["code"] != "0000":
            return None, None
        else:
            m3u8 = data["data"]["m3u8"]
            current_quality = m3u8["currentQuality"]
            quality_array = m3u8["qualityArr"]
            if current_quality == "QQ":
                decoded_url = m3u8["url"].decode("base64")
                real_url = loads(decoded_url)
                print real_url
                return real_url["V"][0]["U"], current_quality
            else:
                return m3u8["url"], current_quality

    def get_play(self, seasonId, episodeSid, quality='super'):
        return self.get_by_sid(seasonId, episodeSid, quality)
