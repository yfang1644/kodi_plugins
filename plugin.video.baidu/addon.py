#!/usr/bin/python
#coding=utf-8

from xbmcswift2 import Plugin, xbmc, xbmcgui, ListItem
from resources.lib.bilibili import Bilibili
from resources.lib.subtitle import subtitle_offset
import time
import string, os
from random import choice
from urllib import quote_plus
from qq import video_from_vid
from common import get_html
from json import loads
from bs4 import BeautifulSoup

plugin = Plugin()

def previous_page(endpoint, page, total_page, **kwargs):
    if int(page) > 1:
        page = str(int(page) - 1)
        return [{'label': u'上一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def next_page(endpoint, page, total_page, **kwargs):
    if int(page) < int(total_page):
        page = str(int(page) + 1)
        return [{'label': u'下一页 - {0}/{1}'.format(page, str(total_page)), 'path': plugin.url_for(endpoint, page=page, **kwargs)}]
    else:
        return []

def get_av_item(aid, **kwargs):
    result = bilibili.get_av_list(aid)
    item = dict(**kwargs)

    if len(result) == 1:
        vid = result[0].get('vid', '')
        item['is_playable'] = True
        if len(vid) > 0:
            item['label'] += '(QQ)'
        else:
            vid = '0'
        item['path'] = plugin.url_for('playmovie', cid=result[0]['cid'], vid=vid)
    else:
        item['path'] = plugin.url_for('list_video', aid=aid)
    return item


@plugin.route('/playmovie/<cid>/<vid>')
def playmovie(cid, vid='0'):
    if vid != '0':
        urls = video_from_vid(vid)
    else:
        urls = bilibili.get_video_urls(cid)

    stack_url = 'stack://' + ' , '.join(urls)
    danmu = plugin.addon.getSetting('danmu')

    playlist = xbmc.PlayList(1)
    playlist.clear()
    player = BiliPlayer()
    list_item = xbmcgui.ListItem(u'播放')
    playlist.add(stack_url, list_item)

    if danmu == 'true':
        bilibili.parse_subtitle(cid)
        player.setSubtitle(bilibili._get_tmp_dir() + '/tmp.ass')
    else:
        player.showSubtitles(False)
        player.show_subtitle = False

    player.play(playlist)
    #while(not xbmc.abortRequested):
    xbmc.sleep(1000)


@plugin.route('/list_video/<aid>')
def list_video(aid):
    plugin.set_content('videos')
    result = bilibili.get_av_list(aid)

    items = []
    for x in result:
        vid = x.get('vid', '')
        if len(vid) < 1:
            vid = '0'
        item = ListItem(**{
            'label': x['pagename'],
            'path': plugin.url_for('playmovie', cid=x['cid'], vid=vid)
        })
        item.set_info("video", {})
        item.set_is_playable(True)
        items.append(item)

    return items

@plugin.route('/searchResult/<page>/<keyword>')
def searchResult(page, keyword):
    searchapi = 'https://search.bilibili.com/ajax_api/video?keyword=%s&page=%s&order=totalrank'
    html = get_html(searchapi % (quote_plus(keyword), str(page)), decoded=False)
    html = html.replace('\\"', '')
    html = html.replace('\\t', '')
    html = html.replace('\\n', '')

    js = loads(html)
    total = js['numResults']
    total_page = js['numPages']
    tree = BeautifulSoup(js['html'], 'html.parser')

    videos = tree.find_all('li')
    items = previous_page('searchResult', page, total_page, keyword=keyword)

    for item in videos:
        aid = item.i['data-aid']
        thumb = item.img['data-src']
        if thumb[0:2] == '//':
            thumb = 'http:' + thumb
        title = item.find('a', {'class': 'title'}).text
        desc = item.find('div', {'class': 'des'})
        if desc is not None:
            desc = desc.text
        genre = item.find('span', {'class': 'type'}).text
        
        info = {
            'plot': desc,
            'genre': genre
            }
        items.append(get_av_item(aid, label=title, thumbnail=thumb, info=info))
    items += next_page('searchResult', page, total_page, keyword=keyword)

    return items 
    

@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard('', '请输入AV号(仅数字)')
    xbmc.sleep(1500)
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyword = keyboard.getText()
        return searchResult(page=1, keyword=keyword)

@plugin.route('/dynamic/<page>')
def dynamic(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_dynamic(page)
    items = previous_page('dynamic', page, total_page)
    for item1 in result:
        item = item1['addition']
        duration = 0
        for t in item['duration'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'genre': item['typename'],
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(item['create'][:4])
        except:
            pass
        items.append(get_av_item(item['aid'], label=item['title'], thumbnail=item['pic'], info = info))

    items += next_page('dynamic', page, total_page)
    return items

@plugin.route('/fav_box')
def fav_box():
    items = [{
        'label': item['name'], 
        'path': plugin.url_for('fav', fav_box = item['fav_box'], page = '1')
        } for item in bilibili.get_fav_box()]
    if len(items) == 1:
        plugin.redirect(items[0]['path'])
    else:
        return items

@plugin.route('/fav/<fav_box>/<page>')
def fav(fav_box, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_fav(fav_box, page)
    items = previous_page('fav', page, total_page, fav_box = fav_box)
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        items.append(get_av_item(item['aid'], label=item['title'], thumbnail=item['pic'], info=info))
    items += next_page('fav', page, total_page, fav_box = fav_box)
    return items

@plugin.route('/season/<season_id>')
def season(season_id):
    plugin.set_content('videos')
    result = bilibili.get_bangumi_detail(season_id)
    items = []
    bangumi_info = {
        'genre': '|'.join([tag['tag_name'] for tag in result['tags']]),
        'episode': len(result['episodes']),
        'castandrole': [u'{}|{}'.format(actor['actor'], actor['role']) for actor in result['actor']],
        'director': result['staff'],
        'plot': result['evaluate'],
        }
    for item in result['episodes']:
        info = dict(bangumi_info)
        try:
            info['year'] = int(item['update_time'][:4])
        except:
            pass
        title = u'【第{}话】'.format(item['index'])
        title += item['index_title']
        if item.get('is_new', '0') == '1':
            title += u'【新】'
        items.append(get_av_item(item['av_id'], label=title, thumbnail=item['cover'], info=info))
    return items


@plugin.route('/bangumi_chase/<page>')
def bangumi_chase(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_bangumi_chase(page)
    items = previous_page('bangumi_chase', page, total_page)
    for item in result:
        info = {
            'plot': item['brief'],  
            }
        title = item['title']
        if item['is_finish'] == 0:
            title += u'【更新至第{0}集】'.format(item['newest_ep_index'])
        else:
            title += u'【已完结】'
        items.append({
            'label': title,
            'path': plugin.url_for('season', season_id = item['season_id']),
            'thumbnail': item['cover'],
            'info': info,
            })
    items += next_page('bangumi_chase', page, total_page)
    return items

@plugin.route('/attention_video/<mid>/<tid>/<page>')
def attention_video(mid, tid, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_attention_video(mid, tid, page)
    items = []
    for item in result['vlist']:
        duration = 0
        for t in item['length'].split(':'):
            duration = duration * 60 + int(t)
        info = {
            'writer': item['author'],
            'plot': item['description'],
            'duration': duration,
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['created'])))
        except:
            pass
        try:
            info['genre'] = bilibili.get_category_name(item['typeid'])
        except:
            pass
        items.append(get_av_item(item['aid'], label=item['title'], thumbnail=item['pic'], info=info))
    items += next_page('attention_video', page, total_page, mid = mid, tid = tid)
    return items 

@plugin.route('/attention_channel_list/<mid>/<cid>/<page>')
def attention_channel_list(mid, cid, page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_attention_channel_list(mid, cid, page)
    items = []
    for item1 in result_info:
        item = item1['info']
        info = {
            'genre': item['tname'],
            'plot': item['desc'],
            'duration': item['duration'],
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        items.append(get_av_item(item['aid'], label=item['title'], thumbnail=item['pic'], info = info))
    items += next_page('attention_channel_list', page, total_page, mid = mid, cid = cid)
    return items 

@plugin.route('/attention_channel/<mid>')
def attention_channel(mid):
    result = bilibili.get_attention_channel(mid)
    items = []
    for item in result:
        title = u'{} ({}个视频) ({}更新)'.format(item['name'], str(item['count']), item['modify_time'][:10])
        items.append({
            'label': title,
            'path': plugin.url_for('attention_channel_list', mid = mid, cid = item['id'], page = '1'),
            })
    return items

@plugin.route('/user_info/<mid>')
def user_info(mid):
    result, total_page = bilibili.get_attention_video(mid, 0, 1, 1)
    items = []
    items.append({
        'label': u'频道',
        'path': plugin.url_for('attention_channel', mid = mid),
        })
    title = u'{} ({}个视频)'.format(u'全部', str(result['count']))
    items.append({
        'label': title,
        'path': plugin.url_for('attention_video', mid = mid, tid = '0', page = '1'),
        })
    for item in result['tlist'].values():
        title = u'{} ({}个视频)'.format(item['name'], str(item['count']))
        items.append({
            'label': title,
            'path': plugin.url_for('attention_video', mid = mid, tid = item['tid'], page = '1'),
            })
    return items

@plugin.route('/attention/<page>/')
def attention(page):
    result, total_page = bilibili.get_attention(page)
    items = []
    for item in result:
        items.append({
            'label': item['uname'],
            'path': plugin.url_for('user_info', mid = item['fid']),
            'thumbnail': item['face'],
            })
    items += next_page('attention', page, total_page)
    return items

@plugin.route('/login/')
def login():
    if bilibili.is_login == False:
        username = plugin.addon.getSetting('username')
        password = plugin.addon.getSetting('password')
        if username == '' or password == '':
            plugin.notify('请设置用户名密码', delay=2000)
            plugin.addon.openSettings()
            username = plugin.addon.getSetting('username')
            password = plugin.addon.getSetting('password')
            if username == '' or password == '':
                plugin.notify('用户名或密码为空', delay=2000)
                return
        filename = tempdir + ''.join(choice(string.ascii_uppercase + string.digits) for _ in range(10)) + '.jpg'
        captcha = LoginDialog(captcha = bilibili.get_captcha(filename)).get()
        os.remove(filename)
        result, msg = bilibili.login(username, password, captcha)
        if result == True:
            plugin.notify('登陆成功', delay=2000)
        else:
            plugin.notify(msg, delay=2000)


@plugin.route('/logout/')
def logout():
    bilibili.logout()


@plugin.route('/history/<page>/')
def history(page):
    plugin.set_content('videos')
    result, total_page = bilibili.get_history(page)
    items = previous_page('history', page, total_page)
    for item in result:
        info = {
            'genre': item['tname'],
            'writer': item['owner']['name'],
            'plot': item['desc'],
            'duration': item['duration']
            }
        try:
            info['year'] = int(time.strftime('%Y',time.localtime(item['ctime'])))
        except:
            pass
        items.append(get_av_item(item['aid'], label=item['title'], thumbnail=item['pic'], info=info))
    items += next_page('history', page, total_page)
    return items


@plugin.route('/category/<tid>')
def category(tid):
    items = []
    results = bilibili.get_category(tid)
    for data in results:
        tid = data.keys()[0]
        value = data.values()[0]
        if not value.has_key('subs') or len(value['subs']) == 0:
            path = plugin.url_for('category_tag', tid=tid)
        else:
            path = plugin.url_for('category', tid=tid)
        items.append({'label': value['title'], 'path': path})

    return items

@plugin.route('/category_tag/<tid>')
def category_tag(tid):
    orderapi = 'https://api.bilibili.com/x/tag/hots?rid={}'
    html = get_html(orderapi.format(tid))
    tags = loads(html)

    tags = tags['data'][0]['tags']

    items = [{
        'label': tag['tag_name'],
        'path': plugin.url_for('category_list',
                               tid=tid,
                               tag=tag['tag_id'],
                               page='1')
    } for tag in tags]

    items.insert(0, {
        'label': '全部',
        'path': plugin.url_for('category_list', tid=tid, tag='0', page=1)
    })
    return items


@plugin.route('/category_list/<tid>/<tag>/<page>')
def category_list(tid, tag, page):
    plugin.set_content('videos')
    page_size = 20
    listapi = 'https://www.bilibili.com/index/catalogy/%s-week.json' % tid
    listByTag = 'https://api.bilibili.com/x/tag/ranking/archives?jsonp=jsonp&tag_id={}&rid={}&ps={}&pn={}'
    listAll = 'https://api.bilibili.com/archive_rank/getarchiverankbypartion?type=jsonp&tid={}&ps={}&pn={}'
    if tag != '0':
        api = listByTag.format(tag, tid, page_size, page)
    else:
        api = listAll.format(tid, page_size, page)
    html = get_html(api)
    lists = loads(html)
    print lists
    archives = lists['data']['archives']
    size = lists['data']['page']['size']
    count = lists['data']['page']['count']
    total_page = (count + size - 1) // size
    items = previous_page('category_list', page, total_page, tid=tid, tag=tag)

    for item in archives:
        if tag != '0':
            x = item
        else:
            x = archives[item]
        info = {
            'genre': x.get('tname'),
            'writer': x.get('author'),
            'plot': x.get('description') or x.get('desc'),
            'duration': x.get('duration'),
            }
        try:
            info['year'] = int(x['create'][:4])
        except:
            pass

        items.append(get_av_item(x['aid'], label=x['title'], thumbnail=x['pic'], info=info))

    items += next_page('category_list', page, total_page, tid=tid, tag=tag)
    return items

@plugin.route('/')
def root():
    items = [
        {'label': u'视频搜索', 'path': plugin.url_for('search')},
        {'label': u'视频分类', 'path': plugin.url_for('category', tid = '0')},
    ]
    if bilibili.is_login:
        items += [
            {'label': u'我的动态', 'path': plugin.url_for('dynamic', page = '1')},
            {'label': u'我的历史', 'path': plugin.url_for('history', page = '1')},
            {'label': u'我的收藏', 'path': plugin.url_for('fav_box')},
            {'label': u'我的追番', 'path': plugin.url_for('bangumi_chase', page = '1')},
            {'label': u'我的关注', 'path': plugin.url_for('attention', page = '1')},
            {'label': u'退出登陆', 'path': plugin.url_for('logout')},
            ]
    else:
        items += [
            {'label': u'登陆账号', 'path': plugin.url_for('login')},
            ]
    return items


if __name__ == '__main__':
    plugin.run()
