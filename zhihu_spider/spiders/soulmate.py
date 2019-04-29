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

	question_url = 'https://www.zhihu.com/api/v4/questions/275359100/answers?include=data%5B*%5D.is_normal%2Cadmin_clo' \
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

	MySQL()

	"""连接redis"""
	if setting.get('IS_REDIS'):
		pool = redis.ConnectionPool(host=setting.get('REDIS_HOST'), port=setting.get('REDIS_PORT'),
		                            password=setting.get('REDIS_PASSWORD'), decode_responses=True)
		r = redis.Redis(connection_pool=pool)

	def start_requests(self):
		self.is_login()
		yield scrapy.Request(url=self.question_url, cookies=self.cookies, callback=self.parse)

	def parse(self, response):
		answer_res = json.loads(response.text)
		items = SoulmateAnswerItem()

		answers = answer_res.get('data', None)
		if answers:
			for answer in answers:
				contents = answer.get('content')
				if len(contents) < 30:      # 如果回答的字数太少，则直接跳过
					continue

				if self.setting.get('IS_REDIS'):
					if self.r.get(str(answer.get('id'))):   # 如果这个答案爬过，直接跳过，防止爬虫中断后重新爬取
						print('{}此回答已爬过'.format(answer.get('id')))
						continue
					else:
						self.r.set(str(answer.get('id')), 1)

				items['answer_id'] = answer.get('id')  # 答案id
				items['answerer_id'] = answer.get('author').get('id')  # 回答者id
				items['beauty'] = -1  # 回答者颜值
				items['gender'] = answer.get('author').get('gender')  # 回答者性别，知乎的性别
				items['face_shape'] = -1    # 回答者脸型，默认值

				user_url = answer.get('author').get('id')
				if user_url == '0':        # 如果是匿名用户，id为0，则取答案的id命名图片
					user_url = answer.get('id')
				image_urls = self.get_imageurl(contents)    # 获取回答中的所有图片的url
				result = get_image_and_beauty(user_url, image_urls)  # 计算图片中人脸的颜值和性别，以及有效图片(有人脸的)数
				if result['code'] == 0:
					items['beauty'] = result['beauty']
				elif result['code'] in [17, 18, 19, 222207]:    # 异常返回错误码，表明颜值检测不可用，终止爬虫
					self.crawler.engine.close_spider(self, 'response msg error {}, job done!\n'
					                                 'code is {}'.format(response.text, result['code']))
					break

				items['pic_num'] = result['counter']    # 有效图片数，有人脸的图片

				user_info = self.get_user_info(contents)
				if user_info['gender'] != -1:
					items['gender'] = user_info['gender']     # 如果回答中明确说明自己的性别，则替换已有的值

				if result['counter']:
					items['gender'] = result['gender']  # 如果有人脸，则用人脸识别的性别修改从知乎上获取的性别
					items['face_shape'] = result['face_shape']  # 如果有人脸，则用人脸识别的脸型修改默认值

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

				yield items

				time.sleep(random.randint(1, 3))
				yield scrapy.Request(url=self.comment_url.format(answer.get('id')), headers=self.headers,
				                     cookies=self.cookies, callback=self.parser_comment)

		if answer_res.get('paging'):
			if not answer_res.get('paging').get('is_end'):
				next_url = answer_res.get('paging').get('next')
				time.sleep(random.randint(1, 3))
				yield scrapy.Request(url=next_url, headers=self.headers, cookies=self.cookies,
				                     callback=self.parse)

	def parser_comment(self, response):
		comment_res = json.loads(response.text)
		comment_items = SoulmateCommentItem()

		comments = comment_res.get('data', None)
		for comment in comments:
			comment_items['answer_id'] = re.compile('answers/(\d+)/root_comments').findall(response.url)[-1]  # 答案id
			comment_items['comment_id'] = comment.get('id')  # 评论id
			comment_items['comment_content'] = comment.get('content')  # 评论内容
			comment_items['vote_count'] = comment.get('vote_count')  # 点赞数
			comment_items['commenter_id'] = comment.get('author').get('member').get('id')  # 评论人id
			comment_items['commenter_token'] = comment.get('author').get('member').get('url_token')  # 评论人token
			comment_items['commenter_name'] = comment.get('author').get('member').get('name')  # 评论人名字
			comment_items['commenter_gender'] = comment.get('author').get('member').get('gender')  # 评论人性别
			comment_items['commenter_headline'] = comment.get('author').get('member').get('headline')  # 评论人签名
			comment_items['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comment.get('created_time')))

			yield comment_items

		if comment_res.get('paging'):
			if not comment_res.get('paging').get('is_end'):
				next_url = '{}{}'.format('https://www.zhihu.com/api/v4/answers',
				                         comment_res.get('paging').get('next').split('answers')[1])
				time.sleep(random.randint(1, 3))
				yield scrapy.Request(url=next_url, headers=self.headers, cookies=self.cookies,
				                     callback=self.parser_comment)

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
					age = 119 - year
				elif year < 19:
					age = 19 - year
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

			if weight > 70 and gender == 0:
				weight = weight / 2

		return {'age': age, 'height': height, 'weight': weight, 'gender': gender}
