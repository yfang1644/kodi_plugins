#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import json
import time
import traceback
from pkgutil import iter_modules
from urllib import quote_plus

from xbmcswift2 import Plugin, actions, xbmc, xbmcgui
import xbmcvfs


plugin = Plugin()
plugin_path = plugin.addon.getAddonInfo('path')
lib_path = os.path.join(plugin_path, 'resources', 'lib')
sys.path[0:0] = [lib_path,
                 os.path.join(lib_path, 'poster-0.4-py2.6.egg'),
                 os.path.join(lib_path, 'rsa_x509_pem-0.1.0.egg')]

import xbmcutils
import modules
import myplayer
from client_api import ClientAPI, PCSApiError, ClientApiError, TRANSCODE_TYPES
from CaptchaDialog import CaptchaDialog
from utils import fetch_url

_registered_modules = []


def register_modules(modname=None):
    global _registered_modules

    if modname:
        try:
            module = __import__(
                modules.__name__ + '.' + modname, fromlist='dummy')
        except ImportError:
            pass
        else:
            plugin.register_module(module.m, '/' + modname)
            _registered_modules.append((modname, module))
            return True

        return

    for _, modname, _ in iter_modules(modules.__path__, ):
        try:
            module = __import__(
                modules.__name__ + '.' + modname, fromlist='dummy')
            _registered_modules.append((modname, module))
        except ImportError:
            plugin.log.debug(traceback.print_exc())
            continue

        plugin.register_module(module.m, '/' + modname)


@plugin.route('/')
def index():
    userid = get_default_userid()

    items = [{
        'label': '[COLOR FFFFFF00]记事本[/COLOR]',
        'path': plugin.url_for('mynotes', userid=userid),
        'thumbnail': os.path.join(
            plugin_path, 'resources/skins/Default/720p/note.png')
    }, {
        #     'label': '[COLOR FFFFFF00]分享动态[/COLOR]',
        #     'path': plugin.url_for('dynamic_list', userid=userid, page=0)
        # }, {
        'label': '[COLOR FFFFFF00]我的关注[/COLOR]',
        'path': plugin.url_for('myfollows', userid=userid, page=0)
    }] if userid else []

    items.extend([{
        'label': '[COLOR FFFFFF00]资源分享[/COLOR]',
        'path': plugin.url_for('hdp_albums')
    }, {
        'label': '[COLOR FFFFFF00]热门资源[/COLOR]',
        'path': plugin.url_for('resources')
    }, {
        'label': '[COLOR FFFFFF00]达人推荐[/COLOR]',
        'path': plugin.url_for('hot_user_list', userid=str(userid),
                               page=0)
    }, {
        'label': '[COLOR FFFFFF00]设置[/COLOR]',
        'path': plugin.url_for('settings'),
    }])

    if plugin.get_setting('test_features', bool):
        items.append({
            'label': '[COLOR FFFFFF00]打开目录[/COLOR]',
            'path': plugin.url_for('open_dir'),
        })

    try:
        items[0:0] = list_dir(userid)
    except:
        plugin.log.info(traceback.format_exc())
        xbmcutils.show_msg('获取目录列表失败，请检查帐号设置是否正确！', '错误')

    return plugin.finish(items, view_mode='thumbnail')


@plugin.route('/open_dir/')
def open_dir():
    dialog = xbmcgui.Dialog()
    dirpath = dialog.browse(0, u'请选择需要打开的目录', 'files')
    if not dirpath:
        return

    xbmc.executebuiltin(
        'Container.Update(plugin://script.module.hdpparser?parser=listdir&uri=%s)' % quote_plus(dirpath))  # noqa


@plugin.route('/hdp_albums/')
def hdp_albums():
    return [{
        'label': r['title'],
        'path': 'plugin://script.module.hdpparser?uri=' + quote_plus(r['url']),
        'thumbnail': r.get('thumb'),
    } for r in json.loads(fetch_url('http://xbmc.hdpfans.com/albums.json'))
    ]


@plugin.route('/mynotes/<userid>/')
def mynotes(userid):
    if userid == 'null':
        return []

    return list_mynotes(userid)


# @plugin.route('/dynamic_list/<userid>/<page>/')
# def dynamic_list(userid, page=0):
#     if userid == 'null':
#         return []

#     page = int(page)

#     items, total_count = list_dynamic_list(userid, page)
#     if 50 * (page + 1) < total_count:
#         items.append({
#             'label': '[COLOR FFFFFF00]下一页[/COLOR]',
#             'path': plugin.url_for('dynamic_list', userid=userid,
#                                    page=page + 1)
#         })

#     return items


@plugin.route('/myfollows/<userid>/<page>/')
def myfollows(userid, page):
    if userid == 'null':
        return []

    page = int(page)

    api = get_api(userid)
    uk = get_uk(userid)

    follow_list, total_count = api.get_follow_list(uk, 24 * page)
    items = [{
        'label': '[[COLOR FF00FFFF]%s[/COLOR]] ([COLOR FF00FF00]%d[/COLOR]) %s' % (  # noqa
            user['follow_uname'], user['pubshare_count'], user['intro']),
        'path': 'plugin://script.module.hdpparser?uri=http%3A%2F%2Fyun.baidu.com%2Fshare%2Fhome%3Fuk%3D{0}'.format(user['follow_uk']),  # noqa
        # 'context_menu': [
        #     (
        #         '[COLOR FFFFFF00]取消关注[/COLOR]',
        #         actions.background(plugin.url_for(
        #             'unfollow', userid=userid, follow_uk=user['follow_uk']))
        #     )],
        # 'replace_context_menu': True
    } for user in follow_list]

    if 24 * (page + 1) < total_count:
        items.append({
            'label': '[COLOR FFFFFF00]下一页[/COLOR]',
            'path': plugin.url_for('myfollows', userid=userid,
                                   page=page + 1)
        })

    # if page == 0:
    #     items.append({
    #                  'label': '[COLOR FFFFFF00]达人推荐[/COLOR]',
    #                  'path': plugin.url_for('hot_user_list', userid=userid,
    #                                         page=0)
    #                  })

    return items


@plugin.route('/unfollow/<userid>/<follow_uk>/')
def unfollow(userid, follow_uk):
    api = get_api(userid)
    api.unfollow(follow_uk)
    xbmcutils.refresh()


@plugin.route('/follow/<userid>/<follow_uk>/<follow_uname>/')
def follow(userid, follow_uk, follow_uname):
    api = get_api(userid)
    api.follow(follow_uk, follow_uname)


@plugin.route('/hot_user_list/<userid>/<page>/')
def hot_user_list(userid, page=0):
    page = int(page)
    api = get_api(userid)
    hotuser_list = api.get_hot_user_list(page * 20)
    items = [{
        'label': '[[COLOR FF00FFFF]%s[/COLOR]] ([COLOR FF00FF00]%d[/COLOR]) %s' % (  # noqa
            user['hot_uname'], user['pubshare_count'], user['intro']),
        'path': 'plugin://script.module.hdpparser?uri=http%3A%2F%2Fyun.baidu.com%2Fshare%2Fhome%3Fuk%3D{0}'.format(user['hot_uk']),  # noqa
        'thumbnail': user.get('avatar_url'),
        # 'context_menu': [
        #     (
        #         '[COLOR FFFFFF00]加关注[/COLOR]',
        #         actions.background(plugin.url_for(
        #             'follow', userid=userid, follow_uk=user['hot_uk'],
        #             follow_uname=user['hot_uname'].encode('utf-8')))
        #     )]
    } for user in hotuser_list]

    if len(items) == 20:
        items.append({
            'label': '[COLOR FFFFFF00]下一页[/COLOR]',
            'path': plugin.url_for('hot_user_list', userid=userid,
                                   page=page + 1)
        })

    return items


@plugin.route('/resources/')
def resources():
    return [{
        'label': getattr(module, 'title', modname),
        'path': module.m.url_for('index')
    } for modname, module in _registered_modules]


@plugin.route('/mynote/<userid>/<note_id>/<category_id>/')
def show_note_btih(userid, note_id, category_id):
    api = get_api(userid)
    notes = [n for n in api.list_note(category_id) if n['_key'] == note_id]
    if notes:
        tmpfile = 'special://temp/_baidu_note.bth'
        xbmcvfs.File(tmpfile, 'w').write(notes[0]['content'].encode('utf-8'))
        xbmc.executebuiltin(
            'Container.Update(plugin://script.module.hdpparser?parser=bth&uri=special%3A%2F%2Ftemp%2F_baidu_note.bth)')  # noqa


@plugin.route('/list_user_dir/<userid>/<path>/')
def list_user_dir(userid, path):
    items = list_dir(userid, path)
    return plugin.finish(items, view_mode='thumbnail')


@plugin.route('/delete_path/<userid>/<path>/')
def delete_path(userid, path):
    api = get_api(userid)
    try:
        plugin.notify('正在删除文件，请稍候...', delay=2000)
        api.delete(path)
    except PCSApiError as e:
        xbmcutils.show_msg(str(e), '错误')
    else:
        xbmc.sleep(1000)
        xbmcutils.refresh()


@plugin.route('/stream/<url>/<name>/', 'play_stream_noresolved')
@plugin.route('/stream/<url>/')
def play_stream(url, name=None):
    params = dict((k, v[0]) for k, v in plugin.request.args.items())
    subtitle = params.get('subtitle')
    if subtitle:
        subtitle += '|User-Agent=Mozilla/5.0%20%28Windows%20NT%206.1%3B%20rv%3A25.0%29%20Gecko/20100101%20Firefox/25.0&Referer=http%3A//pan.baidu.com/disk/home'  # noqa

    url += '|User-Agent=Mozilla/5.0%20%28Windows%20NT%206.1%3B%20rv%3A25.0%29%20Gecko/20100101%20Firefox/25.0&Referer=http%3A//pan.baidu.com/disk/home'  # noqa

    if name is None:
        plugin.set_resolved_url(url, subtitle)
    elif is_torrent(name):
        plugin.redirect(plugin.url_for('play_torrent', url=url))
    else:
        listitem = xbmcgui.ListItem(name)
        player = myplayer.Player()
        player.play(url, listitem, sublist=subtitle)


@plugin.route('/play_path/<userid>/<path>/<name>/<md5>/')
def play_path(userid, path, md5, name=None):
    params = dict((k, v[0]) for k, v in plugin.request.args.items())
    subtitle = params.get('subtitle')
    if subtitle:
        subtitle = [get_dlink(userid, subtitle) + '|User-Agent=AppleCoreMedia/1.0.0.9B206 (iPad; U; CPU OS 5_1_1 like Mac OS X; zh_cn)']  # noqa
    else:
        subtitle = []

    # api = get_api(userid)
    # item = api.get_filemetas(path)['info'][0]
    # url = item['dlink'] + '|User-Agent=AppleCoreMedia/1.0.0.9B206 (iPad; U; CPU OS 5_1_1 like Mac OS X; zh_cn)'  # noqa
    url = get_dlink(userid, path) + '|User-Agent=AppleCoreMedia/1.0.0.9B206 (iPad; U; CPU OS 5_1_1 like Mac OS X; zh_cn)'  # noqa

    api = get_api(userid)
    api_res = api.get_subtitle(md5, name or '', path)
    if api_res['total_num'] > 0:
        for sub_record in api_res['records']:
            subtitle.insert(0, sub_record['file_path'])

    params = dict((k, v[0]) for k, v in plugin.request.args.items())
    if 'resolved' in params:
        plugin.set_resolved_url(url)

        if subtitle:
            player = xbmc.Player()
            for _ in xrange(30):
                if player.isPlaying():
                    break
                time.sleep(1)
            else:
                raise Exception('No video playing. Aborted after 30 seconds.')

            for surl in subtitle:
                # print '$'*50, surl
                player.setSubtitles(surl)

            # player.setSubtitleStream(0)

    else:
        listitem = xbmcgui.ListItem(name)
        player = myplayer.Player()
        player.play(url, listitem, sublist=subtitle)


# @plugin.route('/play_torrent/<userid>/<url>/')
# def play_torrent(userid, url):
#     xbmc.executebuiltin(
# 'Container.Update(plugin://plugin.video.btfactory/btmanager/play_torrent/%s/)' %  # noqa
#         quote_url(url))


# @plugin.route('/show_compressed_file/<name>/<url>/')
# def show_compressed_file(name, url):
#     xbmc.executebuiltin(
# 'Container.Update(plugin://plugin.video.btfactory/btmanager/listdir/%s/)' %  # noqa
#         quote_url(quote_url('%s://%s/' % (name[-3:].lower(), quote_url(u


@plugin.route('/play_transcode_video/<userid>/<path>/<name>/<md5>/user/',
              name='play_transcode_video_select_type',
              options={'select_type': True})
@plugin.route('/play_transcode_video/<userid>/<path>/<name>/<md5>/')
def play_transcode_video(userid, path, name, md5, select_type=False):
    player = myplayer.Player()
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type="Video", infoLabels={'Title': name})

    api = get_api(userid)
    if select_type:
        choice = xbmcutils.select('请选转码格式', TRANSCODE_TYPES)
        if choice < 0:
            return
        transcode_type = TRANSCODE_TYPES[choice]
    else:
        transcode_type = plugin.get_setting('transcode_type', str)

    params = dict((k, v[0]) for k, v in plugin.request.args.items())
    subtitle = params.get('subtitle')
    if subtitle:
        subtitle = [subtitle]
    else:
        subtitle = []

    api_res = api.get_subtitle(md5, name or '', path)
    if api_res['total_num'] > 0:
        for sub_record in api_res['records']:
            subtitle.append(sub_record['file_path'])

    player.play(api.get_transcode_url(path, transcode_type),
                listitem, sublist=subtitle)


@plugin.route('/settings/')
def settings():
    current_user = get_default_userid()

    items = [{
        'label': '当前帐号： [COLOR FFFFFF00]%s[/COLOR]' % (
            current_user or NULL_USER),
        'path': plugin.url_for('select_user'),
        'is_playable': True,
        'properties': {'isPlayable': ''}
    }, {
        'label': '帐号管理',
        'path': plugin.url_for('users_list')
    }, {
        'label': '清空缓存',
        'path': plugin.url_for('clear_cache'),
        'is_playable': True,
        'properties': {'isPlayable': ''}
    }]

    return items


@plugin.route('/select_user/')
def select_user():
    config = plugin.get_storage('config')
    users = config.get('users', {})
    if not users:
        return

    userid_list = users.keys()
    userid_list.insert(0, NULL_USER)
    choice = xbmcutils.select('请选择活动帐号', userid_list)
    if choice < 0:
        return

    config['current_user'] = userid_list[choice] if choice > 0 else None
    config.sync()

    xbmcutils.refresh()


@plugin.route('/users_list/')
def users_list():
    items = [{
        'label': '[COLOR FFFFFF00]增加帐号[/COLOR]',
        'path': plugin.url_for('add_user'),
        'is_playable': True,
        'properties': {'isPlayable': ''}
    }]

    config = plugin.get_storage('config')
    users = config.setdefault('users', {})
    for userid in users.keys():
        items.append({
            'label': userid,
                     'path': plugin.url_for('remove_user', userid=userid),
                     'is_playable': True,
                     'properties': {'isPlayable': ''},
            'context_menu': [(
                '[COLOR FFFFFF00]重新登录[/COLOR]',
                actions.background(
                    plugin.url_for('relogin', userid=userid))
            )],
            'replace_context_menu': True
        })

    return items


@plugin.route('/remove_user/<userid>/')
def remove_user(userid):
    if not xbmcutils.yesno('注销帐号', '是否注销帐号 %s？' % userid):
        return

    config = plugin.get_storage('config')
    users = config.setdefault('users', {})
    users.pop(userid, None)
    if config.get('current_user') == userid:
        config['current_user'] = users.keys()[0] if users else None
    config.sync()

    userdata = plugin.get_storage('userdata')
    userdata.pop(userid, None)
    userdata.sync()

    plugin.notify('帐号已经注销成功', delay=3000)
    xbmcutils.refresh()


@plugin.route('/add_user/')
def add_user():
    userid = (xbmcutils.keyboard(heading='请输入您的百度云帐号')
              or '').strip()
    if not userid:
        return

    config = plugin.get_storage('config')
    users = config.setdefault('users', {})
    if userid in users:
        plugin.notify('用户已存在', delay=2000)
        return

    password = (xbmcutils.keyboard(heading='请输入密码', hidden=True)
                or '').strip()
    if not password:
        return

    api = creaet_api_with_publickey()
    try:
        login_info = api.try_login(userid, password, on_verifycode)
    except Exception as e:
        plugin.log.info(traceback.format_exc())
        if isinstance(e, ClientApiError):
            e = e.get_errmsg()
        xbmcutils.show_msg('登录失败: %s' % e)
        return

    if not login_info:
        return

    _save_user_info(config, userid, password, login_info, api)

    plugin.notify('用户添加成功', delay=3000)
    xbmcutils.refresh()


@plugin.route('/relogin/<userid>/')
def relogin(userid):
    config = plugin.get_storage('config')
    users = config['users']
    old_password = users[userid]

    password = (xbmcutils.keyboard(old_password, '请输入密码', True) or '').strip()
    if not password:
        return

    api = creaet_api_with_publickey()
    try:
        login_info = api.try_login(userid, password, on_verifycode)
    except Exception as e:
        plugin.log.info(traceback.format_exc())
        if isinstance(e, ClientApiError):
            e = e.get_errmsg()
        xbmcutils.show_msg('登录失败: %s' % e)
        return

    if not login_info:
        return

    _save_user_info(config, userid, password, login_info, api)

    plugin.notify('用户登录成功', delay=3000)
    xbmcutils.refresh()


@plugin.route('/clear_cache/')
def clear_cache():
    plugin.clear_function_cache()
    plugin.notify('缓存清除完毕！'.encode('utf-8'))

_video_file_exts = None
_api_maps = {}
NULL_USER = '[ 空 ]'


def get_uk(userid):
    userdata = plugin.get_storage('userdata')
    user = userdata.setdefault(userid, {})
    if 'uk' in user:
        return user['uk']

    uk = get_api(userid).get_uk()
    user['uk'] = uk
    userdata.sync()

    return uk


def get_api(userid):
    global _api_maps
    if userid in _api_maps:
        return _api_maps[userid]

    api = creaet_api_with_publickey()
    userdata = plugin.get_storage('userdata')
    user = userdata.setdefault(userid, {})
    if 'session' in user:
        api.set_login_info(user['session'])

    _api_maps[userid] = api

    return api


def on_verifycode(imgurl, captcha_error=False):
    if captcha_error:
        plugin.notify('验证码不正确，请重新输入', delay=2000)

    win = CaptchaDialog('captcha.xml', plugin_path, imgurl=imgurl)
    try:
        win.doModal()
        input_text = win.get_text()
        if input_text:
            return input_text
    finally:
        del win


def _save_user_info(config, userid, password, login_info, api):
    users = config['users']
    users[userid] = password
    if not config.get('current_user'):
        config['current_user'] = userid

    ss = (login_info['bduss'], login_info[
          'uid'], login_info['ptoken'], login_info['stoken'])

    api.set_login_info(ss)

    userdata = plugin.get_storage('userdata')
    userdata[userid] = {'session': ss, 'session_time': time.time()}

    config.sync()
    userdata.sync()


def list_dir(userid=None, path='/'):
    if not userid:
        return []

    api = get_api(userid)

    entries = []
    for page in xrange(1, 21):
        tmp_entries = api.list_dir(path, page=page)
        entries.extend(tmp_entries)

        if len(tmp_entries) < 100:
            break

    dirs = []
    video_files = []
    # torrent_files = []
    subtitle_files = []
    # compresses_files = []
    other_files = []
    for entry in entries:
        filename = entry['server_filename']
        remote_path = entry.get('path').encode('utf-8')
        file_md5 = entry.get('md5')
        imgurl = ''
        if 'thumbs' in entry and 'url1' in entry['thumbs']:
            imgurl = entry['thumbs']['url1'].replace(
                'size=c140_u90', 'size=c300_u300')

        if str(entry['isdir']) == '1':
            dirs.append(filename)
        elif is_video(filename):
            video_files.append((filename, remote_path, imgurl, file_md5))
        # elif is_torrent(filename):
        #     torrent_files.append((filename, dlink, imgurl,file_md5))
        elif is_subtitle(filename):
            subtitle_files.append((filename, remote_path, imgurl, file_md5))
        # elif is_compressed(filename):
        #     compresses_files.append((filename, dlink, imgurl,file_md5))
        else:
            other_files.append((filename, remote_path, imgurl, file_md5))

    def get_context_menu(userid, path):
        if isinstance(path, unicode):
            path = path.encode('utf-8')

        return [(
            '[COLOR FFFFFF00]删除[/COLOR]',
            actions.background(
                plugin.url_for('delete_path', userid=userid, path=path))
        )]

    def get_subtitle(name):
        filename, _, ext = name.rpartition('.')
        for subfile, subfile_dlink, _, _ in subtitle_files:
            if (subfile.startswith(filename + '.')
                    and '.' not in subfile[len(filename) + 1:]):
                return subfile_dlink

        return ''

    items = [{
        'label': '[ %s ]' % name,
        'path': plugin.url_for('list_user_dir', userid=userid,
                               path=(path + '/' + name).encode('utf-8')),
        'context_menu': get_context_menu(userid, path + '/' + name)
    } for name in dirs]

    if video_files:
        prefer_transcode = plugin.get_setting('prefer_transcode', bool)
        items.extend([{
            'label': name,
            'path': (plugin.url_for('play_transcode_video',
                                    userid=userid,
                                    path=(path + '/' + name).encode('utf-8'),
                                    md5=file_md5,
                                    name=name.encode('utf-8'),
                                    subtitle=get_subtitle(name))
                     if prefer_transcode else
                     plugin.url_for(
                         'play_path', userid=userid, path=remote_path,
                         md5=file_md5,
                         name=name.encode('utf-8'),
                         subtitle=get_subtitle(name),
                         resolved=True)),
            'is_playable': True,
            'thumbnail': imgurl or api.get_thumbnail_url(path + '/' + name),
            'properties': {'isPlayable': '' if prefer_transcode else 'true'},
            'context_menu': [(
                '[COLOR FFFFFF00]播放原始视频[/COLOR]' if prefer_transcode
                else '[COLOR FFFFFF00]播放转码视频[/COLOR]',
                actions.background(
                    plugin.url_for(
                        'play_path',
                        userid=userid,
                        path=remote_path,
                        md5=file_md5,
                        name=name.encode('utf-8'),
                        subtitle=get_subtitle(name))
                    if prefer_transcode
                    else plugin.url_for(
                        'play_transcode_video',
                        userid=userid,
                        path=(path + '/' + name).encode('utf-8'),
                        md5=file_md5,
                        name=name.encode('utf-8'),
                        subtitle=get_subtitle(name))
                )
            ), (
                '[COLOR FFFFFF00]选择转码格式播放[/COLOR]',
                actions.background(plugin.url_for(
                    'play_transcode_video_select_type',
                    userid=userid,
                    path=(path + '/' + name).encode('utf-8'),
                    md5=file_md5,
                    name=name.encode('utf-8'),
                    subtitle=get_subtitle(name)))
            )] + get_context_menu(userid, path + '/' + name)
        } for name, remote_path, imgurl, file_md5 in video_files])

    # if torrent_files:
    #     items.extend([{
    #         'label': name,
    #         'path': plugin.url_for('play_torrent', userid=userid, url=dlink),
    #         'is_playable': True,
    #         'properties': {'isPlayable': ''},
    #         'context_menu': get_context_menu(userid, path + '/' + name)
    #     } for name, dlink, imgurl in torrent_files])

    # if compresses_files:
    #     items.extend([{
    #         'label': name,
    #         'path': plugin.url_for('show_compressed_file',
    #                                name=name.encode('utf-8'),
    #                                url=dlink),
    #         'context_menu': get_context_menu(userid, path + '/' + name)
    #     } for name, dlink, imgurl in compresses_files])

    if other_files and plugin.get_setting('show_non_video_files', bool):
        items.extend([{
            'label': name,
            'path': '',
            'thumbnail': imgurl,
            'is_playable': True,
            'properties': {'isPlayable': ''},
            'context_menu': get_context_menu(userid, path + '/' + name),
            'replace_context_menu': True
        } for name, remote_path, imgurl, file_md5 in other_files])

    return items


def is_video(filename):
    global _video_file_exts
    if not _video_file_exts:
        _video_file_exts = ['.' + ext for ext in plugin.get_setting(
            'video_file_exts', str).split(',')]

    filename = filename.lower()
    return any(filename.endswith(ext) for ext in _video_file_exts)


def is_subtitle(filename):
    filename = filename.lower()
    return any(filename.endswith(ext) for ext in (
        '.srt', '.sub', '.ssa', '.smi', '.ass'))


def is_torrent(filename):
    return filename.lower().endswith('.torrent')


def creaet_api_with_publickey():
    api = ClientAPI()
    api.set_public_key(*_get_public_key())
    return api


@plugin.cached(360)
def _get_public_key():
    from simple_rsa import get_public_key
    cert = ClientAPI().get_cert()[0]
    return get_public_key(cert)


@plugin.cached(360)
def get_dlink(userid, path):
    api = get_api(userid)
    info = api.get_filemetas(path)['info']
    return info[0]['dlink']


def get_default_userid():
    return plugin.get_storage('config').get('current_user')


def list_mynotes(userid=None):
    if not userid:
        return []

    api = get_api(userid)
    categories = [c for c in api.list_note_categories()
                  if c['title'] == 'xbmc_bth']
    if not categories:
        res = api.add_category('xbmc_bth')
        category_id = res[0]['_key']
    else:
        category_id = categories[0]['_key']

    notes = api.list_note(category_id)
    if not notes:
        api.add_note('#示例\nhttp://pan.baidu.com/share/home?uk=791642990',
                     category_id)
        notes = api.list_note(category_id)

    items = []
    for note in notes:
        name = note['title']
        content = note['content']
        if content.startswith('#'):
            firstline, _, content = content.partition('\n')
            firstline = firstline.lstrip('#').strip()
            if firstline:
                name = firstline

        items.append({
            'label': name,
            'path': plugin.url_for(
                'show_note_btih', userid=userid, note_id=note['_key'],
                category_id=category_id),
            'is_playable': True,
            'properties': {'isPlayable': ''}
        })

    return items


# def list_dynamic_list(userid, page=0):
#     api = get_api(userid)

#     uk = get_uk(userid)
#     records, total_count = api.get_dynamic_list(uk, page * 50, 50, 1)

#     items = [{
#         'label': video['server_filename'],
#         'path': plugin.url_for('play_stream', url=video['dlink']),
#         'is_playable': True,
#         'thumbnail': video.get('thumburl')
#     } for record in records for video in record['filelist']]

#     return items, total_count


def log(*args):
    plugin.log.info(args[0] if len(args) == 1 else args)


def quote_url(url):
    return quote_plus(url, '')


def is_compressed(filename):
    name = filename.lower()
    return name.endswith('.zip') or name.endswith('.rar')

reload(sys)
sys.setdefaultencoding('utf-8')

register_modules()


if __name__ == '__main__':
    plugin.run()
