#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import json
import shutil
import hashlib
import binascii
import gzip
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import urllib2
from urllib import urlencode
from urlparse import urljoin

from utils import fetch_url


_opener_registered = False


def ensure_poster():
    global _opener_registered
    if not _opener_registered:
        from poster.streaminghttp import register_openers
        register_openers()
        _opener_registered = True


def md5_checksum(filepath, start=0, length=0):
    with open(filepath, 'rb') as fp:
        m = hashlib.md5()
        if start:
            fp.seek(start)

        bytes_read = 0
        while True:
            data = fp.read(8192)

            if not data:
                break

            if length > 0:
                bytes_read += len(data)
                if bytes_read >= length:
                    if bytes_read > length:
                        data = data[:length - bytes_read]
                    m.update(data)
                    break

            m.update(data)

        return m.hexdigest()


def crc32_checksum(filepath, start=0, length=0):
    crc = 0

    with open(filepath, 'rb') as fp:
        if start:
            fp.seek(start)

        bytes_read = 0
        while True:
            data = fp.read(8192)

            if not data:
                break

            if length > 0:
                bytes_read += len(data)
                if bytes_read >= length:
                    if bytes_read > length:
                        data = data[:length - bytes_read]
                    crc = binascii.crc32(data, crc)
                    break

            crc = binascii.crc32(data, crc)

    return crc & 0xFFFFFFFF


class PCSApiError(Exception):

    def __init__(self, error_code, error_msg):
        self._error_code = error_code
        self._error_msg = error_msg

    def __str__(self):
        return 'PCS API Error %s: %s' % (self._error_code, self._error_msg)


class ApiBase:
    _pcsapi_baseUrl = 'https://pcs.baidu.com/rest/2.0/pcs/'

    def _create_pcsurl(self, path, params):
        return '%s?%s&access_token=%s' % \
            (self._pcsapi_baseUrl + path, urlencode(
                params), self._access_token)

    def _fetch_pcsapi(self, path, params=None, data=None, headers={}):
        url = urljoin(self._pcsapi_baseUrl, path) + '?'
        if params:
            url += urlencode(params) + '&'
        url += 'access_token=' + self._access_token

        try:
            r = fetch_url(url, data, headers)
        except urllib2.HTTPError as e:
            try:
                error_content = e.read()
                if e.headers.get('content-encoding') == 'gzip':
                    error_content = gzip.GzipFile(fileobj=StringIO(
                        error_content), mode='rb').read()
                eo = json.loads(error_content)

            except:
                raise e
            else:
                raise PCSApiError(eo.get('error_code'), eo.get('error_msg'))

        return json.loads(r)
        # handle json and return , and error msg thrown


class PCSApiMixin():

    def __init__(self, access_token):
        self._access_token = access_token

    def get_quota(self):
        return self._fetch_pcsapi('quota', {'method': 'info'})

    def upload_file(self, localfile, remotepath, newfile=None, overwrite=None,
                    tmpfile=False):
        from poster.encode import multipart_encode

        params = {'method': 'upload', 'path':
                  os.path.join(remotepath,
                               newfile or os.path.basename(localfile))}
        if tmpfile:
            params['type'] = 'tmpfile'
        elif overwrite is not None:
            params['ondup'] = overwrite and 'overwrite' or 'newcopy'

        ensure_poster()
        datagen, headers = multipart_encode({"file": open(localfile, "rb")})

        return self._fetch_pcsapi('file', params, datagen, headers)

    def create_super_file(self, remotepath, filename, md5list, overwrite=None):
        params = {'method': 'createsuperfile',
                  'path': os.path.join(remotepath, filename)}
        if overwrite is not None:
            params['ondup'] = overwrite and 'overwrite' or 'newcopy'
        data = {'param': json.dumps({'block_list': md5list})}

        return self._fetch_pcsapi('file', params, data)

    def get_download_url(self, remotefile):
        return self._create_pcsurl(
            'file', {'method': 'download', 'path': remotefile})

    def download(self, remotefile, localpath=None, newfile=None):
        url = self.get_download_url(remotefile)
        if localpath:
            localfile = os.path.join(localpath,
                                     newfile or os.path.basename(remotefile))
            with open(localfile, 'wb') as fp:
                r = urllib2.urlopen(url)
                shutil.copyfileobj(r, fp)
            # or urllib retrieve
            return True

        else:
            return fetch_url(url)

    def mkdir(self, remotepath):
        return self._fetch_pcsapi(
            'file', {'method': 'mkdir', 'path': remotepath})

    def get_meta(self, remotepath):
        return self._fetch_pcsapi(
            'file', {'method': 'meta', 'path': remotepath})

    def get_batch_meta(self, paths):
        params = {'method': 'meta'}
        data = {'param': json.dumps({'list': [{'path': p} for p in paths]})}
        return self._fetch_pcsapi('file', params, data)

    def list(self, remotepath, by=None, asc=None, start=0, end=0):
        params = {'method': 'list', 'path': remotepath}
        if by is not None:
            params['by'] = by
        if asc is not None:
            params['order'] = asc and 'asc' or 'desc'
        if end > start:
            params['limit'] = '%d-%d' % (start, end)

        return self._fetch_pcsapi('file', params)

    def move(self, from_, to):
        data = {'from': from_, 'to': to}
        return self._fetch_pcsapi('file', {'method': 'move'}, data)

    def batch_move(self, *args):
        assert len(args) > 0
        data = {'param': json.dumps({'list': [{
                                    'from': f, 'to': t} for f, t in args]})}
        return self._fetch_pcsapi('file', {'method': 'move'}, data)

    def copy(self, from_, to):
        data = {'from': from_, 'to': to}
        return self._fetch_pcsapi('file', {'method': 'copy'}, data)

    def batch_copy(self, *args):
        assert len(args) > 0
        data = {'param': json.dumps({'list': [{
                                    'from': f, 'to': t} for f, t in args]})}
        return self._fetch_pcsapi('file', {'method': 'copy'}, data)

    def delete(self, path):
        data = {'path': path}
        return self._fetch_pcsapi('file', {'method': 'delete'}, data)

    def batch_delete(self, *args):
        nargs = len(args)
        assert nargs > 0
        if nargs == 1 and isinstance(args[0], (tuple, list)):
            paths = args[0]
        else:
            paths = args
        data = {'param': json.dumps({'list': [{'path': p} for p in paths]})}
        return self._fetch_pcsapi('file', {'method': 'delete'}, data)

    def search(self, path, keyword, recursive=False):
        params = {'method': 'search', 'path': path, 'wd': keyword}
        if recursive:
            params['re'] = 1
        return self._fetch_pcsapi('file', params)

    def get_thumbnail_url(self, picfile, width=160, height=None, quality=100):
        params = {'method': 'generate', 'path': picfile,
                  'width': width, 'height': height or width}
        if 0 < quality < 100:
            params['quality'] = quality
        return self._create_pcsurl('thumbnail', params)

    def diff(self, cursor='null'):
        params = {'method': 'diff', 'cursor': cursor}
        return self._fetch_pcsapi('file', params)

    def get_transcode_url(self, videofile, trans_type='M3U8_AUTO_720'):
        '''
            M3U8_320_240、M3U8_480_224、M3U8_480_360、M3U8_640_480、M3U8_854_480
            M3U8_AUTO_360、M3U8_AUTO_240、M3U8_AUTO_480、M3U8_AUTO_720
        '''
        params = {'method': 'streaming', 'path': videofile, 'type': trans_type}
        return self._create_pcsurl('file', params)

    def get_stream_file_list(self, stream_type='video', start=0, limit=1000,
                             filter_path=None):
        assert stream_type in ('video', 'audio', 'image', 'doc')

        params = {'method': 'list', 'type': stream_type}
        if start > 0:
            params['start'] = start
        if 0 < limit < 1000:
            params['limit'] = limit
        if filter_path:
            params['filter_path'] = filter_path
        return self._fetch_pcsapi('stream', params)

    def get_stream_url(self, remotefile):
        return self._create_pcsurl(
            'stream', {'method': 'download', 'path': remotefile})

    def _rapid_upload(self, fullpath, content_length, content_md5, slice_md5,
                      content_crc32, overwrite=None):
        params = {
            'method': 'rapidupload',
            'path': fullpath,
            'content-length': content_length,
            'content-md5': content_md5,
            'slice-md5': slice_md5,
            'content-crc32': content_crc32
        }
        if overwrite is not None:
            params['ondup'] = overwrite and 'overwrite' or 'newcopy'

        return self._fetch_pcsapi('file', params, '')

    def rapid_upload(self, localfile, path, newfile=None, overwrite=None):
        fullpath = os.path.join(path, newfile or os.path.basename(localfile))
        content_length = os.path.getsize(localfile)
        assert content_length > 256 * 1024

        content_md5 = md5_checksum(localfile)
        slice_md5 = md5_checksum(localfile, 0, 256 * 1024)
        content_crc32 = crc32_checksum(localfile)

        return self._rapid_upload(fullpath, content_length, content_md5,
                                  slice_md5, content_crc32, overwrite)

    def cloud_download(self, source_url, save_path, expires=None,
                       rate_limit=None, timeout=None, callback=None):
        params = {
            'method': 'add_task',
            'source_url': source_url,
            'save_path': save_path
        }

        if expires:
            params['expires'] = expires
        if rate_limit:
            params['rate_limit'] = rate_limit
        if timeout:
            params['timeout'] = timeout
        if callback:
            params['callback'] = callback

        return self._fetch_pcsapi('services/cloud_dl', params, '')

    def query_task(self, task_ids, op_type=1, expires=None):
        if not isinstance(task_ids, basestring):
            task_ids = ','.join(id for id in task_ids)

        params = {
            'method': 'query_task',
            'task_ids': task_ids,
            'op_type': op_type
        }

        if expires:
            params['expires'] = expires

        return self._fetch_pcsapi('services/cloud_dl', params, '')

    def list_task(self, expires=None, start=0, limit=10, asc=False,
                  source_url=None, save_path=None, create_time=None,
                  status=None, need_task_info=True):

        params = {
            'method': 'list_task',
        }

        if expires:
            params['expires'] = expires
        if start != 0:
            params['start'] = start
        if limit != 10:
            params['limit'] = limit
        if asc:
            params['asc'] = 1
        if source_url:
            params['source_url'] = source_url
        if save_path:
            params['save_path'] = save_path
        if create_time:
            params['create_time'] = create_time
        if status:
            params['status'] = status
        if not need_task_info:
            params['need_task_info'] = 0

        return self._fetch_pcsapi('services/cloud_dl', params, '')

    def cancel_task(self, task_id, expires=None):
        params = {
            'method': 'cancel_task',
            'task_id': task_id,
        }

        if expires:
            params['expires'] = expires

        return self._fetch_pcsapi('services/cloud_dl', params, '')

    def list_cycle(self, start=0, limit=1000):
        params = {'method': 'listrecycle'}
        if start != 0:
            params['start'] = start
        if limit != 1000:
            params['limit'] = limit
        return self._fetch_pcsapi('file', params)

    def restore_from_cycle(self, *args):
        assert args > 0
        if len(args) == 1:
            return self._restore_from_cycle(args[0])

        return self._batch_restore_from_cycle(args)

    def _restore_from_cycle(self, fs_id):
        params = {'method': 'restore', 'fs_id': fs_id}

        return self._fetch_pcsapi('file', params, '')

    def _batch_restore_from_cycle(self, fs_ids):
        params = {
            'method': 'restore',
            'param': json.dumps({'list': [{'fs_id': p} for p in fs_ids]})
        }

        return self._fetch_pcsapi('file', params, '')

    def empty_cycle(self):
        params = {'method': 'delete', 'type': 'recycle'}
        return self._fetch_pcsapi('file', params, '')

    # def create_share_url(self, remotefile):
    #     params = {
    #         'method': 'create',
    #         'type': 'public',
    #         'path': remotefile
    #     }

    #     return self._fetch_pcsapi('share', params, '')


class PCSApi(PCSApiMixin, ApiBase):
    pass
