#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc as _xbmc
from xbmcswift2 import xbmc, xbmcgui


def keyboard(default='', heading='', hidden=False):

    if hidden:
        kb = _xbmc.Keyboard(default, heading, hidden)
    else:
        try:
            import ChineseKeyboard
            kb = ChineseKeyboard.Keyboard(default, heading)
        except:
            kb = xbmc.Keyboard(default, heading)

    xbmc.sleep(1000)
    kb.doModal()
    if (kb.isConfirmed()):
        return kb.getText()


def show_msg(msg, title='提示'):
    return xbmcgui.Dialog().ok(title, msg)


def select(title, items_list):
    return xbmcgui.Dialog().select(title, items_list)


def yesno(title, *args):
    return xbmcgui.Dialog().yesno(title, *args)


def refresh():
    xbmc.executebuiltin('Container.Refresh')


def update_plugin_url(plugin_url):
    xbmc.executebuiltin('Container.Update(%s)' % plugin_url)
