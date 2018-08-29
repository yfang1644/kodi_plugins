#coding=utf-8
from xbmcswift2 import xbmc, xbmcgui

class LoginDialog(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.cptloc = kwargs.get('captcha')
        self.img = xbmcgui.ControlImage(400, 10, 400, 100,self.cptloc)
        self.addControl(self.img)
        self.kbd = xbmc.Keyboard()
        #self.kbd.setHeading(u'请输入验证码')

    def get(self):
        self.show()
        self.kbd.doModal()
        if (self.kbd.isConfirmed()):
            text = self.kbd.getText()
        else:
            text = False
        self.close()
        return text
