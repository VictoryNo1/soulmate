# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class SoulmateAnswerItem(scrapy.Item):
    answer_id = scrapy.Field()       # 答案id
    answerer_id = scrapy.Field()     # 回答者id
    url_token = scrapy.Field()       # 回答者token
    name = scrapy.Field()            # 回答者名字
    gender = scrapy.Field()          # 回答者性别
    age = scrapy.Field()             # 回答者年龄
    height = scrapy.Field()          # 回答者身高
    weight = scrapy.Field()          # 回答者体重
    beauty = scrapy.Field()          # 回答者颜值
    face_shape = scrapy.Field()      # 回答者脸型
    pic_num = scrapy.Field()         # 回答者上传的有效图片数
    follower_count = scrapy.Field()  # 回答者粉丝数
    headline = scrapy.Field()        # 回答者签名
    content = scrapy.Field()         # 回答内容
    voteup_count = scrapy.Field()    # 答案点赞数
    comment_count = scrapy.Field()   # 答案评论数
    create_time = scrapy.Field()     # 答案创建时间
    update_time = scrapy.Field()     # 答案更新时间
    code = scrapy.Field()           # 地区


class SoulmateCommentItem(scrapy.Item):
    answer_id = scrapy.Field()           # 答案id
    comment_id = scrapy.Field()          # 评论id
    parent_id = scrapy.Field()      # 表明该评论是哪个评论下面的回复
    comment_content = scrapy.Field()     # 评论内容
    vote_count = scrapy.Field()          # 点赞数
    commenter_id = scrapy.Field()        # 评论人id
    commenter_token = scrapy.Field()     # 评论人token
    commenter_name = scrapy.Field()      # 评论人名字
    commenter_gender = scrapy.Field()    # 评论人性别
    commenter_headline = scrapy.Field()  # 评论人签名
    create_time = scrapy.Field()         # 评论创建时间
    code = scrapy.Field()
    parentCode = scrapy.Field()         # 分表，往哪个表写数据


# 10 -- 全国数据
# 11 -- 湖北（110）、重庆（111）、安徽（112）
# 12 -- 北京（120）、天津（121）、河北（122）
# 13 -- 山东（130）、河南（131）、山西（132）
# 14 -- 江苏（140）、浙江（141）
# 15 -- 福建（150）、江西（151）、湖南（152）
# 16 -- 广东（160）、广西（161）
# 17 -- 内蒙古（170）、宁夏（171）、甘肃（172）、新疆（173）、西藏（174）、青海（175）、云南（176）
# 18 -- 四川（180）、陕西（181）、贵州（182）、海南（183）
# 19 -- 辽宁（190）、吉林（191）、黑龙江（192）、上海（193）
