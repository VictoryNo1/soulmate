# soulmate

本项目爬取了知乎中[你的择偶标准是怎样的？](https://www.zhihu.com/question/275359100/answer/622591897)下所有回答，提取出答主的一些信息。

## 概览
1.共爬取24539个回答，和248718条评论.</br>
2.共爬取20319条性别信息，性别占比如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/gender.png)</br>
3.共爬取11293条年龄数据，年龄分布如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/age.png)</br>
4.共爬取12584条身高数据，身高分布如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/height.png)</br>
5.共爬取8487条体重数据，体重分布如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/weight.png)</br>
6.共爬取2583条颜值数据，颜值分布如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/beauty.png)</br>
7.答主个性签名词云图如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/headline.png)</br>
8.该问题下的回答趋势图如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/create_num%20of%20month.png)</br>
9.所有评论的词云图如下图所示：</br>
![](https://github.com/leeyoshinari/soulmate/blob/master/res/comment.png)</br>

10.更多数据[请点击](https://mp.weixin.qq.com/s?__biz=Mzg5OTA3NDk2MQ==&mid=2247483738&idx=1&sn=664f2faed886d2f5715c640a5c390c1f&chksm=c0599fa4f72e16b2979ed378dc19033b4831bf0202962781c9f4991725ae34f468bce24a9302&token=11969908&lang=zh_CN#rd).</br>

## 总体思路
1.登陆：使用selenium模拟登陆知乎，获取cookies，然后将cookies保存至本地，为了避免被反爬，每次爬取随机延时</br>
2.数据库：MySQL数据库存储爬取的数据</br>
3.redis：保存爬取的回答ID，避免爬虫中断后重新爬取。如何快速在windows下安装linux版本的redis，[请点击](https://blog.csdn.net/leeyoshinari/article/details/89070281)</br>
4.性别：首先获取知乎性别，但知乎性别很多都是假的，于是用图片的人脸识别出的性别替换知乎性别，又由于图片可能是表情包，于是又从回答内容中正则出性别，以保证性别获取尽可能准确。</br>
5.颜值：使用百度人脸识别API，为了尽量减少表情包的影响，屏蔽掉人脸概览小于0.7的图片和颜值小于40的图片。</br>
6.数据清洗：</br>
>(1)性别为女的体重进行转换和过滤，将大于80的数据转换成kg，将小于40的数据屏蔽掉</br>
(2)性别为男的体重进行过滤，将小于50的数据屏蔽掉</br>
(3)通过身高过滤性别，身高大于180的统一为男，身高小于160的统一为女</br>
(4)通过评论者的性别过滤答主的性别，评论中性别为男的居多，则答主性别为女；反之亦然</br>
(5)通过回答内容过滤性别，例如“希望他”、“，女，”、“老阿姨”、“女的，活的”、“爱好男”、“要求男”等</br>
(6)再次通过性别过滤体重</br>
  
  以上牺牲少数，保证多数数据正确，不可避免一些数据过滤出错，因此结果仅供参考。</br>
  
## Installation
1. Clone soulmate repository
	```Shell
	$ git clone https://github.com/leeyoshinari/soulmate.git
    $ cd soulmate
	```

2. Scraping
	```Shell
	$ python main.py
	```
	
3. Plotting
	```Shell
	$ python dealData.py
	```

## Requirements
>1. matplotlib
>2. pymysql
>3. redis
>4. scrapy
>5. jieba
>6. wordcloud
>7. baidu-api
>8. selenium
>9. chrome webdriver
