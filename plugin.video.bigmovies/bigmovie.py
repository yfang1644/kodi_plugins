#!/usr/bin/python
# -*- coding: utf-8 -*-

from json import loads
from urllib import urlencode
from common import get_html
SERVER = "http://www.lajiaovod.com:22435/index.php"

class BigMovie(object):
    """docstring for RenRenMeiJu"""
    def __init__(self):
        pass

    def get_json(self, url, data=None):
        s = loads(get_html(url, data=data))
        return s

    def index(self):
        API = '/api/index'
        return self.get_json(SERVER + API)

    def movie_detail(self, id):
        API = '/api/movieinfo/'
        return self.get_json(SERVER + API + str(id))

    def movie_list(self, method):
        API = '/api/movielist/'
        return self.get_json(SERVER + API + method)

    def tv_list(self, method):
        API = '/api/tvplaylist/'
        return self.get_json(SERVER + API + method)

    def tv_detail(self, id):
        API = '/api/tvplayinfo/'
        return self.get_json(SERVER + API + str(id))

    def search(self, keyword):
        API = '/api/search'
        data = {"keyword": keyword}
        return self.get_json(SERVER + API, urlencode(data))
