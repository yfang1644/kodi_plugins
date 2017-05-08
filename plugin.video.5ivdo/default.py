#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib2
import urllib
import re
import sys
import gzip
import StringIO
import time
import cookielib
import dr

# 5ivdo(5ivdo) by sand, 2015

# Plugin constants
__addon__   = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonid__   = __addon__.getAddonInfo('id')

UserAgent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

DP = xbmcgui.DialogProgress()


def Get5ivdoData(url):
    req = urllib2.Request(url)
    req.add_header('User_Agent', UserAgent)
    response = urllib2.urlopen(req)
    httpdata = response.read()
    httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
    response.close()
    return httpdata


def showmenu(purl, pvmode='0'):
    link = Get5ivdoData(purl)
    match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url><thumb>(.+?)</thumb>').findall(link)
    for imode, ititle, iurl, ithumb in match:
        li = xbmcgui.ListItem(ititle, iconImage='', thumbnailImage=ithumb)
        u = sys.argv[0]+"?mode="+urllib.quote_plus(imode)+"&url="+urllib.quote_plus('http://www.5ivdo.com/' + iurl)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, True)
    if pvmode != '0':
        xbmc.executebuiltin('Container.SetViewMode(' + pvmode + ')')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def PlayMenu(pmenu):
    iparams = genparamdata(pmenu)
    dialog = xbmcgui.Dialog()
    PlayVideo(iparams)


def showdata(purl):
    imultesite = ''
    isinglemem = ''
    ipara = ''
    dialog = xbmcgui.Dialog()
    link = Get5ivdoData(purl)
    match0 = re.compile('<head>(.+?)</head>').search(link).group(1)
    if match0.find('multesite') > 0:
        imultesite = re.compile('<multesite>(.+?)</multesite>').findall(match0)[0]
    if match0.find('singlemem') > 0:
        isinglemem = re.compile('<singlemem>(.+?)</singlemem>').findall(match0)[0]
    if imultesite == 'TRUE':
        match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url>(.+?)\n').findall(link)
        listA = []
        listP = []
        for imode, ititle, iurl, iother in match:
            ipara = ''
            if iother.find('thumb') > 0:
                ithumb = re.compile('<thumb>(.+?)</thumb>').findall(iother)[0]
            else:
                ithumb = ''
            if iother.find('matchstr') > 0:
                iimatchstr = re.compile('<matchstr>(.+?)</matchstr>').findall(iother)[0]
            else:
                iimatchstr = ''
            if iother.find('mflag') > 0:
                iimflag = re.compile('<mflag>(.+?)</mflag>').findall(iother)[0]
            else:
                iimflag = ''
            if iother.find('sub') > 0:
                iisub = re.compile('<sub>(.+?)</sub>').findall(iother)[0]
            else:
                iisub = ''
            if iother.find('prefix') > 0:
                iiprefix = re.compile('<prefix>(.+?)</prefix>').findall(iother)[0]
                ipara = ipara + "&prefix="+urllib.quote_plus(iiprefix)
            if iother.find('options') > 0:
                iioptions = re.compile('<options>(.+?)</options>').findall(iother)[0]
                ipara = ipara + "&options="+urllib.quote_plus(iioptions)
            ui = "?name="+urllib.quote_plus(ititle)+"&mode="+urllib.quote_plus(imode)+"&matchstr="+urllib.quote_plus(iimatchstr)+"&mflag="+urllib.quote_plus(iimflag)+"&url="+urllib.quote_plus(iurl)+"&sub="+urllib.quote_plus(iisub)+ipara
            u = sys.argv[0]+ui
            if isinglemem == 'TRUE':
                listA.append(ititle)
                listP.append(ui)
            else:
                li = xbmcgui.ListItem(ititle, iconImage='', thumbnailImage=ithumb)
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        if isinglemem == 'TRUE':
            if len(match) > 1:
                isel = dialog.select(__addonname__, listA)
            else:
                isel = 0
            if isel >= 0:
                PlayMenu(listP[isel])
        else:
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
        ipara = ''
        if match0.find('matchstr') > 0:
            imatchstr = re.compile('<matchstr>(.+?)</matchstr>').findall(match0)[0]
        if match0.find('mflag') > 0:
            imflag = re.compile('<mflag>(.+?)</mflag>').findall(match0)[0]
        if match0.find('sub') > 0:
            isub = re.compile('<sub>(.+?)</sub>').findall(match0)[0]
        else:
            isub = ''
        if match0.find('prefix') > 0:
            iiprefix = re.compile('<prefix>(.+?)</prefix>').findall(match0)[0]
            ipara = ipara + "&prefix="+urllib.quote_plus(iiprefix)
        if match0.find('options') > 0:
            iioptions = re.compile('<options>(.+?)</options>').findall(match0)[0]
            ipara = ipara + "&options="+urllib.quote_plus(iioptions)
        match = re.compile('<mode>(.+?)</mode><title>(.+?)</title><url>(.+?)</url><thumb>(.+?)</thumb>').findall(link)
        for imode, ititle, iurl, ithumb in match:
            li = xbmcgui.ListItem(ititle, iconImage='', thumbnailImage=ithumb)
            u = sys.argv[0]+"?name="+urllib.quote_plus(ititle)+"&mode="+urllib.quote_plus(imode)+"&matchstr="+urllib.quote_plus(imatchstr)+"&mflag="+urllib.quote_plus(imflag)+"&url="+urllib.quote_plus(iurl)+"&sub="+urllib.quote_plus(isub) + ipara
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, li, False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


def rootList():
    irootfile = None
    link = dr.GetHttpData('http://www.5ivdo.net/index.xml')
    match0 = re.compile('<config>(.+?)</config>', re.DOTALL).search(link)
    match = re.compile('<name>(.+?)</name><value>(.+?)</value>').findall(match0.group(1))
    for iname, ivalue in match:
        if iname == 'rootfile':
            irootfile = ivalue

    showmenu(irootfile, '500')


def urlExists(url):
    try:
        resp = urllib2.urlopen(url)
        result = True
        resp.close()
    except urllib2.URLError, e:
        result = False
    return result


def playRAW(pname, purl):
    DP.update(80)
    playlist = xbmc.PlayList(1)
    playlist.clear()
    listitem = xbmcgui.ListItem(pname)
    listitem.setInfo(type="Video", infoLabels={"Title": pname})
    playlist.add(purl, listitem)
    xbmc.Player().play(playlist)


def sohuPlayLive(pname, purl, pthumb):
    DP.update(20)
    link = dr.GetHttpData(purl)
    match = re.compile(',"live":"(.+?)",').findall(link)
    if len(match) > 0:
        link2 = dr.GetHttpData(match[0])
        match2 = re.compile(',"url":"(.+?)",').findall(link2)
        if len(match2) > 0:
            playRAW(pname, match2[0])
    DP.close()


def sohuPlayVideo(pname, purl, pthumb):
    link = dr.GetHttpData(purl)
    match = re.compile('"clipsURL"\:\["(.+?)"\]').findall(link)
    if len(match) == 0:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '无法播放，请换用其他网站重试。')
        return
    paths = match[0].split('","')
    match = re.compile('"su"\:\["(.+?)"\]').findall(link)
    if len(match) == 0:
        dialog = xbmcgui.Dialog()
        ok = dialog.ok(__addonname__, '无法播放，请换用其他网站重试。')
        return
    newpaths = match[0].split('","')
    urls = []
    for i in range(0, len(paths)):
        p_url = 'http://data.vod.itc.cn/?prot=2&file='+paths[i].replace('http://data.vod.itc.cn','')+'&new='+newpaths[i]
        link = dr.GetHttpData(p_url)
        # http://newflv.sohu.ccgslb.net/|623|116.14.234.161|Googu7gm-8WjRTd5ZfBVPIfrtRtLE5Cn|1|0
        key = link.split('|')[3]
        url = link.split('|')[0].rstrip("/")+newpaths[i]+'?key='+key
        urls.append(url)
    if DP.iscanceled():
        DP.close()
        return
    else:
        DP.update(50)
    stackurl = 'stack://' + ' , '.join(urls)
    listitem = xbmcgui.ListItem(pname)
    listitem.setInfo(type="Video", infoLabels={"Title": pname})
    xbmc.Player().play(stackurl, listitem)


def Getmatch1(purl, pmatchstr):
    link = dr.GetHttpData(purl)
    match = re.compile(pmatchstr).findall(link)
    return match


def Getmatch2(purl, matchstr, match2str):
    link = dr.GetHttpData(purl)
    matchA = re.compile(match2str).findall(link)
    match = []
    if matchA:
        match = re.compile(matchstr).findall(matchA[0])
    return match


def Getmatch3(purl, pmatchstr, pgroupstr, pgroupid):
    rt = []
    iflag = 'N'
    link = dr.GetHttpData(purl)
    match = re.compile(pmatchstr).findall(link)
    for a in match:
        ig = re.compile(pgroupstr).findall(a)
        if len(ig) > 0:
            if pgroupid == ig[0]:
                iflag = 'Y'
            else:
                iflag = 'N'
            continue
        if iflag == 'Y':
            rt.append(a)
    return rt

#   Addon = xbmcaddon.Addon(id='plugin.video.5ivdo')
#   xbmc.executebuiltin('XBMC.Notification("%s","%s",%s,"%s")' % (mHead, mMSG, 3000, Addon.getAddonInfo('icon').encode('utf-8')))

def parsepmod(pPARMS):
    ipmod = ''
    ioptions = pPARMS['options']
    isub = pPARMS['sub']
    if ioptions.find('LIVE') > 0:
        ipmod = ipmod + '|LIVE'
    if ioptions.find('SOHU') > 0:
        ipmod = ipmod + '|SOHU'
    if ioptions.find('FIRSTONE') > 0:
        ipmod = ipmod + '|FIRSTONE'
    if ioptions.find('NOSTACK') > 0:
        ipmod = ipmod + '|NOSTACK'
    if ioptions.find('RAW') > 0:
        ipmod = ipmod + '|RAW'
    if ioptions.find('<match2str>') > 0:
        ipmod = ipmod + '|MATCH2STR'
    if ioptions.find('<groupstr>') > 0:
        ipmod = ipmod + '|GROUPSELECT'
    if len(pPARMS['sub']) > 0:
        ipmod = ipmod + '|SUB'
    if len(pPARMS['prefix']) > 0:
        ipmod = ipmod + '|PRE'
    return ipmod


def genparamdata(pmenustr=None):
    if pmenustr:
        params = pmenustr[1:]
    else:
        params = sys.argv[2][1:]
    params = dict(urllib2.urlparse.parse_qsl(params))

    iret = {}
    iret['thumb'] = params.get('thumb', '')
    iret['name'] = params.get('name')
    iret['matchstr'] = params.get('matchstr')
    iret['mflag'] = params.get('mflag')
    iret['url'] = params.get('url')
    iret['mode'] = params.get('mode')
    iret['sub'] = params.get('sub', '')
    iret['prefix'] = params.get('prefix', '')
    iret['options'] = ' ' + params.get('options', '')

    return iret


def playDR(pname, purl, pthumb):
    itype, iurl = dr.work(purl)
    DP.update(80)
    if itype in '|M3U8|SINGLE':
        playlist = xbmc.PlayList(1)
        playlist.clear()
        listitem = xbmcgui.ListItem(pname, thumbnailImage=pthumb)
        listitem.setInfo(type="Video", infoLabels={"Title": pname})
        playlist.add(iurl, listitem)
        xbmc.Player().play(playlist)
    elif itype in '|MULTI|':
        stackurl = 'stack://' + ' , '.join(iurl)
        listitem = xbmcgui.ListItem(pname)
        listitem.setInfo(type="Video", infoLabels={"Title": pname})
        xbmc.Player().play(stackurl, listitem)


def PlayVideo(pPARMs):
    name = pPARMs['name']
    url = pPARMs['url']
    matchstr = pPARMs['matchstr']
    multiflag = pPARMs['mflag']
    thumb = pPARMs['thumb']
    ioptions = pPARMs['options']
    pmod = parsepmod(pPARMs)

    DP.create('5iVDO 提示', '节目准备中 : ', pPARMs['name'] + ' ...')
    DP.update(10)

    if url[0:2] == 'DR':
        playDR(name, url, thumb)
    elif pmod.find('RAW') > 0:
        playRAW(name, url)
    elif pmod.find('SOHU') > 0:
        if pmod.find('LIVE') > 0:
            sohuPlayLive(name, url, thumb)
        else:
            sohuPlayVideo(name, url, thumb)
    else:
        urls = []
        if pmod.find('MATCH2STR') > 0:
            imatch = re.compile('<match2str>(.+?)</match2str>').findall(ioptions)
            match2str = imatch[0]
            match = Getmatch2(url, matchstr, match2str)
        elif pmod.find('GROUPSELECT') > 0:
            imatch = re.compile('<groupstr>(.+?)</groupstr>').findall(ioptions)
            groupstr = imatch[0]
            imatch = re.compile('<groupid>(.+?)</groupid>').findall(ioptions)
            groupid = imatch[0]
            match = Getmatch3(url, matchstr, groupstr, groupid)
        else:
            match = Getmatch1(url, matchstr)
        if len(match) == 0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(__addonname__, '播放地址已失效，请换用其他网站重试。')
            return
        for x in match:
            purl = x
            if pmod.find('SUB') > 0:
                imatch = re.compile('<from>(.+?)</from><to>(.+?)</to>').findall(pPARMs['sub'])
                subfrom = imatch[0][0]
                subto = imatch[0][1]
                purl = x.replace(subfrom, subto)
            if pmod.find('PRE') > 0:
                purl = pPARMs['prefix'] + purl
            urls.append(purl)

        if DP.iscanceled():
            DP.close()
            return
        else:
            DP.update(50)

        if multiflag == '1':
            playlist = xbmc.PlayList(1)
            playlist.clear()
            listitem = xbmcgui.ListItem(name)
            listitem.setInfo(type="Video", infoLabels={"Title": name})
            if pmod.find('FIRSTONE') > 0:
                playlist.add(urls[0], listitem)
            else:
                playlist.add(urls[len(urls)-1], listitem)
            xbmc.Player().play(playlist)
        else:
            if pmod.find('NOSTACK') > 0:
                playlist = xbmc.PlayList(1)
                playlist.clear()
                dialog = xbmcgui.Dialog()
                for i in range(0, len(urls)):
                    listitem = xbmcgui.ListItem(name)
                    listitem.setInfo(type="Video", infoLabels={"Title": name+" 第"+str(i+1)+"/"+str(len(urls))+" 节"})
                    playlist.add(urls[i], listitem)
                xbmc.Player().play(playlist)
            else:
                stackurl = 'stack://' + ' , '.join(urls)
                dialog = xbmcgui.Dialog()
                listitem = xbmcgui.ListItem(name)
                listitem.setInfo(type="Video", infoLabels={"Title": name})
                xbmc.Player().play(stackurl, listitem)


play_data = genparamdata()
mode = play_data['mode']

cj = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
opener.addheaders = [('Cookie', '__ysuid={0}'.format(time.time()))]
urllib2.install_opener(opener)
if mode is None:
    rootList()
elif mode == 'menu':
    showmenu(play_data['url'])
elif mode == 'data':
    showdata(play_data['url'])
elif mode == 'play':
    PlayVideo(play_data)
elif mode == 'diag':
    dialog = xbmcgui.Dialog()
    ok = dialog.ok(__addonname__, '开发阶段。')
