#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import json
import re
import hashlib
import urllib2
import traceback
import logging
from urlparse import urljoin
from urllib import urlencode, quote, quote_plus
from simple_rsa import RSA, create_rsa_from_cert

from utils import fetch_url, unzip
from pcsapi import PCSApiMixin, PCSApiError

logger = logging.getLogger('baiduyun.client_api')


class ClientApiError(Exception):

    def __init__(self, obj):
        self._obj = obj

    @property
    def obj(self):
        return self._obj

    def get_errmsg(self):
        obj = self._obj
        errno = obj.get('errno') or obj.get('error_code')
        if errno == 4:
            return '密码错误'

        return obj.get('errMsg') or obj.get('error_msg') or 'unknown error'

    def __str__(self):
        obj = self._obj
        return 'API Error %s: %s' % (obj.get('errno') or obj.get('error_code'),
                                     self.get_errmsg()
                                     ) + '\n' + repr(obj)


class ApiBase:
    _pcsapi_baseUrl = 'https://pcs.baidu.com/rest/2.0/pcs/'

    def _fetch_clientapi(self, url, data=None, headers={}, need_auth=True):
        if need_auth and self._bduss:
            headers['Cookie'] = 'BDUSS=' + self._bduss
        content = fetch_url(url, data, headers)
        r = json.loads(content)
        if r.get('errno', 0) or r.get('error_code', 0):
            raise ClientApiError(r)

        return r

    def _create_pcsurl(self, path, params):
        assert self._bduss is not None
        return 'http://pcs.baidu.com/rest/2.0/pcs/%s?%s&app_id=250528&BDUSS=%s' % (  # noqa
                    path, urlencode(params), self._bduss)  # noqa

    def _fetch_pcsapi(self, path, params=None, data=None, headers={}):
        assert self._bduss is not None
        url = urljoin(self._pcsapi_baseUrl, path) + '?app_id=266719'
        if params:
            url += '&' + urlencode(params)
        headers['Cookie'] = 'BDUSS=' + self._bduss

        try:
            r = fetch_url(url, data, headers)
        except urllib2.HTTPError as e:
            try:
                error_content = e.read()
                if e.headers.get('content-encoding') == 'gzip':
                    error_content = unzip(error_content)
                eo = json.loads(error_content)

            except:
                raise e
            else:
                raise PCSApiError(eo.get('error_code'), eo.get('error_msg'))

        return json.loads(r)


class ClientAPIMixin:

    def __init__(self):
        self._rsa = None
        self.set_login_info((None,) * 4)

    def get_login_info(self):
        return self._bduss, self._uid, self._ptoken, self._stoken

    def set_login_info(self, sinfo):
        self._bduss, self._uid, self._ptoken, self._stoken = sinfo

    def set_public_key(self, n, e):
        self._rsa = RSA(n, e)

    def _get_rsa(self):
        rsa = self._rsa
        if not rsa:
            cert = self.get_cert()[0]
            rsa = create_rsa_from_cert(cert)

        return rsa

    def get_cert(self):
        url = 'http://openapi.baidu.com/sslcrypt/get_last_cert'
        r = self._fetch_clientapi(url)
        return r['cert'], r['cert_id']

    def _encrypt_password(self, passwd):
        keystr = passwd + '\x01' + time.strftime('%Y%m%d%H%M%S')
        rsa = self._get_rsa()
        return rsa.encrypt(keystr)

    def _create_sig(self, params, sign_key):
        verify_str = '&'.join(sorted(
            '%s=%s' % (k, v) for k, v in params.iteritems()
        )) + '&sign_key=' + sign_key

        return hashlib.md5(verify_str).hexdigest()

    def _create_verifycode_url(self, vcodestr):
        return 'http://passport.baidu.com/cgi-bin/genimage?' + vcodestr

    def login(self, username, password, verifycode=None, vcodestr=None):
        params = {
            'login_type': '3',
            'isphone': '0',
            'username': username,
            'cert_id': '1',
            'appid': '1',
            'crypttype': '3',
            'tpl': 'esfb'
        }
        if verifycode and vcodestr:
            params['verifycode'] = verifycode
            params['vcodestr'] = vcodestr
        params['password'] = self._encrypt_password(password)
        params['sig'] = self._create_sig(params,
                                         '3e504de3df373ce5e1080f3b9c33afba')

        r = self._fetch_clientapi(
            'http://passport.baidu.com/v2/sapi/login', params)
        self.set_login_info(map(r.__getitem__, [
                            'bduss', 'uid', 'ptoken', 'stoken']))

        return r

    def try_login(self, username, password, vcode_recognizer=None):
        vcodestr, verifycode = '', ''

        while True:
            try:
                return self.login(username, password, verifycode, vcodestr)
            except ClientApiError as e:
                r = e.obj
                errno = r.get('errno')
                if r.get('needvcode') == 1 and errno in (6, 257) \
                        and callable(vcode_recognizer):
                    vcodestr = r['vcodestr']
                    verifycode = vcode_recognizer(
                        self._create_verifycode_url(vcodestr), errno == 6)
                    if not verifycode:
                        return
                else:
                    raise

    def get_filemetas(self, remote_paths):
        if isinstance(remote_paths, basestring):
            remote_paths = [remote_paths]
        data = {
            'target': json.dumps(remote_paths),
            'dlink': '1'
        }

        return self._fetch_clientapi('http://pan.baidu.com/api/filemetas',
                                     data)

    def list_share(self, shareid, uk, fid=None, remote_dir=None,
                   page=1, num=100, order='time', desc=1):
        params = {'shareid': shareid, 'uk': uk}
        if fid:
            params[fid] = fid
        elif remote_dir:
            params['dir'] = quote_plus(remote_dir, '')
        else:
            params['root'] = 1
        if page > 1:
            params['page'] = page
        if 1 < num < 100:
            params['num'] = num
        if order != 'time':
            params['order'] = order
        if desc != 1:
            params['desc'] = desc

        url = 'http://pan.baidu.com/share/list?' + urlencode(params)

        return self._fetch_clientapi(url, need_auth=False)['list']

    def list_baidu_share_home(self, uk, remote_dir='/',
                              page=1, num=100, order='time', desc=1):
        params = {'uk': uk, 'dir': remote_dir, 'page': page}
        if 1 < num < 100:
            params['num'] = num
        if order != 'time':
            params['order'] = order
        if desc != 1:
            params['desc'] = desc

        url = 'http://pan.baidu.com/share/list?' + urlencode(params)

        return self._fetch_clientapi(url, need_auth=False)['list']

    def transfer_share(self, shareid, from_, filelist, remotepath=''):
        url = 'http://pan.baidu.com/share/transfer?from=%s&shareid=%s' % (
            from_, shareid)
        if isinstance(filelist, basestring):
            filelist = [filelist]
        data = {
            'path': remotepath,
            'filelist': '["' + '","'.join(filelist) + '"]'
        }

        return self._fetch_clientapi(url, data)

    def get_quota(self):
        url = 'http://pan.baidu.com/api/quota'
        return self._fetch_clientapi(url)

    def delete(self, path):
        url = 'http://pan.baidu.com/api/filemanager?opera=delete&bdstoken=' + \
            self._stoken
        if isinstance(path, basestring):
            path = [path]
        filelist = '["%s"]' % '","'.join(path)
        data = {'filelist': filelist}

        return self._fetch_clientapi(url, data)

    def list_dir(self, remote_dir='/', page=1, num=100, order='time', desc=1):
        params = {'dir': remote_dir, 'page': page, 'num': num, 'web': 1}
        if order != 'time':
            params['order'] = order
        if desc != 1:
            params['desc'] = desc

        url = 'http://pan.baidu.com/api/list?' + urlencode(params)

        return self._fetch_clientapi(url)['list']

    def get_filediff(self, cursor='null'):
        url = 'http://pan.baidu.com/api/filediff?cursor=%s&bdstoken=%s' % (
            cursor, self._stoken)

        return self._fetch_clientapi(url)

    def _fetch_clientapi(self, url, data=None, headers={}, need_auth=True):
        if need_auth and self._bduss:
            headers['Cookie'] = 'BDUSS=' + self._bduss
        content = fetch_url(url, data, headers)
        r = json.loads(content)
        if r.get('errno', 0) or r.get('error_code', 0):
            raise ClientApiError(r)

        return r

    def get_uk(self):
        url = 'http://pan.baidu.com/share/manage'
        content = fetch_url(url, headers={'Cookie': 'BDUSS=' + self._bduss})
        _RE = re.compile(
            r'<a class="homepagelink" href="http://pan.baidu.com/share/home\?uk=(\d+)"')  # noqa
        uk = int(_RE.search(content).group(1))

        return uk

    def get_subtitle(self, file_md5, wd, path=''):
        url = 'http://pan.baidu.com/api/resource/subtitle?hash_str=%s&format=2&hash_method=1&wd=%s&search_local=1&video_path=%s' % (  # noqa
            file_md5.upper(), quote_plus(wd), quote_plus(path))
        try:
            return self._fetch_clientapi(url)
        except:
            logger.debug(traceback.format_exc())
            return {'total_num': 0}


class YunAPIMixin:

    def get_dynamic_list(self, query_uk, start=0, limit=50, category='null'):
        params = {'start': start, 'limit': limit, 'category': category,
                  'query_uk': query_uk, 'bdstoken': self._stoken}
        url = 'http://yun.baidu.com/pcloud/feed/getdynamiclist?' + \
            urlencode(params)

        res = self._fetch_clientapi(url)

        return res['records'], res['total_count']

    def get_user_info(self, query_uk):
        url = 'http://yun.baidu.com/pcloud/friend/getuinfo?query_uk=' + \
            query_uk

        return self._fetch_clientapi(url, need_auth=False)['user_info']

    def get_follow_list(self, query_uk, start=0, limit=24):
        params = {'query_uk': query_uk, 'limit': limit, 'start': start}
        url = 'http://yun.baidu.com/pcloud/friend/getfollowlist?' + \
            urlencode(params)

        res = self._fetch_clientapi(url, need_auth=False)

        return res['follow_list'], res['total_count']

    def follow(self, follow_uk, follow_uname='null', mark_name='null',
               group_id='null'):
        data = {'appid': 123123, 'follow_uk': follow_uk, 'follow_uname':
                follow_uname, 'mark_name': mark_name, 'group_id': group_id}
        url = 'http://yun.baidu.com/pcloud/friend/addfollow?bdstoken=' + \
            self._stoken

        self._fetch_clientapi(url, data)

    def unfollow(self, follow_uk):
        data = {'appid': 123123, 'follow_uk': follow_uk}
        url = 'http://yun.baidu.com/pcloud/friend/removefollow?bdstoken=' + \
            self._stoken

        self._fetch_clientapi(url, data)

    def get_hot_user_list(self, start=0, limit=20):
        url = 'http://yun.baidu.com/pcloud/friend/gethotuserlist?start=%s&limit=%s' % (  # noqa
            start, limit)

        return self._fetch_clientapi(url, need_auth=False)['hotuser_list']


class NoteAPIMixin:

    def _get_noteapi_tick(self):
        return '&t=%d' % (1000 * time.time())

    def _get_noteapi_headers(self):
        return {'Referer': 'http://note.baidu.com/'}

    def list_note_categories(self):
        url = 'http://note.baidu.com/api/category?method=select' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(
            url, 'param=', headers=self._get_noteapi_headers())

        return res['records']

    def list_note(self, category_id=None, start=0, end=100):
        url = 'http://note.baidu.com/api/note?method=select'
        if category_id:
            url += '&category=' + category_id
        if start:
            url + '&limit=%d-%d' % (start, end)
        url += self._get_noteapi_tick()

        res = self._fetch_clientapi(
            url, 'param=', headers=self._get_noteapi_headers())

        return res['records']

    def add_note(self, content, category_id=None):
        params = {'content': quote(content, '').replace('%', '%25')}
        if category_id:
            params['category_id'] = category_id
        url = 'http://note.baidu.com/api/note?method=add' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def update_note(self, content, key):
        params = {'content': quote(content, ''), '_key': key}
        url = 'http://note.baidu.com/api/note?method=update' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def move_note(self, note_id, category_id):
        if isinstance(note_id, basestring):
            note_id = [note_id]

        params = {'records': [{'_key': key, 'category_id': category_id}
                              for key in note_id]}
        url = 'http://note.baidu.com/api/note?method=category' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def delete_note(self, keys):
        if isinstance(keys, basestring):
            keys = [keys]

        params = {'_key': keys}
        url = 'http://note.baidu.com/api/note?method=delete' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def add_category(self, title):
        params = {'title': quote(title, '')}
        url = 'http://note.baidu.com/api/category?method=add' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def modify_category(self, key, new_title):
        params = {'title': quote(new_title, ''), '_key': key}
        url = 'http://note.baidu.com/api/category?method=update' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']

    def delete_category(self, key, delete_notes=True):
        if delete_notes:
            params = {'src_cate': key}
            url = 'http://note.baidu.com/api/note?method=delete' + \
                self._get_noteapi_tick()
            self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                  headers=self._get_noteapi_headers())

        params = {'_key': key}
        url = 'http://note.baidu.com/api/category?method=delete' + \
            self._get_noteapi_tick()

        res = self._fetch_clientapi(url, 'param=' + json.dumps(params),
                                    headers=self._get_noteapi_headers())

        return res['records']


class ClientAPI(YunAPIMixin, ClientAPIMixin, NoteAPIMixin, PCSApiMixin,
                ApiBase):

    def get_thumbnail_url(self, picfile, width=160, height=None, quality=100):
        url = PCSApiMixin.get_thumbnail_url(self, picfile, width, height,
                                            quality).rpartition('&BDUSS=')[0]
        return url + '|Cookie=BDUSS=' + self._bduss


TRANSCODE_TYPES = [
    'M3U8_AUTO_720', 'M3U8_AUTO_480', 'M3U8_AUTO_360', 'M3U8_AUTO_240',
    # 'M3U8_320_240', 'M3U8_480_224', 'M3U8_480_360', 'M3U8_640_480',
    # 'M3U8_854_480',
]
