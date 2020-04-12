#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
if sys.version[0]=='3':
    from urllib.request import Request, urlopen
else:
    from urllib2 import Request, urlopen
from io import BytesIO
import re
import gzip
import zlib
import socket
cookies = None

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent_IE = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'
UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'
}


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def match1(text, *patterns):
    if len(patterns) == 1:
        pattern = patterns[0]
        return r1(pattern, text)
    else:
        ret = []
        for pattern in patterns:
            ret.append(r1(pattern, text))
        return ret


def urlopen_with_retry(*args, **kwargs):
    for i in range(10):
        try:
            return urlopen(*args, **kwargs)
        except socket.timeout:
            pass


def get_html(url,
             data=None,
             headers=fake_headers,
             decoded=True):
    """Gets the content of a URL via sending a HTTP GET request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """

    req = Request(url, data)
    req.add_header('User-Agent', UserAgent)
    if cookies:
        cookies.add_cookie_header(req)
        req.headers.update(req.unredirected_hdrs)

    for item in headers:
        req.add_header(item, headers[item])

    response = urlopen_with_retry(req)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.headers.get('Content-Encoding')
    if content_encoding == 'gzip':
        t = bytearray(data)
        if t[-1] == 10:    # b'\n'
            data = data[:-1]
        buffer = BytesIO(data)
        f = gzip.GzipFile(fileobj=buffer)
        data = f.read()
    elif content_encoding == 'deflate':
        data = zlib.decompressobj(-zlib.MAX_WBITS).decompress(data)

    # Decode the response body
    if decoded:
        match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(str(data))
        if match:
            charset = match[0]
            data = data.decode(charset)
        else:
            data = data.decode('utf-8', 'ignore')

    return data


def updateTime():
    import time, os
    req = Request('http://time.pptv.com')
    resp = urlopen(req)
    data = resp.read()
    timefmt = time.localtime(float(data))

    settime = time.strftime('%Y%m%d%2H%2M.%S', timefmt)
    os.system('date -s' + settime)

#updateTime()
