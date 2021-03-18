#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : leeyoshinari
import re
import time
import copy
import numpy as np
import colorsys
import jieba
import pymysql
import matplotlib.pyplot as plt
from wordcloud import WordCloud

import zhihu_spider.settings as cfg


def ReadDateFromMySQL():
	db = pymysql.connect(cfg.MYSQL_HOST, cfg.MYSQL_USER, cfg.MYSQL_PASSWORD, cfg.MYSQL_DATABASE)
	cursor = db.cursor()

	answer_sql = """SELECT a.answer_id, a.answerer_id, a.url_token, a.name, a.gender, a.age, a.height, a.weight, a.beauty, a.voteup_count, a.comment_count, a.create_time, a.update_time, a.headline, a.content FROM answers a JOIN (select answer_id answer_id , MAX(id) id from answers where code=110 group by answer_id) as b ON a.id=b.id;"""
	comment_sql = """SELECT content, url_token, create_time FROM comments_1 where code=110;"""

	cursor.execute(answer_sql)
	answer_res = cursor.fetchall()

	cursor.execute(comment_sql)
	comment_res = cursor.fetchall()

	return {'answer': answer_res, 'comment': comment_res}


def counter_per_value(mylist, ordered=None):
	"""统计列表中每个元素的个数，去掉重复的
	:param mylist 待统计的列表
	:param ordered mylist列表中元素的顺序，如果不传入该参数，则按列表中每个元素依次出现的顺序排序

	:return mylist列表中每个元素的个数
	"""
	res = {}
	if not ordered:
		ordered = set(mylist)
	for order in ordered:
		res.update({str(order): mylist.count(order)})

	return res


def list1_and_list2(list1, list2):
	if len(list1) == len(list2):
		male = []
		female = []
		for i in range(len(list1)):
			if list1[i] > 0 and list2[i] >= 0:
				if list2[i] == 0:
					female.append(list1[i])
				if list2[i] == 1:
					male.append(list1[i])

		male.sort()
		female.sort()
		return male, female
	else:
		print("长度不相等")


def list2_of_per_list1(list1, list2, ordered1=None, ordered2=None):
	"""
	每个list1中属于list2的个数，例如list1为身高列表，list2为性别列表，返回的是每个身高下，男女的数量
	:param list1: 列表1
	:param list2: 列表2
	:param ordered1: 列表1的元素排序
	:param ordered2: 列表2的元素排序
	:return: 返回统计后的结果
	"""
	res = {}
	if not ordered1:
		ordered1 = set(list1)
	for ordered in ordered1:
		listed = [list2[i] for i in range(len(list1)) if list1[i] == ordered]
		res.update({str(ordered): counter_per_value(listed, ordered2)})

	return res


def random_color(num, bright=True):
	"""
	生产随机颜色
	:param num: 生产随机颜色的数量
	:param bright: 颜色亮度
	:return: 生成的颜色列表，RGB格式
	"""
	brightness = 0.8 if bright else 0.7
	hsv = [(i / num, 1, brightness) for i in range(num)]
	colors = list(map(lambda c: colorsys.hsv_to_rgb(*c), hsv))
	np.random.shuffle(colors)
	return colors


def plot_bar(bar_values, title):
	"""
	画柱状图，并保存到本地
	:param bar_values: 字典类型
	:param title: 画出的图片标题
	"""
	if isinstance(bar_values, dict):
		label = []
		value = []
		for k, v in bar_values.items():
			label.append(k)
			value.append(v)

		plt.figure(title, figsize=[19.2, 10.8])
		index = np.arange(len(value)) * 0.5 + 0.2
		plt.bar(index, value, 0.4, color=random_color(len(value)))
		plt.xlim((0, index[-1] + 0.6))
		for x, y in zip(index, value):
			plt.text(x, y, y, ha='center', va='bottom')

		plt.xticks(index, label, rotation=45)
		plt.savefig('{}.png'.format(title), bbox_inches='tight')
		plt.show()
	else:
		print('TypeError: param must be dict.')


def plot_pie(pie_values, title):
	"""
	画饼状图，并保存到本地
	:param pie_values: 字典类型
	:param title: 画出的图片标题
	"""
	label = []
	value = []
	for k, v in pie_values.items():
		label.append(k)
		value.append(v)

	explode = tuple([0.02] * len(label))
	plt.figure('title', figsize=[9.6, 7.2])
	plt.pie(value, labels=label, colors=random_color(len(label)), autopct='%.2f%%', shadow=True, explode=explode)
	plt.axis('equal')
	plt.savefig('{}.png'.format(title), bbox_inches='tight')
	plt.show()


def plot_line(line_value, title):
	"""
	画折线图
	:param line_value: 字典类型
	:param title: 画出的图片标题
	"""
	label = []
	value = []
	for k, v in line_value.items():
		label.append(k)
		value.append(v)

	index = np.arange(len(label))
	plt.figure(title, figsize=[19.2, 10.8])
	plt.plot(index, value, color='red', marker='^', markersize=6)
	plt.xticks(index, label, rotation=45)
	for x, y in zip(index, value):
		plt.text(x, y, y, ha='center', va='bottom')
	plt.ylim((0, max(value)+10))
	plt.savefig('{}.png'.format(title), bbox_inches='tight')
	plt.show()


def word_frequency(contents, title):
	"""
	生成词云图
	:param contents: 待生成词云图的文本, 列表
	:param title: 生成的词云图的标题
	"""
	exclude_w = {'呢', '不', '哈哈', '一个', '还是', '评论', '删除', '可以', '自己', '虽然', '请问', '其实', '怎么', '这么', '那么', '答主', '所以',
				 '你好', '这个', '加油', '一点', '哪里', '是不是', '有点', '我', '你', '的', '是', '人', '了', '吧', '呀', '在', '啊', '吗', '也', '该'
				 '哈哈哈', '都', '就'}
	if isinstance(contents, list):
		text = [" ".join(jieba.cut(content, cut_all=False)) for content in contents]

		word_cloud = WordCloud(width=1920, height=1080, font_path='simhei.ttf',
							   background_color='white', stopwords=exclude_w).generate(' '.join(text))

		plt.figure('title')
		plt.imshow(word_cloud)
		plt.axis('off')
		plt.show()
		plt.imsave('{}.png'.format(title), word_cloud)
	else:
		print('TypeError: param must be list.')


def counter_beauty(beauties):
	res = []
	for beauty in beauties:
		res.append(int(int(beauty) / 10))

	r = {}
	for i in range(10):
		key = '{}-{}'.format(i, i+1)
		num = res.count(i)
		if num > 0:
			r.update({str(key): num})

	return r


def maintain_answer_time(create_time, update_time):
	"""
	Calculate the time that user maintains answer.
	:param create_time: '2019-04-09 00:00:00'
	:param update_time: '2019-04-09 00:00:00'
	:return: interval(s)
	"""
	create_t = [time.mktime(time.strptime(ct, '%Y-%m-%d %H:%M:%S')) for ct in create_time]
	update_t = [time.mktime(time.strptime(ut, '%Y-%m-%d %H:%M:%S')) for ut in update_time]

	interval = []
	for x, y in zip(update_t, create_t):
		interval.append(x - y)

	return interval


def deal_age(ages):
	num = []
	sex = copy.deepcopy(ages)
	for k, v in sex.items():
		if int(k) > 40:
			num.append(v)
			del ages[k]

	ages.update({'≥41': sum(num)})
	return ages


def average_height(height):
	total = 0
	sum_height = 0
	for k, v in height.items():
		sum_height += int(k) * v
		total += v

	return sum_height / total


def create_trend(create_time):
	"""
	Answers' num that created every month.
	:param create_time: '2019-04-09 00:00:00'
	:return: The counter of every month.
	"""
	month = []
	for t in create_time:
		month.append(str(t)[:7])

	return counter_per_value(month, sorted(set(month)))


def update_trend(update_time):
	"""
	Answers' updated time.
	:param update_time:
	:return: The counter of every hour.
	"""
	time24 = []
	for t in update_time:
		time24.append(str(t)[11:13])

	return counter_per_value(time24, sorted(set(time24)))


def pre_deal_content(content):
	"""
	将评论中的汉字提取出来,过滤英文 数字和标点符号
	:param content:
	:return:
	"""
	con = re.compile('([\u4e00-\u9fa5]+)').findall(content)
	return ','.join(con)


def gender_content(gender, content):
	male_content = []
	female_content = []

	for i in range(len(content)):
		if gender[i] == 0:
			female_content.append(content[i])
		if gender[i] == 1:
			male_content.append(content[i])

	return male_content, female_content


def comment_url_token(url_token):
	token = []
	count = []
	for k, v in url_token.items():
		token.append(k)
		count.append(v)

	return token, count


def comment_word_cloud(content, url_token, sort_token):
	"""
	Draw top5' comments word cloud.
	:param content: all content
	:param url_token: all url_token
	:param sort_token: top5 url_token
	:return:
	"""
	for token in sort_token:
		index = [i for i in range(len(url_token)) if url_token[i] == token]
		word_cloud = [content[j] for j in index]
		word_frequency(word_cloud, token)


def deal_answer(answers):
	answer_ids = []
	names = []
	genders = []
	ages = []
	heights = []
	weights = []
	beauties = []
	face_shapes = []
	pic_nums = []
	follower_counts = []
	headlines = []
	contents = []
	voteup_counts = []
	comment_counts = []
	create_times = []
	update_times = []

	for i in range(len(answers)):
		answer_ids.append(answers[i][0])
		names.append(answers[i][3])
		genders.append(answers[i][4])
		ages.append(answers[i][5])
		heights.append(answers[i][6])
		weights.append(answers[i][7])
		beauties.append(answers[i][8])
		# face_shapes.append(answers[i][9])
		# pic_nums.append(answers[i][10])
		# follower_counts.append(answers[i][11])
		headlines.append(answers[i][13])
		contents.append(pre_deal_content(answers[i][14]))
		voteup_counts.append(answers[i][9])
		comment_counts.append(answers[i][10])
		create_times.append(str(answers[i][11]))
		update_times.append(str(answers[i][12]))

	filter_gender = [['unknown', 'female', 'male'][x+1] for x in genders]
	print('共统计出{}个性别'.format(len(filter_gender)))
	plot_pie(counter_per_value(filter_gender), 'gender')

	filter_age = list(filter(lambda x: x > 0, ages))
	print('共统计出{}个有效年龄'.format(len(filter_age)))
	filter_age.sort()
	plot_bar(deal_age(counter_per_value(filter_age)), 'age')
	male_age, female_age = list1_and_list2(ages, genders)
	plot_bar(deal_age(counter_per_value(male_age)), 'male age')
	plot_bar(deal_age(counter_per_value(female_age)), 'female age')

	filter_height = list(filter(lambda x: x > 100, heights))
	print('共统计出{}个有效身高'.format(len(filter_height)))
	filter_height.sort()
	plot_bar(counter_per_value(filter_height), 'height')
	male_height, female_height = list1_and_list2(heights, genders)
	plot_bar(counter_per_value(male_height), 'male height')
	plot_bar(counter_per_value(female_height), 'female height')
	print('男生身高平均值为{:.2f}'.format(average_height(counter_per_value(male_height))))
	print('女生身高平均值为{:.2f}'.format(average_height(counter_per_value(female_height))))

	filter_weight = list(filter(lambda x: x > 30, weights))
	print('共统计出{}个有效体重'.format(len(filter_weight)))
	filter_weight.sort()
	plot_bar(counter_per_value(filter_weight), 'weight')
	male_weight, female_weight = list1_and_list2(weights, genders)
	plot_bar(counter_per_value(male_weight), 'male weight')
	plot_bar(counter_per_value(female_weight), 'female weight')

	filter_beauty = list(filter(lambda x: x > 0, beauties))
	print('共统计出{}个颜值信息'.format(len(filter_beauty)))
	filter_beauty.sort()
	plot_bar(counter_beauty(filter_beauty), 'beauty')
	male_beauty, female_beauty = list1_and_list2(beauties, genders)
	plot_bar(counter_beauty(male_beauty), 'male beauty')
	plot_bar(counter_beauty(female_beauty), 'female beauty')

	headline = list(filter(None, headlines))
	word_frequency(headline, '个性签名常用的字词')

	male_voteup, female_voteup = list1_and_list2(voteup_counts, genders)
	print('男生回答下的平均点赞数为{:.2f}，女生回答下的平均点赞数为{:.2f}'.format(np.mean(male_voteup), np.mean(female_voteup)))

	male_comment, female_comment = list1_and_list2(comment_counts, genders)
	print('男生回答下的平均评论数为{:.2f}，女生回答下的平均评论数为{:.2f}'.format(np.mean(male_comment), np.mean(female_comment)))

	interval = maintain_answer_time(create_times, update_times)
	plot_line(create_trend(create_times), 'create_num of month')
	plot_bar(update_trend(update_times), 'update_num of hour')
	sort_ind = np.argsort(np.array(interval))
	# sort_interval = np.array(interval)[sort_ind]
	sort_create = np.array(create_times)[sort_ind]
	sort_update = np.array(update_times)[sort_ind]
	print('   create_time              update_time   ')
	print('*'*45)
	for ind in range(1, 11):
		print('{}      {}'.format(sort_create[-ind], sort_update[-ind]))

	male_content, female_content = gender_content(genders, contents)
	word_frequency(male_content, 'male answer content')
	word_frequency(female_content, 'female answer content')


def deal_comment(comments):
	content = []
	url_token = []
	create_time = []
	for j in range(len(comments)):
		content.append(pre_deal_content(comments[j][0]))
		url_token.append(comments[j][1])
		create_time.append(str(comments[j][2]))

	word_frequency(content, '打招呼评论词云图')

	url_token_counter = counter_per_value(list(filter(None, url_token)))
	token, count = comment_url_token(url_token_counter)
	sort_ind = np.argsort(np.array(count))
	sort_count = np.array(count)[sort_ind]
	sort_token = np.array(token)[sort_ind]
	print('   url_token              counter   ')
	print('*' * 45)
	for ind in range(1, 11):
		print('{}            {}'.format(sort_token[-ind][:4]+'***', sort_count[-ind]))

	comment_word_cloud(content, url_token, sort_token[-3:])

	index = [i for i in range(len(url_token)) if url_token[i] == sort_token[-1]]
	sort_first_create_time = [create_time[j] for j in index]
	plot_line(create_trend(sort_first_create_time), 'sort_first_create_time_pre_month')

	plot_bar(update_trend(create_time), 'comment_num of hour')


def main():
	result = ReadDateFromMySQL()
	answers = result['answer']
	comments = result['comment']
	print('总共有{}个回答，共计有{}个评论'.format(len(answers), len(comments)))
	deal_answer(answers)
	deal_comment(comments)


if __name__ == '__main__':
	main()
