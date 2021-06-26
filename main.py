#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File   : main.py
# @Author : leeyoshinari


import os
import sys
from scrapy.cmdline import execute
import logging

logging.basicConfig(filename='log.txt',level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s', datefmt='%a, %d %b %Y %H:%M:%S')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy', 'crawl', 'soulmate'])
