#!/usr/bin/env python
# encoding: utf-8
# File Name: anayl.py
# Author: Fang Yuan (yfang@nju.edu.cn)
# Created Time: Mon 06 Feb 2017 07:58:55 PM CST
#!/usr/bin/evn python
#coding=utf8
#author:[email protected]
#date:2014-12-26

import sys
import os
import time
import urllib2
import cStringIO, gzip
import lxml.html
import re
import json
import random


def createRequest(url, referer=None):
    print url
    req = urllib2.Request(
        urllib2.quote(url.split('#')[0].encode('utf8'), safe="%/:=&?~#+!$,;'@()*[]"),
        headers={"Accept":"application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5",
               "Accept-Charset":"GBK,utf-8;q=0.7,*;q=0.3",
               "Accept-Encoding":"gzip",
               "Accept-Language":"zh-CN,zh;q=0.8",
               "Cache-Control":"max-age=0",
               "Connection":"keep-alive",
               "User-Agent":"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.106 Safari/535.2",
               })
    if referer is not None:
        req.add_header('Referer', referer)
    return req


def getContent(url, referer=None):
    f = urllib2.urlopen(createRequest(url, referer), timeout=15)
    data = f.read()
    if f.headers.get('content-encoding') == 'gzip':
        data = gzip.GzipFile(fileobj=cStringIO.StringIO(data)).read()
    f.close()
    return data


def getCdnUrl(apiUrl, referer=None):
    content = getContent(apiUrl, referer)
    data = json.loads(content)
    token = data['token']
    for resource in data['fsps']:
        fspUrl = resource['url']
        if resource['clarity'] == 'super-dvd':
            fspUrl = resource['url']

    fsp = re.findall("fsp://(w+)", fspUrl)[0]
    if fsp == '':
        return None
    else:
        timestamp = int(time.time())
    cdnUrl = 'http://jobsfe.funshion.com/query/v1/mp4/{0}.json?clifz=fun&mac=&tm={1}&token={2}'.format(fsp, timestamp, token)
    return cdnUrl


def getPlayUrl(cdnUrl, referer=None):
    content = getContent(cdnUrl, referer)
    data = json.loads(content)
    if data['return'] == 'succ':
        playUrls = data['playlist'][0]['urls']
        return playUrls[random.randint(0, len(playUrls)-1)]

    return None


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1].startswith('http') is None:
        print 'Usage: python fun.py http://www.fun.tv/vplay/m-115946/'
        print 'Please input the url to be parse'
        sys.exit()

    videoUrl = sys.argv[1]
    vid = int(re.findall("vplay/m-(\d+)", videoUrl)[0])
    apiUrl = 'http://api.fun.tv/ajax/get_webplayinfo/{0}/1/mp4?user=funshion'.format(vid)
    cdnUrl = getCdnUrl(apiUrl, videoUrl)
    playUrl = getPlayUrl(cdnUrl, videoUrl)
    print playUr
