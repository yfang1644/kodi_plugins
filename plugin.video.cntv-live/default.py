#!/usr/bin/python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin, xbmcgui
from common import get_html
import re

plugin = Plugin()
url_for = plugin.url_for

channelList = [{'央视频道':
          [{'CCTV1综合':'http://223.110.242.130:6610/gitv/live1/G_CCTV-1-HQ/'},
           {'CCTV2财经':'http://223.110.242.130:6610/gitv/live1/G_CCTV-2-HD/'},
           {'CCTV3综艺':'http://223.110.242.130:6610/gitv/live1/G_CCTV-3-HQ/'},
           {'CCTV4国际':'http://223.110.242.130:6610/gitv/live1/G_CCTV-4-HQ/'},
           {'CCTV5体育':'http://223.110.242.130:6610/gitv/live1/G_CCTV-5-HQ/'},
           {'CCTV5赛事':'http://223.110.242.130:6610/gitv/live1/G_CCTV-5PLUS-HQ/'},
           {'CCTV6电影':'http://223.110.242.130:6610/gitv/live1/G_CCTV-6-HQ/'},
           {'CCTV7国防军事':'http://223.110.242.130:6610/gitv/live1/G_CCTV-7-HQ/'},
           {'CCTV8电视剧':'http://223.110.242.130:6610/gitv/live1/G_CCTV-8-HQ/'},
           {'CCTV9纪录':'http://223.110.242.130:6610/gitv/live1/G_CCTV-9/'},
           {'CCTV10科教':'http://223.110.242.130:6610/gitv/live1/G_CCTV-10-HQ/'},
           {'CCTV11戏剧':'http://223.110.242.130:6610/gitv/live1/G_CCTV-11-HQ/'},
           {'CCTV12社会与法':'http://223.110.242.130:6610/gitv/live1/CCTV-12/'},
           {'CCTV13新闻':'http://223.110.242.130:6610/gitv/live1/G_CCTV-13-HQ/'},
           {'CCTV14少儿':'http://223.110.242.130:6610/gitv/live1/G_CCTV-14/'},
           {'CCTV15音乐':'http://223.110.242.130:6610/gitv/live1/G_CCTV-15/'},
           {'CCTV17农业农村':'http://223.110.242.130:6610/gitv/live1/G_CCTV-17/'},
           {'CCTV发现之旅':'http://223.110.242.130:6610/gitv/live1/G_FAXIANZL/'},
           {'CCTV第一剧场':'http://39.135.15.70:6610/PLTV/88888888/224/3221225702/1/'},
           {'CCTV风云剧场':'http://httpdvb.slave.homed.hrtn.net/playurl?playtype=live&protocol=hls&accesstoken=R5D22D2B7U309E0093K7735BBEDIAC2DC601PBM3187915V10453Z6B7EDWE3620470C71&&playtoken=&programid=4200000094'},
           {'CCTV怀旧剧场':'http://httpdvb.slave.homed.hrtn.net/playurl?playtype=live&protocol=hls&accesstoken=R5D22D2B7U309E0093K7735BBEDIAC2DC601PBM3187915V10453Z6B7EDWE3620470C71&&playtoken=&programid=4200000089'},
           {'CCTV老故事':'http://223.110.242.130:6610/gitv/live1/G_LAOGUSHI/'},
           {'CCTV女性时尚':'http://223.110.242.130:6610/gitv/live1/G_NVXINGSS/'},
          ]},
         {'央视数字频道NewTV':
          [{'NewTV精品体育':'http://223.110.242.130:6610/cntv/live1/jtiyu/jtiyu'},
           {'NewTV动画王国':'http://223.110.242.130:6610/cntv/live1/donghuawg/donghuawg'},
           {'NewTV动作电影':'http://223.110.242.130:6610/cntv/live1/dongzuody/dongzuody'},
           {'NewTV爱情喜剧':'http://223.110.242.130:6610/cntv/live1/aiqingxj/aiqingxj'},
           {'NewTV精品电影':'http://223.110.242.130:6610/cntv/live1/jdianying/jdianying'},
           {'NewTV古装剧场':'http://223.110.242.130:6610/cntv/live1/guzhuangjc/guzhuangjc'},
           {'NewTV明星大片':'http://223.110.242.130:6610/cntv/live1/mingxingdp/mingxingdp'},
           {'NewTV东北热剧':'http://ottrrs.hl.chinamobile.com/PLTV/88888888/224/3221225741/index.m3u8'},
           {'NewTV海外剧场':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225917/1.m3u8'},
           {'NewTV精品大剧':'http://223.110.242.130:6610/cntv/live1/jdaju/jdaju'},
           {'NewTV中国功夫':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226298/1.m3u8'},
           {'NewTV搏击':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226297/1.m3u8'},
           {'NewTV金牌综艺':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226296/1.m3u8'},
           {'NewTV超级综艺':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226231/1.m3u8'},
           {'NewTV惊悚悬疑':'http://223.110.242.130:6610/cntv/live1/jingsongxy/jingsongxy'},
           {'NewTV军旅剧场':'http://223.110.242.130:6610/cntv/live1/junlvjc/junlvjc'},
           {'NewTV农业致富':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226304/1.m3u8'},
           {'NewTV潮妈辣婆':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225957/1.m3u8'},
           {'NewTV超级电视剧':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226253/1.m3u8'},
           {'NewTV超级体育':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226232/1.m3u8'},
           {'NewTV超级电影':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226233/1.m3u8'},
           {'NewTV电竞':'http://112.50.243.7/PLTV/88888888/224/3221225894/1.m3u8'},
           {'NewTV家庭剧场':'http://223.110.242.130:6610/cntv/live1/jiatingjc/jiatingjc'},
           {'NewTV欢乐剧场':'http://ottrrs.hl.chinamobile.com/PLTV/88888888/224/3221225742/1.m3u8'},
           {'NewTV健康有约':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225919/1.m3u8'},
           {'NewTV精品记录':'http://223.110.242.130:6610/cntv/live1/jingpinjl/jingpinjl'},
           {'NewTV军事评论':'http://223.110.242.130:6610/cntv/live1/junshipl/junshipl'}
          ]},
         {'央视数字频道':
          [{'CIBN军事':'http://live1.nty.tv189.com/tm-yg1gzjc-512k.m3u8'},
           {'CIBN财经':'http://live1.nty.tv189.com/tm-yg1sfyx-512k.m3u8'},
           {'CIBN古装剧场':'http://live1.nty.tv189.com/tm-yg1zypd-512k.m3u8'},
           {'CIBN旅游':'http://live1.nty.tv189.com/tm-yg1lypd-512k.m3u8'},
           {'CIBN喜剧影院':'http://live1.nty.tv189.com/tm-yg1xjyy-1200k.m3u8'},
           {'CIBN电影导视':'http://live1.nty.tv189.com/tm-yg1dyds-1200k.m3u8
           {'CIBN华语影院':'http://live1.nty.tv189.com/tm-yg1hyyy-1200k.m3u8'},
           {'CIBN流金岁月':'http://live1.nty.tv189.com/tm-yg1scpd-1200k.m3u8'},
           {'CIBN电影':'http://live1.nty.tv189.com/tm-yg1dypd-1200k.m3u8'},
           {'CIBN精品影院':'http://live1.nty.tv189.com/tm-yg1jpyy-1200k.m3u8'},
           {'CIBN微电影':'http://live1.nty.tv189.com/tm-yg1wdypd-1200k.m3u8'},
           {'CIBN童学世界':'http://live1.nty.tv189.com/tm-yg1rbjc-1200k.m3u8'},
           {'CIBN健康':'http://live1.nty.tv189.com/tm-yg1jkpd-512k.m3u8'},
           {'CIBN骄阳剧场':'http://live1.nty.tv189.com/tm-yg1jyjc-1200k.m3u8'},
           {'CIBN嗨播':'http://live1.nty.tv189.com/tm-yg1yypd-512k.m3u8'},
           {'CIBN嗨播-经典音乐':'http://live1.nty.tv189.com/tm-yg1jdyy-800k.m3u8'},
           {'CIBN嗨播-音乐综艺':'http://live1.nty.tv189.com/tm-yg1yyzy-800k.m3u8'},
           {'CIBN嗨播-流行榜单':'http://live1.nty.tv189.com/tm-yg1lxbd-800k.m3u8'},
           {'CIBN嗨播-音乐大师课':'http://live1.nty.tv189.com/tm-yg1yydks-800k.m3u8'},
           {'CIBN嗨播-女团专场':'http://live1.nty.tv189.com/tm-yg1ntzc-800k.m3u8'},
           {'CIBN嗨播-原创音乐':'http://live1.nty.tv189.com/tm-yg1ycyy-800k.m3u8'},
           {'CIBN嗨播-MV':'http://live1.nty.tv189.com/tm-yg1mv-800k.m3u8'},
           {'CHC华诚影视':'http://live1.nty.tv189.com/tm-cridyty-800k.m3u8'},
           {'CRI精选剧场':'http://live1.nty.tv189.com/tm-cridsjty-800k.m3u8'},
           {'SIZE体育赛事':'http://live1.nty.tv189.com/rs-sizedj02/live.m3u8'},
           {'CBN风尚生活':'http://www.dszbdq.cn/diao/gz.php?id=bd5a65f3eef22bf93ac0169b64ffbd7e'},
           {'CBN每日影院':'http://www.dszbdq.cn/diao/gz.php?id=ad1795ad29a4b83dffb88a592bd157e2'},
           {'CBN幸福剧场':'http://www.dszbdq.cn/diao/gz.php?id=245ba3ebf5e9e61dc1999ff32a95d349'},
           {'CBN幸福娱乐频道':'http://httpdvb.slave.homed.hrtn.net/playurl?playtype=live&protocol=hls&accesstoken=R5D22D2B7U309E0093K7735BBEDIAC2DC601PBM3187915V10453Z6B7EDWE3620470C71&playtoken=ABCDEFGHIGK&programid=4200000193'},
          ]},
         {'爱奇艺轮播':
          [{'经典港片':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_jingdianguangpian_1080p_t10/c15_lb_jingdianguangpian_1080p_t10.m3u8'},
           {'电影精选':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_dianyingjingxuan_1080p_t10/c15_lb_dianyingjingxuan_1080p_t10.m3u8'},
           {'五星影院':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_wuxingyingyuan_1080p_t10/c15_lb_wuxingyingyuan_1080p_t10.m3u8'},
           {'动作电影':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_dongzuodianying_1080p_t10/c16_lb_dongzuodianying_1080p_t10.m3u8'},
           {'黑帮电影':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_heibangdianying_1080p_t10/c16_lb_heibangdianying_1080p_t10.m3u8'},
           {'欢乐剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_xijudianying_1080p_t10/c16_lb_xijudianying_1080p_t10.m3u8'},
           {'惊悚午夜场':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_jingnawuyechang_1080p_t10/c16_lb_jingnawuyechang_1080p_t10.m3u8'},
           {'动画电影':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_donghuadianying_1080p_t10/c16_lb_donghuadianying_1080p_t10.m3u8'},
           {'记录片':'http://cdn-out.iqy.sc96655.com/tslive/c15_lb_newjilupian_1080p_t10/c15_lb_newjilupian_1080p_t10.m3u8'},
           {'科学探索':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_kexuetansuo_1080p_t10/c16_lb_kexuetansuo_1080p_t10.m3u8'},
           {'自然地理':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_zirandili_1080p_t10/c16_lb_zirandili_1080p_t10.m3u8'},
           {'华语院线':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_huayuyuanxian_1080p_t10/c16_lb_huayuyuanxian_1080p_t10.m3u8'},
           {'怀旧剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_huaijiujuchang_1080p_t10/c16_lb_huaijiujuchang_1080p_t10.m3u8'},
           {'日韩院线':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_rihanyuanxian_1080p_t10/c16_lb_rihanyuanxian_1080p_t10.m3u8'},
           {'周末影院':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_fengxiaogang_1080p_t10/c16_lb_fengxiaogang_1080p_t10.m3u8'},
           {'经典重温':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_jingdianjuchang_1080p_t10/c16_lb_jingdianjuchang_1080p_t10.m3u8'},
           {'谍战剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_diezhanjuchang_1080p_t10/c16_lb_diezhanjuchang_1080p_t10.m3u8'},
           {'军旅剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_junlvjuchang_1080p_t10/c16_lb_junlvjuchang_1080p_t10.m3u8'},
           {'情景喜剧':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_kaixinjuchang_1080p_t10/c16_lb_kaixinjuchang_1080p_t10.m3u8'},
           {'热血搏击':'http://cdn-out.iqy.sc96655.com/tslive/c16_lb_bojinew_1080p_t10/c16_lb_bojinew_1080p_t10.m3u8'},
           {'人文社会':'http://cdn-out.iqy.sc96655.com/tslive/c15_lb_renwenshehui_1080p_t10/c15_lb_renwenshehui_1080p_t10.m3u8'},
           {'老年剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_laonianjuchang_1080p_t10/c15_lb_laonianjuchang_1080p_t10.m3u8'},
           {'青春剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_weizhangzhe_1080p_t10/c15_lb_weizhangzhe_1080p_t10.m3u8'},
           {'宫廷正剧':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_niandaijuchang_1080p_t10/c15_lb_niandaijuchang_1080p_t10.m3u8'},
           {'家庭剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_jiatingjuchang_1080p_t10/c15_lb_jiatingjuchang_1080p_t10.m3u8'},
           {'抗战剧场':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_kangzhanjuchang_1080p_t10/c15_lb_kangzhanjuchang_1080p_t10.m3u8'},
           {'热播电视剧':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_reboju_1080p_t10/c15_lb_reboju_1080p_t10.m3u8'},
           {'历史秘闻':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_lishimiwen_1080p_t10/c15_lb_lishimiwen_1080p_t10.m3u8'},
           {'旅游攻略':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_lvyounew_1080p_t10/c15_lb_lvyounew_1080p_t10.m3u8'},
           {'军事观察':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_junshinew_1080p_t10/c16_lb_junshinew_1080p_t10.m3u8'},
           {'童年经典':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_balalaxiaomoxian_1080p_t10/c15_lb_balalaxiaomoxian_1080p_t10.m3u8'},
           {'动物兄弟':'http://baiducdnct.inter.iqiyi.com/tslive/c16_lb_yingshijinqu_1080p_t10/c16_lb_yingshijinqu_1080p_t10.m3u8'},
           {'怀旧动画':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_huanjiudongman_1080p_t10/c15_lb_huanjiudongman_1080p_t10.m3u8'},
           {'儿童乐园':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_dongmantiandi_1080p_t10/c15_lb_dongmantiandi_1080p_t10.m3u8'},
           {'亲子启蒙':'http://101.72.196.41/r/baiducdnct.inter.iqiyi.com/tslive/c16_lb_qinziqimeng_1080p_t10/c16_lb_qinziqimeng_1080p_t10.m3u8'},
           {'宝贝课堂':'http://cdn-out.iqy.sc96655.com/tslive/c16_lb_baobaoketang_1080p_t10/c16_lb_baobaoketang_1080p_t10.m3u8'},
           {'脱口秀':'http://baiducdnct.inter.iqiyi.com/tslive/c15_lb_mingxingtoukouxiu_1080p_t10/c15_lb_mingxingtoukouxiu_1080p_t10.m3u8'},
           {'王牌对王牌':'http://cdn-out.iqy.sc96655.com/tslive/c20_lb_fengshang_high_t10/c20_lb_fengshang_high_t10.m3u8'},
           {'网球赛事':'http://cdn-out.iqy.sc96655.com/tslive/c15_lb_wangqiu2_1080p_t10/c15_lb_wangqiu2_1080p_t10.m3u8'},
           {'奔跑吧':'http://cdn-out.iqy.sc96655.com/tslive/c15_lb_benpaobaxiongdi_1080p_t10/c15_lb_benpaobaxiongdi_1080p_t10.m3u8'},
           {'宠物台':'http://cdn-out.iqy.sc96655.com/tslive/c15_lb_chongwutai_1080p_t10/c15_lb_chongwutai_1080p_t10.m3u8'},
        ]},
         {'北京':
          [{'北京卫视':'http://cctvalih5ca.v.myalicdn.com/wstv/btv1_2/index.m3u8'},
           {'北京文艺':'http://cctvalih5ca.v.myalicdn.com/wstv/btv2_2/index.m3u8'},
           {'北京科教':'http://cctvalih5ca.v.myalicdn.com/wstv/btv3_2/index.m3u8'},
           {'北京影视':'http://cctvalih5ca.v.myalicdn.com/wstv/btv4_2/index.m3u8'},
           {'北京财经':'http://cctvalih5ca.v.myalicdn.com/wstv/btv5_2/index.m3u8'},
           {'北京体育':'http://cctvalih5ca.v.myalicdn.com/wstv/btv6_2/index.m3u8'},
           {'北京生活':'http://cctvalih5ca.v.myalicdn.com/wstv/btv7_2/index.m3u8'},
           {'北京青年':'http://cctvalih5ca.v.myalicdn.com/wstv/btv8_2/index.m3u8'},
           {'北京新闻':'http://cctvalih5ca.v.myalicdn.com/wstv/btv9_2/index.m3u8'},
           {'北京少儿':'http://ivi.bupt.edu.cn/hls/btv10.m3u8'}
          ]},
         {'上海':
          [{'东方卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227208/index.m3u8'},
           {'上海纪实':'http://ott.js.chinamobile.com/PLTV/3/224/3221227420/index.m3u8'},
           {'上海lcs':'http://117.156.28.21/PLTV/88888888/224/3221225639/index.m3u8'},
           {'上海影视':'http://117.156.28.21/PLTV/88888888/224/3221225654/index.m3u8'},
          ]},
         {'天津':
          [{'天津卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227212/index.m3u8'},
           {'天津都市频道':'http://www.dszbdq.cn/diao/tjdspd.php'},
           {'天津科教频道':'http://www.dszbdq.cn/diao/tjkjpd.php'},
           {'天津少儿频道':'http://www.dszbdq.cn/diao/tjsepd.php'},
           {'天津体育频道':'http://www.dszbdq.cn/diao/tjtypd.php'},
           {'天津文艺频道':'http://www.dszbdq.cn/diao/tjwypd.php'},
           {'天津新闻频道':'http://www.dszbdq.cn/diao/tjxwpd.php'},
           {'天津影视频道':'http://www.dszbdq.cn/diao/tjyspd.php'},
          ]},
         {'重庆':
          [{'重庆卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225594/index.m3u8'}
          ]},
         {'港澳台':
          [{'凤凰中文':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225942/1.m3u8'},
           {'凤凰香港':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226120/1.m3u8'},
           {'凤凰资讯':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225949/1.m3u8'},
           {'阳光卫视':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226121/1.m3u8'}
          ]},
         {'江苏':
          [{'江苏城市':'http://ott.js.chinamobile.com/PLTV/4/224/3221225929/index.m3u8'},
           {'江苏卫视':'http://ott.js.chinamobile.com/PLTV/4/224/3221225782/index.m3u8'},
           {'江苏体育休闲':'http://ott.js.chinamobile.com/PLTV/4/224/3221225935/index.m3u8'},
           {'江苏公共':'http://223.110.241.204:6610/gitv/live1/G_JSGG/G_JSGG/'},
           {'江苏教育':'http://223.110.241.204:6610/gitv/live1/G_JSJY/G_JSJY/'},
           {'江苏综艺':'http://223.110.241.204:6610/gitv/live1/G_JSZY/G_JSZY/'},
           {'江苏影视':'http://ott.js.chinamobile.com/PLTV/4/224/3221225937/index.m3u8'},
           {'南京新闻综合':'http://223.110.241.139:6610/gitv/live1/G_NJXW/G_NJXW'},
           {'南京教科频道':'http://223.110.241.204:6610/gitv/live1/G_NJJK/G_NJJK'},
           {'南京生活频道':'http://live.nbs.cn/channels/njtv/shpd/flv:500k/live'},
           {'南京娱乐频道':'http://live.nbs.cn/channels/njtv/ylpd/flv:500k/live'},
           {'南京少儿频道':'http://live.nbs.cn/channels/njtv/sepd/flv:500k/live'},
           {'南京信息频道':'http://live.nbs.cn/channels/njtv/xxpd/flv:500k/live'},
           {'南京十八频道':'http://223.110.241.139:6610/gitv/live1/G_NJSB/G_NJSB'},
           {'栖霞电视台':'http://pili-live-hls.140.i2863.com/i2863-140/live_140_236499.m3u8'},
          ]},
         {'湖南':
          [{'湖南卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225908/index.m3u8'},
           {'湖南电视剧频道':'http://www.dszbdq.cn/diao/mgtv.php?id=484'},
           {'湖南公共频道':'http://www.dszbdq.cn/diao/mgtv.php?id=261'},
           {'湖南经视':'http://www.dszbdq.cn/diao/mgtv.php?id=280'},
           {'湖南教育电视台':'http://pull.hnedutv.com/live/edutv.m3u8'},
           {'湖南娱乐频道':'http://www.dszbdq.cn/diao/mgtv.php?id=344'},
          ]},
         {'广东':
          [{'广东南方卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227005/index.m3u8'},
           {'广东卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225592/index.m3u8'},
           {'广东珠江频道':'http://nclive.grtn.cn/zjpd/sd/live.m3u8'},
           {'广东房产频道':'http://nclive.grtn.cn/fcpd/sd/live.m3u8'},
           {'广东高尔夫频道':'http://nclive.grtn.cn/grfpd/sd/live.m3u8'},
           {'广东公共频道':'http://nclive.grtn.cn/ggpd/sd/live.m3u8'},
           {'广东国际频道':'http://nclive.grtn.cn/gjpd/sd/live.m3u8'},
           {'广东经济科教':'http://nclive.grtn.cn/tvs1hd/hd/live.m3u8'},
           {'广东岭南戏曲':'http://nclive.grtn.cn/lnxq/sd/live.m3u8'},
           {'广东少儿频道':'http://nclive.grtn.cn/tvs5/sd/live.m3u8'},
           {'广东体育频道':'http://www.dszbdq.cn/diao/migu.php?id=624303497'},
           {'广东新闻频道':'http://nclive.grtn.cn/xwpd/sd/live.m3u8'},
           {'广东影视频道':'http://nclive.grtn.cn/tvs4/sd/live.m3u8'},
           {'广东综艺频道':'http://player.ioioz.com/18/tv.php?tv=gdtv&id=gdtvs3'},
           {'嘉佳卡通':'http://nclive.grtn.cn/jjkt/sd/live.m3u8'},
           {'深圳卫视':'http://cctvtxyh5ca.liveplay.myqcloud.com/wstv/shenzhen_2/index.m3u8'},
          ]},
        {'浙江':
         [{'浙江卫视':'http://ali.m.l.cztv.com/channels/lantian/channel01/720p.m3u8'},
          {'浙江钱江':'http://ali.m.l.cztv.com/channels/lantian/channel02/720p.m3u8'},
          {'浙江经济':'http://ali.m.l.cztv.com/channels/lantian/channel03/720p.m3u8'},
          {'浙江科教':'http://ali.m.l.cztv.com/channels/lantian/channel04/720p.m3u8'},
          {'浙江影视':'http://ali.m.l.cztv.com/channels/lantian/channel05/720p.m3u8'},
          {'浙江民生':'http://ali.m.l.cztv.com/channels/lantian/channel06/720p.m3u8'},
          {'浙江新闻':'http://ali.m.l.cztv.com/channels/lantian/channel07/720p.m3u8'},
          {'浙江少儿':'http://ali.m.l.cztv.com/channels/lantian/channel08/720p.m3u8'},
          {'浙江留学世界':'http://ali.m.l.cztv.com/channels/lantian/channel09/720p.m3u8'},
          {'浙江国际':'http://ali.m.l.cztv.com/channels/lantian/channel10/720p.m3u8'},
          {'好易购':'http://ali.m.l.cztv.com/channels/lantian/channel11/720p.m3u8'},
          {'浙江数码时代':'http://ali.m.l.cztv.com/channels/lantian/channel12/720p.m3u8'},
        ]},
        {'安徽':
         [{'安徽卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225634/index.m3u8'},
          {'安徽公共频道':'http://zbbf2.ahtv.cn/live/752.m3u8'},
          {'安徽国际频道':'http://zbbf2.ahtv.cn/live/dab.m3u8'},
          {'安徽经济生活':'http://zbbf2.ahtv.cn/live/750.m3u8'},
          {'安徽科教频道':'http://zbbf2.ahtv.cn/live/754.m3u8'},
          {'安徽影视频道':'http://zbbf2.ahtv.cn/live/756.m3u8'},
          {'安徽综艺频道':'http://zbbf2.ahtv.cn/live/758.m3u8'},
        ]},
        {'福建':
         [{'东南卫视':'http://ott.js.chinamobile.com/PLTV/4/224/3221225816/index.m3u8'},
          {'厦门卫视':'http://cstvpull.live.wscdns.com/live/xiamen.flv'},
          {'厦门一套':'http://cstvpull.live.wscdns.com/live/xiamen1.flv'},
          {'厦门二套':'http://cstvpull.live.wscdns.com/live/xiamen2.flv'},
          {'厦门三套':'http://cstvpull.live.wscdns.com/live/xiamen3.flv'},
          {'厦门四套':'http://cstvpull.live.wscdns.com/live/xiamen4.flv'},
          {'厦门移动':'http://cstvpull.live.wscdns.com/live/xiamenyidong.flv'},
         ]},
        {'山东':
         [{'山东卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227258/index.m3u8'},
          {'山东教育卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227019/index.m3u8'},
          {'山东公共频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=ggpd'},
          {'山东国际频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=gjpd'},
          {'山东农科频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=nkpd'},
          {'山东齐鲁电视台':'http://player.ioioz.com/18/tv.php?tv=qltv&id=qlpd'},
          {'山东少儿频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=sepd'},
          {'山东生活频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=shpd'},
          {'山东体育频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=typd'},
          {'山东影视频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=yspd'},
          {'山东综艺频道':'http://player.ioioz.com/18/tv.php?tv=qltv&id=zypd'},
         ]},
        {'山西':
         [{'山西卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225576/index.m3u8'}
         ]},
        {'湖北':
         [{'湖北卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227211/index.m3u8'},
          {'湖北公共新闻':'http://live.cjyun.org/hubeitv/s10008-live-hbgg.m3u8'},
          {'湖北经视高清':'http://live.cjyun.org/hubeitv/s10008-live-hbjs.m3u8'},
          {'湖北教育频道':'http://live.cjyun.org/hubeitv/s10008-live-hbjy.m3u8'},
          {'湖北垄上频道':'http://live.cjyun.org/hubeitv/s10008-live-hbls.m3u8'},
          {'湖北美嘉购物':'http://live.cjyun.org/hubeitv/s10008-live-mjgw.m3u8'},
          {'湖北生活频道':'http://live.cjyun.org/hubeitv/s10008-live-hbsh.m3u8'},
          {'湖北休闲指南':'http://live.cjyun.org/hubeitv/s10008-live-xxzn.m3u8'},
          {'湖北影视频道':'http://live.cjyun.org/hubeitv/s10008-live-hbys.m3u8'},
          {'湖北综合频道':'http://live.cjyun.org/hubeitv/s10008-live-hbzh.m3u8'},
         ]},
        {'四川':
         [{'四川卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225570/index.m3u8'},
          {'四川文化旅游频道':'http://scgctvshow.sctv.com/hdlive/sctv2/1.m3u8'},
          {'四川经济频道':'http://scgctvshow.sctv.com/hdlive/sctv3/1.m3u8'},
          {'四川新闻频道':'http://scgctvshow.sctv.com/sdlive/sctv4/1.m3u8'},
          {'四川影视文艺':'http://scgctvshow.sctv.com/hdlive/sctv5/1.m3u8'},
          {'四川星空购物':'http://scgctvshow.sctv.com/hdlive/sctv6/1.m3u8'},
          {'四川妇女儿童':'http://scgctvshow.sctv.com/hdlive/sctv7/1.m3u8'},
          {'四川公共乡村频道':'http://scgctvshow.sctv.com/hdlive/sctv9/1.m3u8'},
          {'峨眉电影':'http://scgctvshow.sctv.com/hdlive/emei/1.m3u8'},
          {'四川国际频道':'http://61.58.60.230:9319/live/238.m3u8'},
          {'四川康巴卫视':'http://scgctvshow.sctv.com/sdlive/kangba/1.m3u8'},
          {'成都新闻综合频道':'http://www.dszbdq.cn/diao/cdtv1.php'},
          {'成都经济资讯频道':'http://www.dszbdq.cn/diao/cdtv2.php'},
          {'成都都市生活频道':'http://www.dszbdq.cn/diao/cdtv3.php'},
          {'成都影视文艺频道':'http://www.dszbdq.cn/diao/cdtv4.php'},
          {'成都公共频道':'http://www.dszbdq.cn/diao/cdtv5.php'},
          {'成都少儿频道':'http://www.dszbdq.cn/diao/cdtv6.php'},
          {'成都食尚频道':'http://www.dszbdq.cn/diao/cdtv9.php'},
          {'成都汽车频道':'http://www.dszbdq.cn/diao/cdtv10.php'},
          {'成都资讯新干线':'http://www.dszbdq.cn/diao/cdtv11.php'},
          {'成都美食旅游频道':'http://www.dszbdq.cn/diao/cdtv12.php'},
          {'成都美食天府频道':'http://www.dszbdq.cn/diao/cdtv17.php'},
          {'成都每日购物频道':'http://www.dszbdq.cn/diao/cdtv18.php'},
          {'成华有线台':'http://www.dszbdq.cn/diao/cdchtv.php'},
          {'成都崇州电视台':'http://www.dszbdq.cn/diao/cdcztv.php'},
          {'成都都江堰电视台':'http://www.dszbdq.cn/diao/cddjytv.php'},
          {'成都大邑电视台':'http://www.dszbdq.cn/diao/cddytv.php'},
          {'成都高新电视台':'http://www.dszbdq.cn/diao/cdgxtv.php'},
          {'金牛有线电视台':'http://www.dszbdq.cn/diao/cdjntv.php'},
          {'成都金堂电视台':'http://www.dszbdq.cn/diao/cdjttv.php'},
          {'成都龙泉驿区电视':'http://www.dszbdq.cn/diao/cdlqtv.php'},
          {'成都郫都电视台':'http://www.dszbdq.cn/diao/cdpdtv.php'},
          {'成都蒲江电视台':'http://www.dszbdq.cn/diao/cdpjtv.php'},
          {'成都彭州电视台':'http://www.dszbdq.cn/diao/cdpztv.php'},
          {'成都青白江电视台':'http://www.dszbdq.cn/diao/cdqbjtv.php'},
          {'成都邛崃电视台':'http://www.dszbdq.cn/diao/cdqltv.php'},
          {'成都双流电视台':'http://www.dszbdq.cn/diao/cdsltv.php'},
          {'成都温江电视台':'http://tp01.videocc.net/cnbaina/cnbaina/playlist.m3u8'},
          {'成都新津电视台':'http://www.dszbdq.cn/diao/cdxjtv.php'},
         ]},
        {'海南':
         [{'海南卫视':'http://112.17.40.140/PLTV/88888888/224/3221226116/index.m3u8'}
         ]},
        {'河南':
         [{'河南卫视':'http://223.110.241.139:6610/gitv/live1/HENAN/HENAN/'},
         ]},
        {'河北':
         [{'河北卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225602/index.m3u8'}
         ]},
        {'辽宁':
         [{'辽宁卫视':'http://223.110.241.139:6610/gitv/live1/LNWS/LNWS/'}
         ]},
        {'吉林':
         [{'吉林卫视':'http://223.110.241.139:6610/gitv/live1/G_JILIN/G_JILIN/'}
         ]},
        {'黑龙江':
         [{'黑龙江卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221227252/index.m3u8'}
         ]},
        {'江西':
         [{'江西卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225536/index.m3u8'}
         ]},
        {'广西':
         [{'广西卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225554/index.m3u8'}
        ]},
         {'云南':
          [{'云南卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225591/index.m3u8'}
          ]},
         {'陕西':
          [{'陕西卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225626/index.m3u8'}
          ]},
         {'贵州':
          [{'贵州卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225540/index.m3u8'}
          ]},
        {'宁夏':
         [{'宁夏卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225628/index.m3u8'}
         ]},
         {'青海':
          [{'青海卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225783/index.m3u8'}
          ]},
         {'西藏':
          [{'西藏卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225579/index.m3u8'}
          ]},
         {'甘肃':
          [{'甘肃卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225590/index.m3u8'},

           {'甘肃都市': 'http://117.156.28.119/270000001111/1110000068/index.m3u8'},
           {'甘肃影视': 'http://117.156.28.119/270000001111/1110000067/index.m3u8'},
           {'甘肃经济': 'http://117.156.28.119/270000001111/1110000070/index.m3u8'},
           {'甘肃少儿': 'http://117.156.28.119/270000001111/1110000071/index.m3u8'},
          ]},
         {'内蒙古':
          [{'内蒙古卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225836/index.m3u8'}
          ]},
         {'新疆':
          [{'新疆卫视':'http://ott.js.chinamobile.com/PLTV/3/224/3221225523/index.m3u8'}
          ]},
         {'电影轮播':
           [{'亚洲影院':'http://hwltc.tv.cdn.zj.chinamobile.com/PLTV/88888888/224/3221228365/42613673.smil/index.m3u8?fmt=ts2hls'},
           {'欧美影院':'http://hwltc.tv.cdn.zj.chinamobile.com/PLTV/88888888/224/3221228384/42613784.smil/index.m3u8?fmt=ts2hls'},
           {'黑莓电影':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221225927/1.m3u8'},
           {'黑莓动画':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226289/1.m3u8'},
           {'黑莓电竞':'http://otttv.bj.chinamobile.com/PLTV/88888888/224/3221226307/1.m3u8'},
           {'周星驰(咪咕)':'http://www.dszbdq.cn/diao/migu.php?id=623338112'},
           {'赌神全集':'http://flv3.quanmin.tv/live/3766_2031799856.flv'},
           {'007系列':'http://flv3.quanmin.tv/live/3766_2015339572.flv'},
          ]},
         ]

@plugin.route('/playvideo/<url>/')
def playvideo(url):
    if url[-4:] == '.php':
        html = get_html(url)
        source = re.compile('src="(.+?m3u8.+?)"').findall(html)
        url = source[0]
    plugin.set_resolved_url(url)


@plugin.route('/category/<number>/')
def category(number):
    items = []
    channels = channelList[int(number)]
    channel = list(channels.items())
    for item in channel[0][1]:
        a = list(item.keys())[0]
        items.append({
            'label': a,
            'path': url_for('playvideo', url=item[a]),
            'is_playable': True,
            'info': {'title': a}
        })
    return items

@plugin.route('/')
def index():
    items = []
    for i, item in enumerate(channelList):
        a = list(item.keys())[0]
        items.append({
            'label': a,
            'path': url_for('category', number=i)
        })

    return items


if __name__ == '__main__':
    plugin.run()
