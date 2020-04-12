#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from bs4 import BeautifulSoup
from json import loads
from common import get_html, r1
from lib.mgtv import video_from_vid, video_from_url, quote_plus

plugin = Plugin()
url_for = plugin.url_for

BANNER_FMT = '[COLOR FFDEB887]%s[/COLOR]'
BANNER_FMT2 = '[COLOR FFDE0087]%s[/COLOR]'
INDENT_FMT0 = '[COLOR FFDEB887]   %s[/COLOR]'
INDENT_FMT1 = '[COLOR FFDEB8FF]   %s[/COLOR]'

LIST_URL = 'http://list.mgtv.com'
HOST_URL = 'https://www.mgtv.com'

def httphead(url):
    if len(url) < 2:
        return url
    if url[:2] == '//':
        url = 'https:' + url
    elif url[0] == '/':
        url = HOST_URL + url

    return url


@plugin.route('/playvideo/<url>/')
def playvideo(url):
    level = int(plugin.addon.getSetting('resolution'))

    #m3u_url = video_from_vid(vid, level=level)
    m3u_url = video_from_url(httphead(url), level=level)
    stackurl = 'stack://' + ' , '.join(m3u_url) if len(m3u_url) > 1 else m3u_url[0]
    plugin.set_resolved_url(stackurl)


@plugin.route('/search')
def search():
    plugin.set_content('TVShows')
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if not keyboard.isConfirmed():
        return

    keyword = keyboard.getText()
    p_url = 'https://so.mgtv.com/so/k-'
    url = p_url + quote_plus(keyword)
    html = get_html(url)
    tree = BeautifulSoup(html, 'html.parser')
    soup = tree.findAll('div', {'class': 'result-content'})
    items = []
    for x in soup:
        try:
            vid = x.a['video-id']
        except:
            vid = 0
        items.append({
            'label': x.img['alt'],
            'path': url_for('episodelist', url=x.a['href'], id=vid, page=1),
            'thumbnail': x.img['src'],
        })

    return items


@plugin.route('/changeList/<url>/')
def changeList(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    tree = soup.findAll('div', {'class': 'm-tag-type'})

    dialog = xbmcgui.Dialog()

    item = tree[0]
    title = item.find('h5', {'class': 'u-title'}).text
    si = item.findAll('a')

    content = [x.text for x in si]
    sel = dialog.select(title, content)
    if sel >= 0:
        urlstr = str(si[sel])
        surl = r1("'(/.+?)'", urlstr)
        if surl:
            url = surl
        filter = si[sel].text.encode('utf-8')

    return mainlist(url, filter)


@plugin.route('/episodelist/<url>/<id>/<page>/')
def episodelist(url, id, page):
    if int(id) == 0:
        url = httphead(url)
        html = get_html(url)
        l = r1('window.location = "(.+?)"', html)
        if l:
            url = httphead(l)
        if url[-1] == '/':    # is a directory
            html = get_html(url)
            id = r1('vid:\s*(\d+)', html)
        else:
            id = r1('(\d+).html', url)
            html = get_html(url)
    else:
        url = httphead(url)
        if url[-1] == '/':
            html = get_html(url)
            url = r1('window.location = "(.+?)"', html)
        html = get_html(httphead(url))

    desc = r1('story:"(.+?)"', html)

    plugin.set_content('TVShows')
    episode_api = 'http://pcweb.api.mgtv.com/movie/list'   # ???
    episode_api = 'http://pcweb.api.mgtv.com/episode/list?video_id={}&page={}&size=50'
    page = int(page)

    html = get_html(episode_api.format(id, page))
    jsdata = loads(html)

    data = jsdata['data']
    total_page = data.get('total_page', 1)

    lists = data.get('list', [])
    for series in lists:
        title = series['t1'] + ' ' + series['t2']
        if series['isnew'] == '1':
            title = title + u'(新)'
        elif series['isnew'] == '2':
            title = title + u'(预)'

        vip = series.get('isvip', 0)
        pay = '(VIP)' if vip == '1' else ''
        d = series.get('time', '0:0')
        duration = 0
        for t in d.split(':'):
            duration = duration*60 + int(t)
        yield {
            'label': title + pay,
            #'path': url_for('playvideo', vid=series['video_id']),
            'path': url_for('playvideo', url=series['url']),
            'is_playable': True,
            'thumbnail': series['img'],
            'info': {'title': title, 'duration': duration, 'plot': desc}
        }

    if page > 1:
        yield {
            'label': BANNER_FMT % u'上一页',
            'path': url_for('episodelist', url=url, id=id, page=page-1)
        }
    if page < total_page:
        yield {
            'label': BANNER_FMT % u'下一页',
            'path': url_for('episodelist', url=url, id=id, page=page+1)
        }

    lists = data.get('short')
    if lists and (page == total_page):
        for series in lists:
            d = series.get('t2', '0:0')
            duration = 0
            for t in d.split(':'):
                duration = duration*60 + int(t)
            yield {
                'label': series['t1'],
                #'path': url_for('playvideo', vid=series['video_id']),
                'path': url_for('playvideo', url=series['url']),
                'is_playable': True,
                'thumbnail': series['img'],
                'info': {'title': title, 'duration': duration}
            }

    related = data.get('related')
    if related and (page == total_page):
        title = related['t1'] + ' ' + related['t2']
        yield {
            'label': BANNER_FMT2 % title,
            'path': url_for('episodelist', url=related['url'], id=0, page=1),
            'thumbnail': related['img'],
            'info': {'title': title}
        }

@plugin.route('/mainlist/<url>/<filter>/')
def mainlist(url, filter):
    if url[:2] == '//':
        utl = 'http:' + url
    elif url[0] == '/':
        url = LIST_URL + url
    plugin.set_content('TVShows')
    filtitle = '' if filter == '0' else filter
    items = [{
        'label': BANNER_FMT % ('[分类过滤]' + filtitle),
        'path': url_for('changeList', url=url)
    }]

    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')

    tree = soup.find('div', {'class': 'm-result-list'})

    tree = tree.findAll('li', {'class': 'm-result-list-item'})
    for item in tree:
        t = item.find('a', {'class': 'u-title'})
        title = t.text
        href = t['href']
        t = item.find('a', {'class': 'u-video'})
        try:
            exinfo = '(' + item.em.text + ')'
        except:
            exinfo = ''

        # pay info
        pay = item.find('i', {'class': 'mark-v'})
        if pay:
            pay = BANNER_FMT2 % ('(' + pay.text + ')')
        else:
            pay = ''

        pinfo = item.find('span', {'class': 'u-desc'})
        info = pinfo.text.replace(' ', '')
        info = info.replace('\t', '')
        items.append({
            'label': title + exinfo + pay,
            'path': url_for('episodelist', url=t['href'], id=0, page=1),
            'thumbnail': httphead(item.img['src']),
            'info': {'title': title, 'plot': info}
        })

    # multiple pages
    setpage = soup.find('div', {'class': 'w-pages'})
    try:
        pages = setpage.findAll('li')
    except:
        return items

    for page in pages:
        title = page.a.get('title', '')
        href = page.a.get('href')
        if href == 'javascript:;' or title == '':
            continue
        items.append({
            'label': BANNER_FMT % title,
            'path': url_for('mainlist', url=href, filter=filter)
        })

    return items

@plugin.route('/')
def root():
    yield {
        'label': BANNER_FMT % '搜索',
        'path': url_for('search')
    }

    mainAPI = 'http://pc.bz.mgtv.com/odin/c1/channel/list?version=5.0&type=4&pageSize=999'
    jsdata = loads(get_html(mainAPI))

    for item in jsdata['data'][1:]:
        url = '/-------------.html?channelId=' + item['pageType']
        yield {
            'label': item['title'],
            'path': url_for('mainlist',
                            url=url,
                            filter='0'),
            'thumbnail': item.get('channelIcon'),
            'info': {'title': item['title'], 'plot': item['vclassName']}
        }

if __name__ == '__main__':
    plugin.run()
