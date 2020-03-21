#!/usr/bin/python
# -*- coding: utf-8 -*-

APPKEY = '19bf1f1192873efa'
APPSECRET = '87677fc06b0afc08cb86e008183390e5'
APPKEY = 'iVGUTjsxvpLeuDCf'
SECRETKEY = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'

API_URL = 'https://api.bilibili.com'
HOME_URL = 'https://www.bilibili.com'
VIEW_URL = API_URL + '/view?{}'
LIST_URL = API_URL + '/list?{}'
LIST_BY_TAG = API_URL + '/x/tag/ranking/archives?jsonp=jsonp&tag_id={}&rid={}&ps={}&pn={}'
LIST_BY_ALL = API_URL + '/archive_rank/getarchiverankbypartion?type=jsonp&tid={}&ps={}&pn={}'
COMMENT_URL = 'https://comment.bilibili.com/{}.xml'
DYNAMIC_URL = API_URL + '/x/feed/pull?type=0&ps={}&pn={}'
SP_URL = API_URL + '/sp'
LOGIN_URL = 'https://passport.bilibili.com/web/login'
LOGIN_CAPTCHA_URL = 'https://passport.bilibili.com/captcha?r={}'
LOGIN_HASH_URL = 'https://passport.bilibili.com/login?act=getkey&r={}'
HISTORY_URL = API_URL + '/x/v2/history?pn={}&ps={}'
FAV_BOX_URL = 'http://space.bilibili.com/ajax/fav/getBoxList?mid={}'
FAV_URL = 'http://space.bilibili.com/ajax/fav/getList?mid={}&page={}&pagesize={}&fid={}'
TIMELINE_URL = 'http://bangumi.bilibili.com/jsonp/timeline_v2.ver?callback=timeline'
MY_INFO_URL = 'http://space.bilibili.com/ajax/member/MyInfo'
AV_URL = HOME_URL + '/widget/getPageList?aid={}'
BANGUMI_CHASE_URL = 'http://space.bilibili.com/ajax/Bangumi/getList?mid={}&page={}&pagesize={}'
BANGUMI_SEASON_URL = 'https://bangumi.bilibili.com/jsonp/seasoninfo/{}.ver?callback=seasonListCallback'
ADD_HISTORY_URL = 'http://interface.bilibili.com/player?id=cid:{}&aid={}'
#ATTENTION_URL = 'http://space.bilibili.com/ajax/friend/GetAttentionList?mid={}&page={}&pagesize={}'
ATTENTION_URL = 'https://api.bilibili.com/x/relation/followings?vmid={}&pn={}&ps={}'
ATTENTION_VIDEO_URL = 'https://space.bilibili.com/ajax/member/getSubmitVideos?mid={}&page={}&pagesize={}&tid={}'
ATTENTION_CHANNEL_URL = 'https://space.bilibili.com/ajax/channel/getChannel?mid={}'
ATTENTION_CHANNEL_LIST_URL = 'https://space.bilibili.com/ajax/channel/getVideo?mid={}&cid={}&p={}&num={}'

INTERFACE_URL = r'http://interface.bilibili.com/playurl?cid={}&from=miniplay&player=1&sign={}'
INTERFACE_PARAMS = r'cid={}&from=miniplay&player=1{}'
SECRETKEY_MINILOADER = r'1c15888dc316e05a15fdd0a02ed6584f'


LOGIN_ERROR_MAP = {
    -105: "验证码错误",
    -618: "昵称重复或含有非法字符",
    -619: "昵称不能小于3个字符或者大于30个字符",
    -620: "该昵称已被使用",
    -622: "Email已存在",
    -625: "密码错误次数过多",
    -626: "用户不存在",
    -627: "密码错误",
    -628: "密码不能小于6个字符或大于16个字符",
    -645: "昵称或密码过短",
    -646: "请输入正确的手机号",
    -647: "该手机已绑定另外一个账号",
    -648: "验证码发送失败",
    -652: "历史遗留问题，昵称与手机号重复，请联系管理员",
    -662: "加密后的密码已过期",
}

ORDER = [
    {
        'title': u'日排行榜',
        'value': 'hot',
        'days': 1,
    },
    {
        'title': u'三日排行榜',
        'value': 'hot',
        'days': 3,
    },
    {
        'title': u'周排行榜',
        'value': 'hot',
        'days': 7,
    },
    {
        'title': u'最新动态',
        'value': 'new',
        'days': 30,
    },
    {
        'title': u'最新投稿',
        'value': 'default',
        'days': 30,
    },
#    {
#        'title': u'按评论数从高至低排序',
#        'value': 'review'
#    },
#    {
#        'title': u'按弹幕数从高至低排序',
#        'value': 'damku'
#    },
#    {
#        'title': u'按推荐数从高至低排序',
#        'value': 'comment'
#    },
#    {
#        'title': u'按宣传数排序（硬币）',
#        'value': 'default'
#    },
]


CATEGORY = {
    "0": {
        "url": HOME_URL,
        "subs": [
            "1", 
            "13", 
            "167", 
            "3", 
            "129", 
            "4", 
            "36", 
            "160", 
            "119", 
            "155", 
            "165", 
            "5", 
            "23", 
            "11",
            "177"
        ], 
        "title": "全部"
    }, 
    "1": {
        "url": HOME_URL + '/video/douga.html',
        "subs": [
            "24", 
            "25", 
            "47", 
            "27"
        ], 
        "title": "动画"
    }, 
    "24": {
        "url": HOME_URL + '/video/douga-mad-1.html',
        "title": "MAD·AMV"
    }, 
    "25": {
        "url": HOME_URL + '/video/douga-mmd-1.html',
        "title": "MMD·3D"
    }, 
    "47": {
        "url": HOME_URL + '/video/douga-voice-1.html',
        "title": "短片·手书·配音"
    }, 
    "27": {
        "url": HOME_URL + '/video/douga-else-1.html',
        "title": "综合"
    }, 
    "13": {
        "url": "http://bangumi.bilibili.com/22/", 
        "subs": [
            "33", 
            "32", 
            "51", 
            "152"
        ], 
        "title": "番剧"
    }, 
    "33": {
        "url": HOME_URL + '/video/bangumi-two-1.html',
        "title": "连载动画"
    }, 
    "32": {
        "url": HOME_URL + '/video/part-twoelement-1.html',
        "title": "完结动画"
    }, 
    "51": {
        "url": HOME_URL + '/video/douga-else-information-1.html',
        "title": "资讯"
    }, 
    "152": {
        "url": HOME_URL + '/video/bagumi_offical_1.html',
        "title": "官方延伸"
    }, 
    "167": {
        "url": "http://bangumi.bilibili.com/guochuang/",
        "subs": [
            "153", 
            "168", 
            "169", 
            "170"
        ], 
        "title": "国创"
    }, 
    "153": {
        "url": HOME_URL + '/video/bangumi_chinese_1.html',
        "title": "国产动画"
    }, 
    "168": {
        "url": HOME_URL + '/video/guochuang-fanvid-1.html',
        "title": "国产原创相关"
    }, 
    "169": {
        "url": HOME_URL + '/video/glove-puppetry-1.html',
        "title": "布袋戏"
    }, 
    "170": {
        "url": HOME_URL + '/video/guochuang-offical-1.html',
        "title": "资讯"
    }, 
    "3": {
        "url": HOME_URL + '/video/music.html',
        "subs": [
            "28", 
            "31", 
            "30", 
            "59", 
            "29", 
            "54", 
            "130"
        ], 
        "title": "音乐"
    }, 
    "28": {
        "url": HOME_URL + '/video/music-original-1.html',
        "title": "原创音乐"
    }, 
    "31": {
        "url": HOME_URL + '/video/music-Cover-1.html',
        "title": "翻唱"
    }, 
    "30": {
        "url": HOME_URL + '/video/music-vocaloid-1.html',
        "title": "VOCALOID·UTAU"
    }, 
    "59": {
        "url": HOME_URL + '/video/music-perform-1.html',
        "title": "演奏"
    }, 
    "29": {
        "url": HOME_URL + '/video/music-coordinate-1.html',
        "title": "三次元音乐"
    }, 
    "54": {
        "url": HOME_URL + '/video/music-oped-1.html',
        "title": "OP/ED/OST"
    }, 
    "130": {
        "url": HOME_URL + '/video/music-collection-1.html',
        "title": "音乐选集"
    }, 
    "129": {
        "url": HOME_URL + '/video/dance.html',
        "subs": [
            "20", 
            "154", 
            "156"
        ], 
        "title": "舞蹈"
    }, 
    "20": {
        "url": HOME_URL + '/video/dance-1.html',
        "title": "宅舞"
    }, 
    "154": {
        "url": HOME_URL + '/video/three-dimension-dance-1.html',
        "title": "三次元舞蹈"
    }, 
    "156": {
        "url": HOME_URL + '/video/dance-demo-1.html',
        "title": "舞蹈教程"
    }, 
    "4": {
        "url": HOME_URL + '/video/game.html',
        "subs": [
            "17", 
            "65", 
            "136", 
            "19", 
            "121"
        ], 
        "title": "游戏"
    }, 
    "17": {
        "url": HOME_URL + '/video/game-video-1.html',
        "title": "单机联机"
    }, 
    "65": {
        "url": HOME_URL + '/video/game-ctary-network-1.html',
        "title": "网游·电竞"
    }, 
    "136": {
        "url": HOME_URL + '/video/music-game-1.html',
        "title": "音游"
    },
    "19": {
        "url": HOME_URL + '/video/game-mugen-1.html',
        "title": "Mugen"
    }, 
    "121": {
        "url": HOME_URL + '/video/gmv-1.html',
        "title": "GMV"
    }, 
    "36": {
        "url": HOME_URL + '/video/technology.html',
        "subs": [
            "37", 
            "124", 
            "122", 
            "39", 
            "96", 
            "95", 
            "98"
        ], 
        "title": "科技"
    }, 
    "37": {
        "url": HOME_URL + '/video/tech-popular-science-1.html',
        "title": "纪录片"
    }, 
    "124": {
        "url": HOME_URL + '/video/tech-fun-1.html',
        "title": "趣味科普人文"
    }, 
    "122": {
        "url": HOME_URL + '/video/tech-wild-1.html',
        "title": "野生技术协会"
    }, 
    "39": {
        "url": HOME_URL + '/video/speech-course-1.html',
        "title": "演讲•公开课"
    }, 
    "96": {
        "url": HOME_URL + '/video/tech-future-military-1.html',
        "title": "星海"
    }, 
    "95": {
        "url": HOME_URL + '/video/tech-future-digital-1.html',
        "title": "数码"
    }, 
    "98": {
        "url": HOME_URL + '/video/tech-future-other-1.html',
        "title": "机械"
    }, 
    "160": {
        "url": HOME_URL + '/video/life.html',
        "subs": [
            "138", 
            "21", 
            "76", 
            "75", 
            "161", 
            "162", 
            "163"
        ], 
        "title": "生活"
    }, 
    "138": {
        "url": HOME_URL + '/video/ent_funny_1.html',
        "title": "搞笑"
    }, 
    "21": {
        "url": HOME_URL + '/video/ent-life-1.html',
        "title": "日常"
    }, 
    "76": {
        "url": HOME_URL + '/video/ent-food-1.html',
        "title": "美食圈"
    }, 
    "75": {
        "url": HOME_URL + '/video/ent-animal-1.html',
        "title": "动物圈"
    }, 
    "161": {
        "url": HOME_URL + '/video/ent-handmake-1.html',
        "title": "手工"
    }, 
    "162": {
        "url": HOME_URL + '/video/ent-painting-1.html',
        "title": "绘画"
    }, 
    "163": {
        "url": HOME_URL + '/video/ent-sports-1.html',
        "title": "运动"
    }, 
    "119": {
        "url": HOME_URL + '/video/kichiku.html',
        "subs": [
            "22", 
            "26", 
            "126", 
            "127"
        ], 
        "title": "鬼畜"
    }, 
    "22": {
        "url": HOME_URL + '/video/ent-Kichiku-1.html',
        "title": "鬼畜调教"
    }, 
    "26": {
        "url": HOME_URL + '/video/douga-kichiku-1.html',
        "title": "音MAD"
    }, 
    "126": {
        "url": HOME_URL + '/video/kichiku-manual_vocaloid-1.html',
        "title": "人力VOCALOID"
    }, 
    "127": {
        "url": HOME_URL + '/video/kichiku-course-1.html',
        "title": "教程演示"
    }, 
    "155": {
        "url": HOME_URL + '/video/fashion.html',
        "subs": [
            "157", 
            "158", 
            "164", 
            "159"
        ], 
        "title": "时尚"
    }, 
    "157": {
        "url": HOME_URL + '/video/fashion-makeup-fitness-1.html',
        "title": "美妆"
    }, 
    "158": {
        "url": HOME_URL + '/video/fashion-clothing-1.html',
        "title": "服饰"
    }, 
    "164": {
        "url": HOME_URL + '/video/fashion-body-1.html',
        "title": "健身"
    }, 
    "159": {
        "url": HOME_URL + '/video/fashion-info-1.html',
        "title": "资讯"
    }, 
    "165": {
        "url": HOME_URL + '/video/ad-ad-1.html',
        "title": "广告"
    }, 
    "5": {
        "url": HOME_URL + '/video/ent.html',
        "subs": [
            "71", 
            "137", 
            "131"
        ], 
        "title": "娱乐"
    }, 
    "71": {
        "url": HOME_URL + '/video/ent-variety-1.html',
        "title": "综艺"
    }, 
    "137": {
        "url": HOME_URL + '/video/ent-circle-1.html',
        "title": "明星"
    }, 
    "131": {
        "url": HOME_URL + '/video/ent-korea-1.html',
        "title": "Korea相关"
    }, 
    "23": {
        "url": 'http://bangumi.bilibili.com/movie/',
        "subs": [
            "82", 
            "85", 
            "145", 
            "146", 
            "147", 
            "83"
        ], 
        "title": "电影"
    }, 
    "82": {
        "url": HOME_URL + '/video/movie-presentation-1.html',
        "title": "电影相关"
    }, 
    "85": {
        "url": HOME_URL + '/video/tv-micromovie-1.html',
        "title": "短片"
    }, 
    "145": {
        "url": HOME_URL + '/video/movie_west_1.html',
        "title": "欧美电影"
    }, 
    "146": {
        "url": HOME_URL + '/video/movie_japan_1.html',
        "title": "日本电影"
    }, 
    "147": {
        "url": HOME_URL + '/video/movie_chinese_1.html',
        "title": "国产电影"
    }, 
    "83": {
        "url": HOME_URL + '/video/movie-movie-1.html',
        "title": "其他国家"
    }, 
    "11": {
        "url": "http://bangumi.bilibili.com/tv/",
        "subs": [
            "15", 
            "34", 
            "86", 
            "128"
        ], 
        "title": "电视剧"
    }, 
    "15": {
        "url": HOME_URL + '/video/soap-three-1.html', 
        "title": "连载剧集"
    }, 
    "34": {
        "url": HOME_URL + '/video/tv-drama-1.html', 
        "title": "完结剧集"
    }, 
    "86": {
        "url": HOME_URL + '/video/tv-sfx-1.html', 
        "title": "特摄"
    }, 
    "128": {
        "url": HOME_URL + '/video/tv-presentation-1.html', 
        "title": "电视剧相关"
    }, 
    "177": {
        'url': HOME_URL + '/documentary',
        'title': '纪录片'
    },
}
