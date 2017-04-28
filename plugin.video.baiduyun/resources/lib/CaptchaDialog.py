#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import xbmc, xbmcgui
import xbmcvfs
import utils

CTRL_ID_BACKSPACE = 8
CTRL_ID_OK = 10
CTRL_ID_TEXT = 1
CTRL_ID_IMG = 2
CTRL_ID_REFRESH = 300

ACTION_PREVIOUS_MENU = (10, 92)


class CaptchaDialog(xbmcgui.WindowXMLDialog):

    def __init__(self, strXMLname, strFallbackPath, defaultSkin='Default',
                 forceFallback=False, imgurl=''):
    # def __init__( self, *args, **kwargs ):
        # Changing the three varibles passed won't change, anything
        # Doing strXMLname = "bah.xml" will not change anything.
        # don't put GUI sensitive stuff here (as the xml hasn't been read yet
        # Idea to initialize your variables here
        self._imgurl = imgurl
        self.input_text = ''
        self._ok = False
        self._tmp_imgfile = 'special://temp/baidu_captcha.jpg'
        # super(MyFirstWinXML, self).__init__(self, *args)

    def __del__(self):
        tmp_imgfile = self._tmp_imgfile
        if xbmcvfs.exists(self._tmp_imgfile):
            try:
                xbmcvfs.delete(tmp_imgfile)
            except:
                pass

    def _download_img(self):
        imgdata = utils.fetch_url(self._imgurl, timeout=10)
        xbmcvfs.File(self._tmp_imgfile, 'w').write(imgdata)

    def onInit(self):
        self._download_img()
        self.getControl(CTRL_ID_IMG).setImage(self._tmp_imgfile)

    def get_text(self):
        if self._ok:
            return self.input_text

    def onAction(self, action):
        # Same as normal python Windows.
        if action in ACTION_PREVIOUS_MENU:
            self.close()

    def onClick(self, controlID):
        """
            Notice: onClick not onControl
            Notice: it gives the ID of the control not the control object
        """
        input_text = self.input_text
        xbmc.log(str(controlID))

        if CTRL_ID_OK == controlID:
            if len(self.input_text) < 4:
                utils.show_msg('验证码必须是4位！')
                return
            self._ok = True
            self.close()
        elif not input_text and CTRL_ID_BACKSPACE == controlID:
            input_text = input_text[:-1]
            self.input_text = input_text
            self.getControl(CTRL_ID_TEXT).setLabel(input_text)
        elif CTRL_ID_REFRESH == controlID:
            self._download_img()
            img_control = self.getControl(CTRL_ID_IMG)
            img_control.setImage('')
            img_control.setImage(self._tmp_imgfile)
            # self.getControl(CTRL_ID_IMG).setImage(
            #     self._imgurl + '&t=%s' % time.time())
        elif len(input_text) < 4 and (ord('0') <= controlID <= ord('9')
                                      or ord('A') <= controlID <= ord('Z')):
                char = chr(controlID)
                xbmc.log(char)
                input_text += char
                self.input_text = input_text
                self.getControl(CTRL_ID_TEXT).setLabel(input_text)

    def onFocus(self, controlID):
        pass
