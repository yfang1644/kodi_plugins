#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
from urllib import urlencode
import json
import gzip
import StringIO
import re

SERVER = "https://api.rr.tv"
TOKEN = '0cd2626c822d49d5a27c4424a299dbaa'
TOKEN = 'a65cb45354614c23bf3e30ca12e043d3'
TOKEN = '8e575ee9b50643368d1c0792eb1a3f22'
#TOKEN = '1d71c7d377bc4b81b0c607b622b84b4b'
#TOKEN = "79e7dc7de5814908bc11e62972b6b819"
TOKEN = '6b6cfdd3e90843c0a0914425638db7ef'
FAKE_HEADERS = {
    "clientType": "android_RRMJ",
    "clientVersion": "3.6.2",
    "token": TOKEN,
    'deviceId': '861134030056126',
    'signature': '643c184f77372e364550e77adc0360cd',
    "Authentication": "RRTV 470164b995ea4aa5a53f9e5cbceded472:IxIYBj:LPWfRb:I9gvePR5R2N8muXD7NWPCj"
};


UserAgent = 'PUClient/3.5.5 (iPhone; iOS 10.0.1; Scale/2.00)'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

def GetHttpData(url, data=None, cookie=None, headers=None):
#    print 'url: %s, data: %s, headers: %s' % (url, data, headers)
    req = urllib2.Request(url, data)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Accept-encoding', 'gzip')
    if cookie is not None:
        req.add_header('Cookie', cookie)
    if headers is not None:
        for header in headers:
            req.add_header(header, headers[header])

    response = urllib2.urlopen(req, timeout=3)
    httpdata = response.read()
    if response.headers.get('content-encoding', None) == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    match = re.compile('encoding=(.+?)"').findall(httpdata)
    if not match:
        match = re.compile('meta charset="(.+?)"').findall(httpdata)
    if match:
        charset = match[0].lower()
        if (charset != 'utf-8') and (charset != 'utf8'):
            httpdata = unicode(httpdata, charset).encode('utf8')
#    print httpdata
    return httpdata


class RenRenMeiJu():
    """docstring for RenRenMeiJu"""

    def __init__(self):
        self.header = FAKE_HEADERS

    def get_json(self, api, data=None, pretty=False):
        headers = self.header
        html = GetHttpData(SERVER+api, data=data, headers=FAKE_HEADERS)
        s = json.loads(html)
        if pretty:
            print headers
            print json.dumps(s, sort_keys=True,
                             indent=4, separators=(',', ': '))
        return html

    def func(self, API='/v3plus', **kwargs):
        return self.get_json(API, data=urlencode(kwargs))

#x = GetTokenX()
meiju=RenRenMeiJu()
API='/v3plus/season/detail'

for x in range(13000,14000):
    html = meiju.func(API=API,seasonId=x)
    js = json.loads(html)
    if js['code'] != '0000':
        print js['msg']
        continue
    print js['data']['season']['title'], js['data']['season']['id']

