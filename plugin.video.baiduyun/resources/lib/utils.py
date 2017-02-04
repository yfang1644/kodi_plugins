#!/usr/bin/python
# -*- coding: utf-8 -*-
import gzip
import urllib2
from urllib import urlencode, quote_plus
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO  # noqa


http_proxy = None


def fetch_url(url, data=None, headers={}, timeout=None, proxies=None):
    headers.setdefault(
        'User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.84 Safari/537.22')  # noqa
    headers.setdefault('Accept-Encoding', 'gzip,deflate')

    if data and isinstance(data, dict):
        data = urlencode(data)

    req = urllib2.Request(url, data, headers)

    if proxies or http_proxy:
        if not proxies:
            if isinstance(http_proxy, basestring):
                proxies = {'http': http_proxy, 'https': http_proxy}
            else:
                proxies = http_proxy
        proxy_handler = urllib2.ProxyHandler(proxies)
        opener = urllib2.build_opener(proxy_handler)
        r = opener.open(req, timeout=timeout)
    else:
        r = urllib2.urlopen(req, timeout=timeout)

    content = r.read()

    if r.headers.get('content-encoding') == 'gzip':
        content = gzip.GzipFile(fileobj=StringIO(
            content), mode='rb').read()

    return content


def create_baidu_url(url):
    return ('plugin://script.module.hdpparser?parser=baiduyun&uri=' +
            quote_plus(url))


def unzip(content):
    return gzip.GzipFile(fileobj=StringIO(
        content), mode='rb').read()
