#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : leeyoshinari
import pymysql
import zhihu_spider.settings as cfg


class MySQL(object):
	def __init__(self):
		self.db = None
		self.cursor = None

		self.connect()

	def connect(self):
		self.db = pymysql.connect(cfg.MYSQL_HOST, cfg.MYSQL_USER, cfg.MYSQL_PASSWORD, cfg.MYSQL_DATABASE)
		self.cursor = self.db.cursor()

		answers_sql = """
			  CREATE TABLE IF NOT EXISTS answers (
			          id INT NOT NULL AUTO_INCREMENT,
			          answer_id VARCHAR(20) NOT NULL,
			          answerer_id VARCHAR(50),
			          url_token VARCHAR(100),
			          name VARCHAR(100),
			          gender INT,
			          age INT,
			          height INT,
			          weight INT,
			          beauty INT,
			          face_shape VARCHAR(8),
			          pic_num INT,
			          follower_count INT,
			          headline VARCHAR(255),
			          content LONGTEXT,
			          voteup_count INT,
			          comment_count INT,
			          create_time DATETIME,
			          update_time DATETIME,
			          code INT,
			          PRIMARY KEY (id))"""

		self.cursor.execute(answers_sql)

		comments_sql = """
			  CREATE TABLE IF NOT EXISTS comments (
					  answer_id VARCHAR(20) NOT NULL,
					  comment_id VARCHAR(20),
					  parent_id VARCHAR(20),
					  content LONGTEXT,
					  vote_count INT,
					  commenter_id VARCHAR(50),
					  url_token VARCHAR(100),
					  name VARCHAR(100),
					  gender INT,
					  headline VARCHAR(255),
					  create_time DATETIME,
					  code INT,
					  PRIMARY KEY (comment_id))"""

		self.cursor.execute(comments_sql)

	def __del__(self):
		del self.db
		del self.cursor
