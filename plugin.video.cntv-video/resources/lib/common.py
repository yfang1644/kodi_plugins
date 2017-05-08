#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import re
import gzip
import StringIO
import socket
cookies = None

UserAgent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:43.0) Gecko/20100101 Firefox/43.0'

fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0'
}


def r1(pattern, text):
    m = re.search(pattern, text)
    if m:
        return m.group(1)


def match1(text, *patterns):
    if len(patterns) == 1:
        pattern = patterns[0]
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ret.append(match.group(1))
        return ret


def urlopen_with_retry(*args, **kwargs):
    for i in range(10):
        try:
            return urllib2.urlopen(*args, **kwargs)
        except socket.timeout:
            pass


def get_html(url, headers={}, decoded=True):
    """Gets the content of a URL via sending a HTTP GET request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """

    headers = {'User_Agent': UserAgent}
    req = urllib2.Request(url, headers=headers)
    if cookies:
        cookies.add_cookie_header(req)
        req.headers.update(req.unredirected_hdrs)

    response = urlopen_with_retry(req)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.headers.get('Content-Encoding')
    if content_encoding == 'gzip':
        httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()

    # Decode the response body
    if decoded:
        charset = match1(response.headers.get('Content-Type'), r'charset=([\w-]+)')
        if charset is not None:
            data = data.decode(charset)
        else:
            data = data.decode('utf-8', 'ignore')

    return data
