#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @File   : main.py
# @Author : leeyoshinari


import os
import sys
from scrapy.cmdline import execute


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy', 'crawl', 'soulmate'])
