#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : leeyoshinari
import os
import re
import time
import json
import random

import redis
import scrapy
from scrapy.utils.project import get_project_settings

from zhihu_spider.login import Login
from zhihu_spider.MySQL import MySQL
from zhihu_spider.items import SoulmateAnswerItem, SoulmateCommentItem
from zhihu_spider.SaveImageAndGetBeauty import get_image_and_beauty


class SoulmateSpider(scrapy.Spider):
    name = 'soulmate'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/question/275359100/answers/updated']
    all_urls = []

    question_url = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data%5B*%5D.is_normal%2Cadmin_clo' \
                'sed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reaso' \
                'n%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_' \
                'content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2C' \
                'review_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvotin' \
                'g%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%3Bdata%5B*%5D.mark_infos%5B*%5' \
                'D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics&offset=20&limit=20&sort_by=updated'

    comment_url = 'https://www.zhihu.com/api/v4/answers/{}/root_comments?include=data%5B*%5D.author%2Ccollapse' \
                  'd%2Creply_to_author%2Cdisliked%2Ccontent%2Cvoting%2Cvote_count%2Cis_parent_author%2Cis_autho' \
                  'r&order=normal&limit=20&offset=0&status=open'

    setting = get_project_settings()
    cookies = None
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en',
        'User-Agent': random.choice(setting.get('USER_AGENT')),
    }

    IS_REDIS = setting.get('IS_REDIS')
    IS_BAIDU = setting.get('IS_BAIDU')

    MySQL()

    """连接redis"""
    if IS_REDIS:
        pool = redis.ConnectionPool(host=setting.get('REDIS_HOST'), port=setting.get('REDIS_PORT'),
                                    password=setting.get('REDIS_PASSWORD'), decode_responses=True)
        r_0 = redis.Redis(connection_pool=pool, db=0)
        r_1 = redis.Redis(connection_pool=pool, db=1)

    def start_requests(self):
        self.is_login()
        self.all_urls = self.read_start_urls()
        # yield scrapy.Request(url=self.question_url, cookies=self.cookies, callback=self.parse)
        for datas in self.all_urls:
            url = self.question_url.format(datas['questionId'])
            yield scrapy.Request(url=url, cookies=self.cookies, callback=self.parse, meta={'code': datas['code'], 'parentCode': datas['parentCode']})

    def parse(self, response):
        answer_res = json.loads(response.text)
        items = SoulmateAnswerItem()
        code = response.meta['code']

        answers = answer_res.get('data', None)
        if answers:
            for answer in answers:
                contents = answer.get('content')
                if len(contents) < 30:      # 如果回答的字数太少，则直接跳过
                    pass

                updateTime = str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answer.get('updated_time'))))
                if self.r_0.get(str(answer.get('id'))) == updateTime or str(answer.get('id'))=='550465108':   # 如果这个答案爬过，直接跳过，防止爬虫中断后重新爬取
                    print('{}：此回答未更新，跳过'.format(answer.get('id')))
                    time.sleep(random.randint(1, 2))
                    yield scrapy.Request(url=self.comment_url.format(answer.get('id')), headers=self.headers,
                                         cookies=self.cookies, callback=self.parser_comment, meta=response.meta)
                else:
                    if self.r_0.get(str(answer.get('id'))):
                        is_save = False
                    else:
                        is_save = True
                    self.r_0.set(str(answer.get('id')), updateTime)

                    items['answer_id'] = answer.get('id')  # 答案id
                    items['answerer_id'] = answer.get('author').get('id')  # 回答者id
                    items['beauty'] = -1  # 回答者颜值
                    items['gender'] = answer.get('author').get('gender')  # 回答者性别，知乎的性别
                    items['face_shape'] = -1    # 回答者脸型，默认值

                    user_url = answer.get('author').get('id')
                    if user_url == '0':        # 如果是匿名用户，id为0，则取答案的id命名图片
                        user_url = answer.get('id')
                    image_urls = self.get_imageurl(contents)    # 获取回答中的所有图片的url
                    result = get_image_and_beauty(user_url, image_urls, is_save=is_save, is_baidu=self.IS_BAIDU)  # 计算图片中人脸的颜值和性别，以及有效图片(有人脸的)数
                    if result['code'] == 0:
                        items['beauty'] = result['beauty']
                    elif result['code'] in [17, 18, 19, 222207]:    # 异常返回错误码，表明颜值检测不可用，终止爬虫
                        self.crawler.engine.close_spider(self, 'response msg error {}, job done!\n'
                                                         'code is {}'.format(response.text, result['code']))
                        break

                    if result['counter']:
                        items['gender'] = result['gender']  # 如果有人脸，则用人脸识别的性别修改从知乎上获取的性别
                        items['face_shape'] = result['face_shape']  # 如果有人脸，则用人脸识别的脸型修改默认值

                    items['pic_num'] = result['counter']    # 有效图片数，有人脸的图片

                    user_info = self.get_user_info(contents)
                    if user_info['gender'] != -1:
                        items['gender'] = user_info['gender']     # 如果回答中明确说明自己的性别，则替换已有的值

                    if user_info['height'] >= 180 and user_info['weight'] >= 65:
                        items['gender'] = 1

                    if 165 >= user_info['height'] > 135 and 50 >= user_info['weight'] > 30:
                        items['gender'] = 0

                    items['age'] = user_info['age']     # 回答者年龄
                    items['height'] = user_info['height']       # 回答者身高
                    items['weight'] = user_info['weight']       # 回答者体重
                    items['url_token'] = answer.get('author').get('url_token')  # 回答者token
                    items['name'] = answer.get('author').get('name')  # 回答者名字
                    items['follower_count'] = answer.get('author').get('follower_count')  # 回答者粉丝数
                    items['headline'] = answer.get('author').get('headline')  # 回答者签名
                    items['content'] = answer.get('content')  # 回答内容
                    items['voteup_count'] = answer.get('voteup_count')  # 答案点赞数
                    items['comment_count'] = answer.get('comment_count')  # 答案评论数
                    items['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answer.get('created_time')))
                    items['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(answer.get('updated_time')))
                    items['code'] = code

                    yield items

                    time.sleep(random.randint(1, 2))
                    yield scrapy.Request(url=self.comment_url.format(answer.get('id')), headers=self.headers,
                                         cookies=self.cookies, callback=self.parser_comment, meta=response.meta)

        if answer_res.get('paging'):
            if not answer_res.get('paging').get('is_end'):
                next_url = answer_res.get('paging').get('next')
                time.sleep(random.randint(1, 3))
                yield scrapy.Request(url=next_url, headers=self.headers, cookies=self.cookies,
                                     callback=self.parse, meta=response.meta)

    def parser_comment(self, response):
        comment_res = json.loads(response.text)
        comment_items = SoulmateCommentItem()
        comment_son = SoulmateCommentItem()
        code = response.meta['code']
        parentCode = response.meta['parentCode']

        comments = comment_res.get('data', None)
        for comment in comments:
            commentId = comment.get('id')
            createTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comment.get('created_time')))
            answerId = re.compile('answers/(\d+)/root_comments').findall(response.url)[-1]  # 答案id

            if self.r_1.get(str(commentId)) == createTime:
                print('{}：该评论已入库，跳过'.format(commentId))
            else:
                comment_items['answer_id'] = answerId
                comment_items['comment_id'] = commentId  # 评论id
                comment_items['parent_id'] = ''
                comment_items['comment_content'] = comment.get('content')  # 评论内容
                comment_items['vote_count'] = comment.get('vote_count')  # 点赞数
                comment_items['commenter_id'] = comment.get('author').get('member').get('id')  # 评论人id
                comment_items['commenter_token'] = comment.get('author').get('member').get('url_token')  # 评论人token
                comment_items['commenter_name'] = comment.get('author').get('member').get('name')  # 评论人名字
                comment_items['commenter_gender'] = comment.get('author').get('member').get('gender')  # 评论人性别
                comment_items['commenter_headline'] = comment.get('author').get('member').get('headline')  # 评论人签名
                comment_items['create_time'] = createTime
                comment_items['code'] = code
                comment_items['parentCode'] = parentCode % 10

                self.r_1.set(str(commentId), createTime)
                yield comment_items

            child_comments = comment.get('child_comments')
            for child in child_comments:
                comment_son['answer_id'] = answerId
                child_comment_id = child.get('id')  # 评论id
                child_create_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(child.get('created_time')))
                if self.r_1.get(str(child_comment_id)) == child_create_time:
                    print('{}：该评论已入库，跳过'.format(child_comment_id))
                else:
                    self.r_1.set(str(child_comment_id), child_create_time)
                    comment_son['comment_id'] = child_comment_id
                    comment_son['parent_id'] = commentId
                    comment_son['comment_content'] = child.get('content')  # 评论内容
                    comment_son['vote_count'] = child.get('vote_count')  # 点赞数
                    comment_son['commenter_id'] = child.get('author').get('member').get('id')  # 评论人id
                    comment_son['commenter_token'] = child.get('author').get('member').get('url_token')  # 评论人token
                    comment_son['commenter_name'] = child.get('author').get('member').get('name')  # 评论人名字
                    comment_son['commenter_gender'] = child.get('author').get('member').get('gender')  # 评论人性别
                    comment_son['commenter_headline'] = child.get('author').get('member').get('headline')  # 评论人签名
                    comment_son['create_time'] = child_create_time
                    comment_son['code'] = code
                    comment_son['parentCode'] = parentCode % 10

                    yield comment_son

        if comment_res.get('paging'):
            if not comment_res.get('paging').get('is_end'):
                next_url = '{}{}'.format('https://www.zhihu.com/api/v4/answers',
                                         comment_res.get('paging').get('next').split('answers')[1])
                time.sleep(random.randint(1, 2))
                yield scrapy.Request(url=next_url, headers=self.headers, cookies=self.cookies,
                                     callback=self.parser_comment, meta=response.meta)

    def is_login(self, res=None):
        if res:
            if '有问题，上知乎' in res.text or res.status != 200:
                login = Login()
                cookie_path = os.path.join(self.setting.get('COOKIE_PATH'), 'cookies.txt')
                if os.path.exists(cookie_path):
                    os.remove(cookie_path)

                self.cookies = login.get_cookie()
                del login
        else:
            login = Login()
            cookie_path = os.path.join(self.setting.get('COOKIE_PATH'), 'cookies.txt')
            if os.path.exists(cookie_path):
                self.cookies = login.read_cookie()
            else:
                self.cookies = login.get_cookie()
            del login

    def get_imageurl(self, content):
        if content:
            res = re.compile('data-original="(.*?)"').findall(content)
            return list(set(res))

    def read_start_urls(self):
        start_urls_path = os.path.join(self.setting.get('COOKIE_PATH'), 'start_urls.txt')
        return json.load(open(start_urls_path, 'r', encoding='utf-8'))

    def get_user_info(self, content):
        age = -1
        gender = -1
        height = -1
        weight = -1

        def filte(s):
            return list(filter(None, list(s)))[0]

        if content:
            ages = re.compile('(\d\d)岁|年龄(\d\d)').findall(content)
            years = re.compile('(\d\d)年').findall(content)
            if '女' in content[:7]:
                gender = 0
            elif '男' in content[:7]:
                gender = 1

            genders = re.compile('性别([男|女])|本人([男|女])|\d\d年([男|女])').findall(content)
            heights = re.compile('身高.*?([1][4-9]\d)|([1][4-9]\d)cm|([1][4-9]\d)CM').findall(content)
            h = re.compile('身高.*?([1]\.\d{1,2})|([1]\.\d{1,2})米|([1]\.\d{1,2})m|([1]\.\d{1,2})M').findall(content)
            weights = re.compile('体重.*?([3-9]\d)|([3-9]\d)kg|([3-9]\d)KG|([3-9]\d)Kg|([3-9]\d)公斤').findall(content)
            w = re.compile('体重.*?(\d{2,3})斤|(\d{2,3})斤').findall(content)

            if ages:
                age = int(filte(ages[0]))
            if years:
                year = int(years[0])
                if year > 50:
                    age = 121 - year
                elif year < 21:
                    age = 21 - year
            if age < 16 or age > 48:
                age = -1

            if heights:
                height = int(filte(heights[0]))
            elif h:
                height = float(filte(h[0])) * 100

            if weights:
                weight = int(filte(weights[0]))
            elif w:
                weight = float(filte(w[0])) / 2

            if genders:
                try:
                    gender = ['女', '男'].index(filte(genders[0]))
                except:
                    with open('error.txt', 'w') as f:
                        f.write(content)

            if '希望他' in content or '老阿姨' in content or '男的，' in content or '，女，' in content or '爱好男' in content \
                    or '我闺蜜' in content or '找个小哥哥' in content or '远嫁' in content or '嫁不出去' in content or '嘻嘻嘻' in content \
                    or '男朋友' in content or '可盐可甜' in content or '比我高' in content or '身高控' in content or '冷暴力' in content \
                    or '化妆' in content or '追剧' in content or '爱豆' in content or '喜欢的男孩' in content or '大龄女青年' in content or '独女' in content \
                    or '独生女' in content or '肤白' in content or '180以上' in content or '175以上' in content or '175及以上' in content or '男生较少' in content \
                    or '遇到他' in content or '颜值尚可' in content or '对男方' in content or '176以上' in content or '178以上' in content or '177以上' in content \
                    or '单身小哥哥' in content or '妆后' in content or '梨形身材' in content or '男生追过' in content or '陪我逛' in content \
                    or '年姑娘' in content or '夸可爱' in content or '本人女' in content or '身材苗条' in content or '高跟' in content \
                    or '优秀的小哥哥' in content or '甜甜的恋爱' in content or '小哥哥看这里' in content or '性别：女' in content \
                    or ' 女生 ' in content or 'p>女，' in content or '征男友' in content:
                gender = 0
            if '希望她' in content or '女的，' in content or '，男，' in content or '爱好女' in content or '找个小姐姐' in content \
                    or '到女朋友' in content or '有女朋友' in content or '遇到她' in content or '女生追过' in content or '不帅' in content \
                    or '对女方' in content or '本人男' in content or '老男孩' in content or '独生子，' in content or '，男生，' in content \
                    or '希望的她' in content or '独子' in content or '小姐姐看这里' in content or '性别：男' in content or ' 男生 ' in content \
                    or 'p>男，' in content or '征女友' in content:
                gender = 1

            if gender == 0 and height > 179:
                height = -1
            if gender == 1 and 160 > height > 100:
                height = -1

            if weight > 70 and gender == 0:
                weight = int(weight / 2)
            if 50 > weight > 1 and gender == 1:
                weight = -1

        return {'age': age, 'height': height, 'weight': weight, 'gender': gender}
