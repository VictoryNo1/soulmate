# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import copy
import traceback
from twisted.enterprise import adbapi
from zhihu_spider.items import SoulmateAnswerItem, SoulmateCommentItem


class ZhihuSpiderPipeline(object):
    def process_item(self, item, spider):
        return item


class MySQLTwistedPipeline(object):
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def from_settings(cls, settings):
        parms = dict(
            host=settings['MYSQL_HOST'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            database=settings['MYSQL_DATABASE']
        )

        dbpool = adbapi.ConnectionPool('pymysql', **parms)

        return cls(dbpool)

    def process_item(self, item, spider):
        asyn_item = copy.deepcopy(item)
        query = self.pool.runInteraction(self.write_item, asyn_item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        print(type(item), failure, type(spider))

    def write_item(self, cursor, item):
        if isinstance(item, SoulmateAnswerItem):
            insert_sql = "INSERT INTO answers (answer_id, answerer_id, url_token, name, gender, age, height, weight, beauty, face_shape, pic_num, follower_count, headline, content, voteup_count, comment_count, create_time, update_time, code) VALUES {}".format((item['answer_id'], item['answerer_id'],
                          item['url_token'], item['name'], item['gender'], item['age'], item['height'],
                          item['weight'], item['beauty'], item['face_shape'], item['pic_num'],
                          item['follower_count'], item['headline'], item['content'], item['voteup_count'],
                          item['comment_count'], item['create_time'], item['update_time'], item['code']))

            try:
                cursor.execute(insert_sql)
            except Exception as e:
                # print(traceback.format_exc())
                print('answer: {}'.format(e))

        if isinstance(item, SoulmateCommentItem):
            comment_sql = "INSERT IGNORE INTO comments_{} VALUE {}".format(item['parentCode'], (item['answer_id'], item['comment_id'], item['parent_id'],
                           item['comment_content'], item['vote_count'], item['commenter_id'], item['commenter_token'],
                           item['commenter_name'], item['commenter_gender'], item['commenter_headline'],
                           item['create_time'], item['code']))

            try:
                cursor.execute(comment_sql)
            except Exception as e:
                # print(traceback.format_exc())
                print('comment: {}'.format(e))
