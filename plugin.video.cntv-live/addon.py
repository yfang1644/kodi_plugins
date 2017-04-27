# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import time
import re
import traceback
import urllib
import urllib2
import urlparse
try:
    import simplejson as jsonimpl
except ImportError:
    import json as jsonimpl

mainList = {
    'yangshi': '央视频道',
    'weishi': '卫视频道',
    'shuzi': '数字频道',
    'chengshi': '城市频道'
}

cityList = [{"area": "安徽", 'id': 'anhui', 'channel': []},
            {"area": "北京", 'id': 'beijing',
             'channel': [{"btv2": "BTV文艺"},
                         {"btv3": "BTV科教"},
                         {"btv4": "BTV影视"},
                         {"btv5": "BTV财经"},
                         {"btv6": "BTV体育"},
                         {"btv7": "BTV生活"},
                         {"btv8": "BTV青年"},
                         {"btv9": "BTV新闻"},
                         {"btvchild": "BTV卡酷少儿"},
                         {"btvjishi": "BTV纪实"},
                         {"btvInternational": "BTV国际"}]},
            {"area": "福建", 'id': 'fujian',
             'channel': [{"xiamen1": "厦门一套"},
                         {"xiamen2": "厦门二套"},
                         {"xiamen3": "厦门三套"},
                         {"xiamen4": "厦门四套"},
                         {"xiamenyidong": "厦门移动"}]},
            {"area": "甘肃", 'id': 'gansu',
             'channel': [{"jingcailanzhou": "睛彩兰州"}]},
            {"area": "广东", 'id': 'guangdong',
             'channel': [{"cztv1": "潮州综合"},
                         {"cztv2": "潮州公共"},
                         {"foshanxinwen": "佛山新闻综合"},
                         {"guangzhouxinwen": "广州新闻"},
                         {"guangzhoujingji": "广州经济"},
                         {"guangzhoushaoer": "广州少儿"},
                         {"guangzhouzonghe": "广州综合"},
                         {"guangzhooyingyu": "广州英语"},
                         {"shaoguanzonghe": "韶关综合"},
                         {"shaoguangonggong": "韶关公共"},
                         {"shenzhencjsh": "深圳财经"},
                         {"zhuhaiyitao": "珠海一套"},
                         {"zhuhaiertao": "珠海二套"}]},
            {"area": "广西", 'id': 'guangxi', 'channel': []},
            {"area": "河北", 'id': 'hebei',
             'channel': [{"hebeinongmin": "河北农民频道"},
                         {"hebeijingji": "河北经济"},
                         {"shijiazhuangyitao": "石家庄一套"},
                         {"shijiazhuangertao": "石家庄二套"},
                         {"shijiazhuangsantao": "石家庄三套"},
                         {"shijiazhuangsitao": "石家庄四套"},
                         {"xingtaizonghe": "邢台综合"},
                         {"xingtaishenghuo": "邢台生活"},
                         {"xingtaigonggong": "邢台公共"},
                         {"xingtaishahe": "邢台沙河"}]},
            {"area": "黑龙江", 'id': 'heilongjiang',
             'channel': [{"haerbinnews": "哈尔滨新闻综合"}]},
            {"area": "湖北", 'id': 'hubei',
             'channel': [{"hubeidst": "湖北电视台综合频道"},
                         {"hubeigonggong": "湖北公共"},
                         {"hubeijiaoyu": "湖北教育"},
                         {"hubeitiyu": "湖北体育"},
                         {"hubeiyingshi": "湖北影视"},
                         {"hubeijingshi": "湖北经视"},
                         {"hubeigouwu": "湖北购物"},
                         {"jznews": "荆州新闻频道"},
                         {"wuhanetv": "武汉教育"},
                         {"jzlongs": "湖北垄上频道"},
                         {"xiangyangtai": "襄阳广播电视台"}]},
            {"area": "吉林", 'id': 'jilin',
             'channel': [{"yanbianguangbo": "延边卫视视频广播"},
                         {"yanbianam": "延边卫视AM"},
                         {"yanbianfm": "延边卫视FM"}]},
            {"area": "江苏", 'id': 'jiangsu',
             'channel': [{"nanjingnews": "南京新闻"},
                         {"nantongxinwen": "南通新闻频道"},
                         {"nantongshejiao": "南通社教频道"},
                         {"nantongshenghuo": "南通生活频道"},
                         {"wuxixinwenzonghe": "无锡新闻综合"},
                         {"wuxidoushizixun": "无锡都市资讯"},
                         {"wuxiyuele": "无锡娱乐"},
                         {"wuxijingji": "无锡经济"},
                         {"wuxiyidong": "无锡移动"},
                         {"wuxishenghuo": "无锡生活"}]},
            {"area": "江西", 'id': 'jiangxi',
             'channel': [{"ganzhou", "赣州新闻综合"},
                         {"nanchangnews": "南昌新闻"}]},
            {"area": "辽宁", 'id': 'liaoning',
             'channel': [{"daliannews": "大连一套"},
                         {"liaoningds": "辽宁都市"}]},
            {"area": "内蒙古", 'id': 'neimenggu',
             'channel': [{"neimenggu2", "蒙语频道"},
                         {"neimengwh": "内蒙古文化频道"}]},
            {"area": "山东", 'id': 'shandong',
             'channel': [{"jinannews": "济南新闻"},
                         {"qingdaonews": "青岛新闻综合"},
                         {"yantaixinwenzonghe": "烟台新闻综合"},
                         {"yantaixinjingjishenghuo": "烟台经济生活"},
                         {"yantaigonggong": "烟台公共频道"}]},
            {"area": "陕西", 'id': 'shaanxi',
             'channel': [{"xiannews": "西安新闻"}]},
            {"area": "上海", 'id': 'shanghai',
             'channel': [{"shnews": "上海新闻综合"}]},
            {"area": "四川", 'id': 'sichuan',
             'channel': [{"cdtv1": "成都新闻综合"},
                         {"cdtv2new": "成都经济资讯服务"},
                         {"cdtv5": "成都公共"}]},
            {"area": "天津", 'id': 'tianjin',
             'channel': [{"tianjin2": "天津2套"},
                         {"tianjinbh": "滨海新闻综合"},
                         {"tianjinbh2": "滨海综艺频道"}]},
            {"area": "西藏", 'id': 'xizang',
             'channel': [{"xizang2": "藏语频道"}]},
            {"area": "新疆", 'id': 'xinjiang',
             'channel': [{"xjtv2": "维语新闻综合"},
                         {"xjtv3": "哈语新闻综合"},
                         {"xjtv5": "维语综艺"},
                         {"xjtv8": "哈语综艺"},
                         {"xjtv9": "维语经济生活"}]},
            {"area": "云南", 'id': 'yunnan',
             'channel': [{"lijiangnews": "丽江新闻综合频道"},
                         {"lijiangpublic": "丽江公共频道"}]},
            {"area": "浙江", 'id': 'zhejiang',
             'channel': [{"nbtv1": "宁波一套"},
                         {"nbtv2": "宁波二套"},
                         {"nbtv3": "宁波三套"},
                         {"nbtv4": "宁波四套"},
                         {"nbtv5": "宁波五套"}]},
            ]

cctvList = [["cctv1", "1-综合"],
            ["cctv2", "2-财经"],
            ["cctv3", "3-综艺"],
            ["cctv4", "4-国际(亚洲)"],
            ["cctveurope", "4-国际(欧洲)"],
            ["cctvamerica", "4-国际(美洲)"],
            ["cctv5", "5-体育"],
            ["cctv5plus", "5-赛事"],
            ["cctv6", "6-电影"],
            ["cctv7", "7-军事农业"],
            ["cctv8", "8-电视剧"],
            ["cctv9", "CCTV-NEWS"],
            ["cctvjilu", "9-纪录"],
            ["cctvdocumentary", "9-纪录(英语)"],
            ["cctv10", "10-科教"],
            ["cctv11", "11-戏曲"],
            ["cctv12", "12-社会与法"],
            ["cctv13", "13-新闻"],
            ["cctvchild", "14-少儿"],
            ["cctv15", "15-音乐"]]

weishList = [["anhui", "安徽卫视"],
             ["btv1", "北京卫视"],
             ["bingtuan", "兵团卫视"],
             ["chongqing", "重庆卫视"],
             ["dongfang", "东方卫视"],
             ["dongnan", "东南卫视"],
             ["gansu", "甘肃卫视"],
             ["guangdong", "广东卫视"],
             ["guangxi", "广西卫视"],
             ["guizhou", "贵州卫视"],
             ["hebei", "河北卫视"],
             ["henan", "河南卫视"],
             ["heilongjiang", "黑龙江卫视"],
             ['hnss', '三沙卫视'],
             ["hubei", "湖北卫视"],
             ["hunan", "湖南卫视"],
             ["jilin", "吉林卫视"],
             ["jiangsu", "江苏卫视"],
             ["jiangxi", "江西卫视"],
             ["kangba", "康巴卫视"],
             ["liaoning", "辽宁卫视"],
             ["travel", "旅游卫视"],
             ["neimenggu", "内蒙古卫视"],
             ["ningxia", "宁夏卫视"],
             ["qinghai", "青海卫视"],
             ["sdetv", "山东教育台"],
             ["shandong", "山东卫视"],
             ["shan1xi", "山西卫视"],
             ["shan3xi", "陕西卫视"],
             ["shenzhen", "深圳卫视"],
             ["sichuan", "四川卫视"],
             ["tianjin", "天津卫视"],
             ["xizang", "西藏卫视"],
             ["xiamen", "厦门卫视"],
             ["xianggangweishi", "香港卫视"],
             ["xinjiang", "新疆卫视"],
             ["yanbian", "延边卫视"],
             ["yunnan", "云南卫视"],
             ["zhejiang", "浙江卫视"]]

addon = xbmcaddon.Addon()
addon_name = addon.getAddonInfo("name")
addon_path = xbmc.translatePath(addon.getAddonInfo("path"))
addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, "movies")

TIMEOUT_S = 2.0


def getHttp(url):
    resp = urllib2.urlopen(url, timeout=TIMEOUT_S)
    data = resp.read()
    data = data.decode('utf-8')
    resp.close()

    branch = re.compile('/cache.+\n').findall(data)
    host = re.compile('(http.+//.+?)/').findall(url)

    try:
        data = host[0] + branch[0]
    except:
        return url
    if data.find('m3u8') >= 0:
        return data
    else:
        return url


def showNotification(stringID):
    xbmc.executebuiltin("Notification({0},{1})".format(addon_name, addon.getLocalizedString(stringID)))


def getQualityRange(quality):
    if quality == "100-300": #Hooray for efficiency!
        return "100-300"
    return "300-500"


def fixURL(tmpurl):
#    tmpurl = tmpurl.replace("vtime.cntv.cloudcdn.net:8000", "vtime.cntv.cloudcdn.net") #Global (HDS/FLV) - wrong port
#    tmpurl = tmpurl.replace("tv.fw.live.cntv.cn", "tvhd.fw.live.cntv.cn") #China - 403 Forbidden
    return tmpurl


def tryStream(jsondata, subkey, type):
    print("Trying stream {0}".format(subkey))

    if subkey in jsondata[type] and jsondata[type][subkey] != "":
        try:
            tmpurl = jsondata[type][subkey]
            tmpurl = fixURL(tmpurl)

            if tmpurl[:7] != 'http://':
                tmpurl = 'http://' + tmpurl
            tmpurl = tmpurl.replace(' ', '')

            req = urllib2.Request(tmpurl)
            conn = urllib2.urlopen(req, timeout=TIMEOUT_S)
            conn.read(8) #Try reading a few bytes

            return tmpurl
        except Exception:
            print("{0} failed.".format(subkey))
            print(traceback.format_exc())

    return None


def tryHDSStream(jsondata, streamName):
    if streamName in jsondata["hds_url"]:
        url = jsondata["hds_url"][streamName]
        url = url + "&hdcore=2.11.3"

        return url


def programList(city):
    prog_api = 'http://api.cntv.cn/epg/Epg24h?serviceId=channel&t=jsonp&cb=%s=&c=%s'
    resp = urllib2.urlopen(prog_api % (city, city))
    data = resp.read()
    data = data.decode('utf-8').encode('utf-8', 'ignore')
    jsdata = jsonimpl.loads(data[data.find('=(')+2:-2])
    info = ''
    try:
        jsprog = jsdata['programs']
        for item in jsprog[:8]:    # list recent 8 programs
            begin = time.localtime(item['startTime'])
            end = time.localtime(item['endTime'])
            title = item['ptitle']
            info += '%02d:%02d--' % (begin[3], begin[4])
            info += '%02d:%02d    ' % (end[3], end[4])
            info += title + '\n'
    except:
        pass

    return info


def addStream(channelID, channelName, mode='?stream='):
    thumb = addon_path + '/resources/media%s.png' % channelID
    info = programList(channelID)
    li = xbmcgui.ListItem(channelName, iconImage=thumb)
    li.setInfo(type='Video',
               infoLabels={'Title': channelName, 'Plot': info})
    u = sys.argv[0] + mode + channelID + '&thumb=' + thumb
    u += '&title=' + channelName
    xbmcplugin.addDirectoryItem(addon_handle, u, li)


def addCity(cityID, cityName):
    thumb = addon_path + '/resources/media/%s.png' % cityID
    li = xbmcgui.ListItem(cityName, iconImage=thumb)
    u = sys.argv[0] + '?city=' + cityID + '&thumb=' + thumb
    xbmcplugin.addDirectoryItem(addon_handle, u, li, isFolder=True)


class XBMCPlayer(xbmc.Player):
    def __init__(self, *args):
        self.channel = 'cctv00'
        self.media_ended = False
        self.media_stopped = False

        pass
        xbmc.log('#=#=#=# '+ self.channel + ' XBMCPlayer Initialized #=#=#=#')

    def __del__(self):
        xbmc.log('#=#=#=# '+ self.channel + ' XBMCPlayer Destructed #=#=#=#')

    def nPlayBackPaused(self):
        xbmc.log('#=#=#=# Status: ' + self.channel + ' Playback Paused #=#=#=#')

    def onPlayBackResumed(self):
        xbmc.log('#=#=#=# Status: ' + self.channel + ' Playback Resumed #=#=#=#')

    def onPlayBackStarted(self):
        # Will be called when xbmc starts playing a file
        xbmc.log('#=#=#=# Status: ' + self.channel + ' Playback Started #=#=#=#')
        self.media_ended = False
        self.media_stopped = False

    def onPlayBackEnded(self):
        # Will be called when xbmc ended playing a file
        xbmc.log('#=#=#=# Status: ' + self.channel + ' Playback Ended, #=#=#=#')
        self.media_ended = True
        # let treated media_ended the same as media_stopped for now
        self.media_stopped = True

    def onPlayBackStopped(self):
        # Will be called when user stops xbmc playing a file
        xbmc.log('#=#=#=# Status: ' + self.channel + ' Playback Stopped #=#=#=#')
        self.media_stopped = True
        # self.stop()


class XBMCMonitor(xbmc.Monitor):
    def __init__(self, *args):
        pass
        xbmc.log("#=#=#=# Monitor initialized  #=#=#=#")

    def __del__(self):
        xbmc.log("#=#=#=# Monitor destructed #=#=#=#")

    def abortRequested(self):
        # Returns True if abort has been requested.
        xbmc.log("#=#=#=# Status: ** abort *** has been requestd #=#=#=#")


def cn_time_s():  # return CST (China Standard Time) in seconds
    lc_time = time.localtime()
    gm_time_s = time.mktime(time.gmtime())
    return gm_time_s + (8 - lc_time.tm_isdst)*3600 # CST = GMT + 8h, tm_isdst = {1,0,-1}


def cntvReplay(ch, title, thumb):
    b_url = 'http://v.cctv.com/live_back/nettv_%s/%s-' % (ch, ch)
    player = XBMCPlayer()
    monitor = XBMCMonitor()

    while(not player.media_stopped):
        cur = cn_time_s()
        hr = time.strftime("%Y-%m-%d-%H", time.localtime(cur-600))
        seg = '-%03d.mp4' % (int((time.strftime("%M", time.localtime(cur-600))))/5+1)
        url = b_url + hr + seg + '?wsiphost=local'
        li = xbmcgui.ListItem('央视重播', iconImage=thumb, thumbnailImage=thumb)
        li.setInfo(type='Video', infoLabels={"Title": title})
        player.play(item=url, listitem=li)
        for x in range(1, 300):
            if monitor.waitForAbort(1) or player.media_stopped: # Sleep/wait for abort for 1 second
                xbmc.log('#=#=#=# ' + ch + ' aborted or media_stopped #=#=#=#')
                player.media_stopped
                break   # Abort was requested while waiting. Exit the while loop.
    player.stop()
    xbmc.log('#=#=#=# left ' + ch + ' #=#=#=#')


def main():
    params = sys.argv[2][1:]
    params = dict(urllib2.urlparse.parse_qsl(params))

    cntv = params.get('stream')
    city = params.get('city')
    category = params.get('category')
    replay = params.get('replay')

    if cntv:
        pDialog = xbmcgui.DialogProgress()
        pDialog.create(addon.getLocalizedString(30009), addon.getLocalizedString(30010))
        pDialog.update(0)
        try:
            #Locate the M3U8 file
            resp = urllib2.urlopen("http://vdn.live.cntv.cn/api2/live.do?channel=pa://cctv_p2p_hd" + cntv)
            data = resp.read()
            data = data.decode('utf-8')
            resp.close()
            if pDialog.iscanceled():
                return

            url = None
            jsondata = jsonimpl.loads(data.encode('utf-8'))
            urlsTried = 0
            urlsToTry = 5

            if 'hls_url' in jsondata:
                for i in range(1, urlsToTry + 1):
                    urlsTried += 1
                    pDialog.update(urlsTried * 500 / urlsToTry,
                                   "{0} {1} (HLS)".format(addon.getLocalizedString(30011), "hls%d" % i))
                    url = tryStream(jsondata, "hls%d" % i, 'hls_url')
                    if url is not None:
                        break
                    if pDialog.iscanceled():
                        return

            if url is None and 'flv_url' in jsondata:
                for i in range(1, 7):
                    url = tryStream(jsondata, "flv%d" % i, 'flv_url')
                    if url is not None:
                        break

            if url is None:
                showNotification(30002)
                pDialog.close()
                return

            auth = urlparse.parse_qs(urlparse.urlparse(url)[4])["AUTH"][0]
            url = url + "|" + urllib.urlencode({"Cookie": "AUTH=" + auth})
            print url
            url = getHttp(url)

            pDialog.close()
            xbmc.Player().play(url)

        except Exception:
            showNotification(30000)
            print(traceback.format_exc())
            pDialog.close()
            return

    elif city:
        for area in cityList:        # find area in cityList
            if area['id'] == city:
                break

        channels = len(area['channel'])
        for i in range(channels):
            key = area['channel'][i].keys()[0]
            addStream(key, area['channel'][i][key])

        xbmcplugin.endOfDirectory(addon_handle)

    elif category:
        if category == "yangshi":
            for item in cctvList:
                addStream(item[0], item[1])

        if category == "weishi":
            for item in weishList:
                addStream(item[0], item[1])

        if category == "shuzi":
            addStream("zhongxuesheng", "CCTV中学生")
            addStream("cctvfxzl", "CCTV发现之旅")
            addStream("xinkedongman", "CCTV新科动漫")
            addStream("zhinan", "CCTV电视指南")

        if category == "chengshi":
            for item in cityList:
                addCity(item['id'], item['area'])

        if category == 'cctvreplay':
            for item in cctvList:
                addStream(item[0], item[1], '?replay=')

        xbmcplugin.endOfDirectory(addon_handle)

    elif replay:
        title = params['title']
        thumb = params['thumb']
        cntvReplay(replay, title, thumb)

    else:
        def addCategory(categoryID, categoryName):
            li = xbmcgui.ListItem(categoryName)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=sys.argv[0] + "?category=" + categoryID, listitem=li, isFolder=True)

        for title in mainList:
            addCategory(title, mainList[title])

        addCategory('cctvreplay', '央视重播节目')
        xbmcplugin.endOfDirectory(addon_handle)

main()
