#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : leeyoshinari
import os
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import zhihu_spider.settings as cfg


class Login(object):
	def __init__(self):
		self.driver = None
		self.cookies = {}
		self.cookie_path = os.path.join(cfg.COOKIE_PATH, 'cookies.txt')

	def get_cookie(self):
		options = webdriver.ChromeOptions()
		options.add_argument('disable-infobars')    # disable infobars
		# Enter developer mode. If not, zhihu knows you use 'webdriver', and return 403 to you.
		options.add_experimental_option('excludeSwitches', ['enable-automation'])
		self.driver = webdriver.Chrome(chrome_options=options)
		self.driver.maximize_window()
		self.driver.get('https://www.zhihu.com')

		# switch to login mode
		WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'SignContainer-switch')))
		self.driver.find_element_by_class_name('SignContainer-switch').find_element_by_tag_name('span').click()

		self.driver.find_element(By.NAME, 'username').clear()
		self.driver.find_element(By.NAME, 'username').send_keys(cfg.USERNAME)   # input username

		self.driver.find_element(By.NAME, 'password').clear()
		self.driver.find_element(By.NAME, 'password').send_keys(cfg.PASSWORD)   # input password

		# press enter key, if captcha is needed, it can trigger captcha,
		# if captcha is not needed, it can login directly
		self.driver.find_element(By.NAME, 'password').send_keys(Keys.ENTER)

		# If captcha is needed. If captcha is English, a captcha is need to be inputted.
		# If captcha is Chinese, Chinese character need to be clicked, and enter any character to continue.
		images = 0
		try:
			images = self.driver.find_element_by_class_name('Captcha-englishContainer').find_element_by_tag_name('img').get_attribute('src')
			flag_input = 1
		except:
			images = self.driver.find_element_by_class_name('Captcha-chineseContainer').find_element_by_tag_name('img').get_attribute('src')
			flag_input = 0
		finally:
			pass

		if len(images) > 50:    # If captcha image is null
			if flag_input:
				self.driver.find_element_by_xpath('//input[@name="captcha"]').send_keys(input('请输入验证码：'))
			else:
				input('请确认是否点击完成')

		self.driver.find_element_by_xpath('//button[@type="submit"]').click()   # login

		time.sleep(2)   # wait to cookies loading
		cookie = self.driver.get_cookies()  # get cookies
		for c in cookie:
			self.cookies.update({c['name']: c['value']})

		self.driver.quit()

		self.write_cookie()

		return self.cookies

	def write_cookie(self):
		with open(self.cookie_path, 'w') as f:
			f.write(json.dumps(self.cookies))

	def read_cookie(self):
		if os.path.exists(self.cookie_path):
			return json.load(open(self.cookie_path, 'r', encoding='utf-8'))
		else:
			return self.get_cookie()

	def __del__(self):
		pass
