#!/usr/bin/python
#coding=utf-8

import sys
import base64
from json import loads
import hashlib
if sys.version[0] == '3':
    from urllib.parse import urlencode, quote_plus, urlparse
    from urllib.request import Request, urlopen
else:
    from urllib import urlencode, quote_plus
    from urlparse import urlparse
    from urllib2 import Request, urlopen

import urllib2
import re
import time
import os
import tempfile
from random import random
from xml.dom.minidom import parseString
from cookielib import MozillaCookieJar
from common import get_html
from bs4 import BeautifulSoup
from bilibili_config import *
from niconvert import create_website

def url_locations(url):
    response = urlopen(Request(url))
    return response.url

class Bilibili():
    name = u'哔哩哔哩 (Bilibili)'

    api_url = 'http://interface.bilibili.com/v2/playurl?'
    bangumi_api_url = 'http://bangumi.bilibili.com/player/web_api/playurl?'
    SEC1 = '94aba54af9065f71de72f5508f1cd42e'
    SEC2 = '9b288147e5474dd2aa67085f716c560d'
    supported_stream_profile = [u'流畅', u'高清', u'超清']
    stream_types = [
        {'id': 'hdflv'},
        {'id': 'flv'},
        {'id': 'hdmp4'},
        {'id': 'mp4'},
        {'id': 'live'},
        {'id': 'vc'}
    ]
    fmt2qlt = dict(hdflv=4, flv=3, hdmp4=2, mp4=1)

    def __init__(self, appkey=APPKEY, appsecret=APPSECRET,
                 width=720, height=480):
        self.defaultHeader = {'Referer':'http://www.bilibili.com'}
        #self.defaultHeader = {}
        self.appkey = appkey
        self.appsecret = appsecret
        self.WIDTH = width
        self.HEIGHT = height
        self.is_login = False
        cookie_path = os.path.dirname(os.path.abspath(__file__)) + '/.cookie'
        self.cj = MozillaCookieJar(cookie_path)
        if os.path.isfile(cookie_path):
            self.cj.load()
            key = None
            for ck in self.cj:
                if ck.name == 'DedeUserID':
                    key = ck.value
                    break
            if key is not None:
                self.is_login = True
                self.mid = str(key)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)

        try:
            os.remove(self._get_tmp_dir() + '/tmp.ass')
        except:
            pass

    def _get_tmp_dir(self):
        try:
            return tempfile.gettempdir()
        except:
            return ''

    def get_captcha(self, path = None):
        key = None
        for ck in self.cj:
            if ck.name == 'sid':
                key = ck.value
                break

        if key is None:
            get_html(LOGIN_CAPTCHA_URL.format(random()),
                    headers = {'Referer':'https://passport.bilibili.com/login'})
        result = get_html(LOGIN_CAPTCHA_URL.format(random()), decoded=False,
                    headers = {'Referer':'https://passport.bilibili.com/login'})
        if path is None:
            path = tempfile.gettempdir() + '/captcha.jpg'
        with open(path, 'wb') as f:
            f.write(result)
        return path

    def get_encryped_pwd(self, pwd):
        import rsa
        result = loads(get_html(LOGIN_HASH_URL.format(random()),
                    headers={'Referer':'https://passport.bilibili.com/login'}))
        pwd = result['hash'] + pwd
        key = result['key']
        pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(key)
        pwd = rsa.encrypt(pwd.encode('utf-8'), pub_key)
        pwd = base64.b64encode(pwd)
        pwd = quote_plus(pwd)
        return pwd

    def api_sign(self, params):
        params['appkey'] = self.appkey
        data = ''
        keys = params.keys()
        # must sorted.  urlencode(params) doesn't work
        keys.sort()
        for key in keys:
            data += '{}={}&'.format(key, quote_plus(str(params[key])))

        data = data[:-1]  # remove last '&'
        if self.appsecret is None:
            return data
        m = hashlib.md5()
        m.update(data + self.appsecret)
        return data + '&sign=' + m.hexdigest()

    def get_category_from_web_page(self):
        category_dict = {'0': {'title': u'全部', 'url': HOME_URL}}
        node = category_dict['0']
        url = node['url']
        result = BeautifulSoup(get_html(url), "html.parser").findAll('li', {'class': 'm-i'})
        for item in result:
            if len(item['class']) != 1:
                continue
            tid = item['data-tid']
            title = item.em.contents[0]
            url = 'http:' + item.a['href']
            category_dict[tid] = {'title': title, 'url': url}
            node['subs'].append(tid)

        #Fix video and movie
        if '11' not in category_dict['0']['subs']:
            category_dict['0']['subs'].append('11')
        if '23' not in category_dict['0']['subs']:
            category_dict['0']['subs'].append('23')
        category_dict['11'] = {'title': u'电视剧', 'url': 'http://bangumi.bilibili.com/tv/'}
        category_dict['23'] = {'title': u'电影', 'url': 'http://bangumi.bilibili.com/movie/'}

        for sub in category_dict['0']['subs']:
            node = category_dict[sub]
            url = node['url']
            result = BeautifulSoup(get_html(url), "html.parser").select('ul.n_num li')
            for item in result[1:]:
                if not item.has_attr('tid'):
                    continue
                if not hasattr(item, 'a'):
                    continue
                if item.has_attr('class'):
                    continue
                tid = item['tid']
                title = item.a.contents[0]
                if item.a['href'][:2] == '//':
                    url = 'http:' + item.a['href']
                else:
                    url = HOME_URL + item.a['href']
                category_dict[tid] = {'title': title, 'url': url}
                node['subs'].append(tid)
        return category_dict

    def get_category(self, tid = '0'):
        items = [{tid: {'title': '全部', 'url': CATEGORY[tid]['url']}}]
        for sub in CATEGORY[tid]['subs']:
            items.append({sub: CATEGORY[sub]})
        return items

    def get_category_name(self, tid):
        return CATEGORY[str(tid)]['title']

    def get_order(self):
        return ORDER

    def get_category_by_tag(self, tag=0, tid=0, page=1, pagesize=20):
        if tag == 0:
            url = LIST_BY_ALL.format(tid, pagesize, page)
        else:
            url = LIST_BY_TAG.format(tag, tid, pagesize, page)
        
        results = loads(get_html(url))
        return results

    def get_category_list(self, tid = 0, order = 'default', days = 30, page = 1, pagesize = 20):
        params = {'tid': tid, 'order': order, 'days': days, 'page': page, 'pagesize': pagesize}
        url = LIST_URL.format(self.api_sign(params))

        result = loads(get_html(url, headers=self.defaultHeader))
        results = []
        for i in range(pagesize):
            if result['list'].has_key(str(i)):
                results.append(result['list'][str(i)])
            else:
                continue
        return results, result['pages']

    def get_my_info(self):
        if self.is_login == False:
            return []
        result = loads(get_html(MY_INFO_URL))
        return result['data']

    def get_bangumi_chase(self, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = BANGUMI_CHASE_URL.format(self.mid, page, pagesize)
        result = loads(get_html(url, headers=self.defaultHeader))
        return result['data']['result'], result['data']['pages']

    def get_bangumi_detail(self, season_id):
        url = BANGUMI_SEASON_URL.format(season_id)
        result = get_html(url, headers=self.defaultHeader)
        if result[0] != '{':
            start = result.find('(') + 1
            end = result.find(');')
            result = result[start:end]
        result = loads(result)
        return result['result']

    def get_history(self, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = HISTORY_URL.format(page, pagesize)
        result = loads(get_html(url, headers=self.defaultHeader))
        if len(result['data']) >= int(pagesize):
            total_page = int(page) + 1
        else:
            total_page = int(page)
        return result['data'], total_page

    def get_dynamic(self, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = DYNAMIC_URL.format(pagesize, page)
        result = loads(get_html(url, headers=self.defaultHeader))
        total_page = int((result['data']['page']['count'] + pagesize - 1) / pagesize)
        return result['data']['feeds'], total_page

    def get_attention(self, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = ATTENTION_URL.format(self.mid, page, pagesize)
        result = loads(get_html(url))
        return result['data']['list']

    def get_attention_video(self, mid, tid = 0, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = ATTENTION_VIDEO_URL.format(mid, page, pagesize, tid)
        result = loads(get_html(url, headers=self.defaultHeader))
        return result['data'], result['data']['pages']

    def get_attention_channel(self, mid):
        if self.is_login == False:
            return []
        url = ATTENTION_CHANNEL_URL.format(mid)
        result = loads(get_html(url, headers=self.defaultHeader))
        return result['data']['list']

    def get_fav_box(self):
        if self.is_login == False:
            return []
        url = FAV_BOX_URL.format(self.mid)
        result = loads(get_html(url, headers=self.defaultHeader))
        return result['data']['list']

    def get_fav(self, fav_box, page = 1, pagesize = 20):
        if self.is_login == False:
            return []
        url = FAV_URL.format(self.mid, page, pagesize, fav_box)
        result = loads(get_html(url, headers=self.defaultHeader))
        return result['data']['vlist'], result['data']['pages']

    def login(self, userid, pwd, captcha):
        #utils.get_html('http://www.bilibili.com')
        if self.is_login == True:
            return True, ''
        pwd = self.get_encryped_pwd(pwd)
        data = 'cType=2&vcType=1&captcha={}&user={}&pwd={}&keep=true&gourl=http://www.bilibili.com/'.format(captcha, userid, pwd)
        result = get_html(LOGIN_URL, data,
                    {'Origin':'https://passport.bilibili.com',
                    'Referer':'https://passport.bilibili.com/login'})

        key = None
        for ck in self.cj:
            if ck.name == 'DedeUserID':
                key = ck.value
                break

        if key is None:
            return False, LOGIN_ERROR_MAP[loads(result)['code']]
        self.cj.save()
        self.is_login = True
        self.mid = str(key)
        return True, ''

    def logout(self):
        self.cj.clear()
        self.cj.save()
        self.is_login = False

    def get_av_list_detail(self, aid, page = 1, fav = 0, pagesize = 20):
        params = {'id': aid, 'page': page}
        if fav != 0:
            params['fav'] = fav
        url = VIEW_URL.format(self.api_sign(params))
        result = loads(get_html(url, headers=self.defaultHeader))
        results = [result]
        if (int(page) < result['pages']) and (pagesize > 1):
            results += self.get_av_list_detail(aid, int(page) + 1, fav, pagesize = pagesize - 1)[0]

        return results, result['pages']

    def get_av_list(self, aid):
        url = AV_URL.format(aid)
        try:
            page = get_html(url)
            result = loads(page)
        except:
            result = {}
        return result


    # 调用niconvert生成弹幕的ass文件
    def parse_subtitle(self, cid):
        page_full_url = COMMENT_URL.format(cid)
        website = create_website(page_full_url)
        if website is None:
            return ''
        else:
            text = website.ass_subtitles_text(
                font_name=u'黑体',
                font_size=24,
                resolution='%d:%d' % (self.WIDTH, self.HEIGHT),
                line_count=12,
                bottom_margin=0,
                tune_seconds=0
            )
            f = open(self._get_tmp_dir() + '/tmp.ass', 'w')
            f.write(text.encode('utf8'))
            f.close()
            return 'tmp.ass'

    def get_video_urls(self, cid, qn=0):
        req = {
            'appkey': APPKEY,
            'cid': cid,
            'platform': 'html5',
            'player': 0,
            'qn': qn
        }
        data = urlencode(req)
        chksum = hashlib.md5(compact_bytes(params_str + SECRETKEY, 'utf-8')).hexdigest()

        purl = '{}?{}&sign={}'.format(api_url, params_str, chksum)
        print "XXXXXXXXXXXXXXXXX",purl
        html = get_html(purl)

        m = hashlib.md5()
        m.update(INTERFACE_PARAMS.format(str(cid), SECRETKEY_MINILOADER))
        url = INTERFACE_URL.format(str(cid), m.hexdigest())
        doc = parseString(get_html(url))
        urls = []
        for durl in doc.getElementsByTagName('durl'):
            u = durl.getElementsByTagName('url')[0].firstChild.nodeValue
            if re.match(r'.*\.qqvideo\.tc\.qq\.com', url):
                re.sub(r'.*\.qqvideo\.tc', 'http://vsrc.store', u)
            urls.append(u)
            #urls.append(u + '|Referer={}'.format(quote('https://www.bilibili.com/')))

        return urls

    def add_history(self, aid, cid):
        url = ADD_HISTORY_URL.format(str(cid), str(aid))
        get_html(url)

    def api_req(self, cid, quality, bangumi, bangumi_movie=False, **kwargs):
        ts = str(int(time.time()))
        if not bangumi:
            params_str = 'cid={}&player=1&quality={}&ts={}'.format(cid, quality, ts)
            chksum = hashlib.md5(bytes(params_str+self.SEC1)).hexdigest()
            api_url = self.api_url + params_str + '&sign=' + chksum
        else:
            mod = 'movie' if bangumi_movie else 'bangumi'
            params_str = 'cid={}&module={}&player=1&quality={}&ts={}'.format(cid, mod, quality, ts)
            chksum = hashlib.md5(bytes(params_str+self.SEC2)).hexdigest()
            api_url = self.bangumi_api_url + params_str + '&sign=' + chksum

        return get_html(api_url)

    def download_by_vid(self, cid, bangumi, **kwargs):
        stream_id = kwargs.get('stream_id')
        if stream_id and stream_id in self.fmt2qlt:
            quality = stream_id
        else:
            quality = 'hdflv' if bangumi else 'flv'

        level = kwargs.get('level', 0)
        xml = self.api_req(cid, level, bangumi, **kwargs)
        doc = parseString(xml)
        urls = []
        for durl in doc.getElementsByTagName('durl'):
            u = durl.getElementsByTagName('url')[0].firstChild.nodeValue
            #urls.append(u)
            urls.append(quote_plus(u + '|Referer=https://www.bilibili.com'))

        return urls

    def entry(self, **kwargs):
        # tencent player
        tc_flashvars = re.search(r'"bili-cid=\d+&bili-aid=\d+&vid=([^"]+)"', self.page)
        if tc_flashvars:
            tc_flashvars = tc_flashvars.group(1)
        if tc_flashvars is not None:
            self.out = True
            return qq_download_by_vid(tc_flashvars, self.title, output_dir=kwargs['output_dir'], merge=kwargs['merge'], info_only=kwargs['info_only'])

        cid = re.search(r'cid=(\d+)', self.page).group(1)
        if cid is not None:
            return self.download_by_vid(cid, False, **kwargs)
        else:
        # flashvars?
            flashvars = re.search(r'flashvars="([^"]+)"', self.page).group(1)
            if flashvars is None:
                raise Exception('Unsupported page {}'.format(self.url))
            param = flashvars.split('&')[0]
            t, cid = param.split('=')
            t = t.strip()
            cid = cid.strip()
            if t == 'vid':
                sina_download_by_vid(cid, self.title, output_dir=kwargs['output_dir'], merge=kwargs['merge'], info_only=kwargs['info_only'])
            elif t == 'ykid':
                youku_download_by_vid(cid, self.title, output_dir=kwargs['output_dir'], merge=kwargs['merge'], info_only=kwargs['info_only'])
            elif t == 'uid':
                tudou_download_by_id(cid, self.title, output_dir=kwargs['output_dir'], merge=kwargs['merge'], info_only=kwargs['info_only'])
            else:
                raise NotImplementedError('Unknown flashvars {}'.format(flashvars))
            return

    def movie_entry(self, **kwargs):
        patt = r"var\s*aid\s*=\s*'(\d+)'"
        aid = re.search(patt, self.page).group(1)
        page_list = loads(get_html('http://www.bilibili.com/widget/getPageList?aid={}'.format(aid)))
        # better ideas for bangumi_movie titles?
        self.title = page_list[0]['pagename']
        return self.download_by_vid(page_list[0]['cid'], True, bangumi_movie=True, **kwargs)

    def get_video_from_url(self, url, **kwargs):
        self.url = url_locations(url)
        frag = urlparse(self.url).fragment
        # http://www.bilibili.com/video/av3141144/index_2.html#page=3
        if frag:
            hit = re.search(r'page=(\d+)', frag)
            if hit is not None:
                page = hit.group(1)
                av_id = re.search(r'av(\d+)', self.url).group(1)
                self.url = 'http://www.bilibili.com/video/av{}/index_{}.html'.format(av_id, page)
        self.page = get_html(self.url)

        if 'bangumi.bilibili.com/movie' in self.url:
            return self.movie_entry(**kwargs)
        elif 'bangumi.bilibili.com' in self.url:
            return self.bangumi_entry(**kwargs)
        elif 'live.bilibili.com' in self.url:
            return self.live_entry(**kwargs)
        elif 'vc.bilibili.com' in self.url:
            return self.vc_entry(**kwargs)
        else:
            return self.entry(**kwargs)

    def bangumi_entry(self, **kwargs):
        pass
    def live_entry(self, **kwargs):
        pass
    def vc_entry(self, **kwargs):
        pass

if __name__ == '__main__':
    b = Bilibili()
    #if b.is_login == False:
    #    b.get_captcha('')
    #    captcha = raw_input('Captcha: ')
    #    print b.login(u'catro@foxmail.com', u'123456', captcha)
    #print b.get_fav(49890104)
    #print b.get_av_list(8163111)
    #print b.add_history(8163111, 13425238)
    #print b.get_video_urls(12821893)
    #print b.get_category_list('32')
    #print b.get_dynamic('2')[1]
    #print b.get_category()
    #print b.get_bangumi_chase()
    #print b.get_attention()
    #print b.get_attention_video('7349', 0, 1, 1)
    #print b.get_attention_channel('7349')
    #print json.dumps(b.get_bangumi_detail('5800'), indent=4, ensure_ascii=False)
    #print b.get_bangumi_detail('5800')
    #print b.get_history(1)
    #with open('bilibili_config.py', 'a') as f:
    #    f.write('\nCATEGORY = ')
    #    f.write(json.dumps(b.get_category_from_web_page(), indent=4, ensure_ascii=False).encode('utf8'))
