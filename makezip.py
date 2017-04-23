#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File Name: makezip.py
# Author: Fang Yuan (yfang@nju.edu.cn)
# Created Time: Tue 28 Feb 2017 04:00:55 PM CST

import os
import sys
import re
import zipfile
import shutil


def release(plugin, version):

    # zip repo
    zipname = '%s/%s-%s.zip' % (plugin, plugin, version)
    zipcmd = 'zip -r ' + zipname + ' ' + plugin
    os.system(zipcmd)

def getVersion(plugin):
    name = '%s/addon.xml' % plugin
    cont = open(name).read()
    addon = re.findall('<addon.*?version="(.*?)"', cont, re.DOTALL)
    if addon:
        return addon[0]


plugin = sys.argv[1].rstrip('/')

version = getVersion(plugin)
release(plugin, version)
