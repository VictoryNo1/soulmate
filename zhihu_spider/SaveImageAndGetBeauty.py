#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author : leeyoshinari
import os
import random
import base64
import urllib.request
import numpy as np
from aip import AipFace
from PIL import Image
import zhihu_spider.settings as cfg
import logging as log


def save_image(image_name, image):
    """Save image to local path.
        :param image: byte format
    """
    with open(image_name, 'wb') as f:
        f.write(image)


def read_image(image_name):
    """
    Read image, byte format
    :param image_name:
    """
    with open(image_name, 'rb') as fp:
        return fp.read()


def compress_image(image_name, threshold=1.5*1024*1024):
    """
    Compress image.
    :param image_name: image name
    :param threshold: threshold, byte
    """
    image_size = os.path.getsize(image_name)
    if image_size > threshold:
        with Image.open(image_name) as img:
            width, height = img.size
            if width >= height:
                new_width = int(np.sqrt(threshold/2))
                new_height = int(new_width * height / width)
            else:
                new_height = int(np.sqrt(threshold/2))
                new_width = int(new_height * width / height)

            resize_img = img.resize((new_width, new_height))
            resize_img.save(image_name)


def get_beauty(image, flag=True):
    """Get beauty by baidu.
        :param image: base64 format
        :param flag: whether retry.
    """
    res = {'error_code': 444444}
    options = {"face_field": "beauty,gender,faceshape", "max_face_num": 1, "face_type": "LIVE"}

    client = AipFace(cfg.AppID, cfg.ApiKey, cfg.SecretKey)
    try:
        res = client.detect(str(image), "BASE64", options)  # 百度限制图片大小2M，如果超过，会报错
    except Exception as e:
        print(e)
        image_name = str(random.randint(0, 100)) + '.jpg'  # 如果图片大于2M，则压缩图片
        save_image(image_name, base64.b64decode(image))
        compress_image(image_name)
        try:
            res = client.detect(read_image(image_name), "BASE64", options)  # 压缩图片后再次重试，如果仍然报错，则放弃这张图片
        except Exception as e:
            print(e)
        os.remove(image_name)

    # print(res)
    log.debug("get baidu result:{}".format(res))
    if res['error_code'] == 0:
        if res['result']['face_list'][0]['face_probability'] > 0.9 and res['result']['face_list'][0]['beauty'] < 40:
            return {'code': res['error_code'], 'beauty': res['result']['face_list'][0]['beauty'],
                    'gender': res['result']['face_list'][0]['gender']['type'],
                    'face_shape': res['result']['face_list'][0]['face_shape']['type']}
        else:
            return {'code': 444444, 'beauty': -1, 'gender': -1, 'face_shape': -1}
    elif res['error_code'] in [222201, 222205, 222206, 222300, 222302, 222901, 222902]:  # 出现这些错误码，可以再重试一次
        if flag:
            get_beauty(image, flag=False)
        else:
            return {'code': res['error_code'], 'beauty': -1, 'gender': -1, 'face_shape': -1}
    else:
        return {'code': res['error_code'], 'beauty': -1, 'gender': -1, 'face_shape': -1}


def get_image_and_beauty(user_id, image_urls, is_save=True, is_baidu=True):
    log.debug("image_is_save:{}".format(is_save))
    G = ['female', 'male']
    if len(image_urls) and isinstance(image_urls, list):
        if not os.path.exists(cfg.IMAGES_PATH):
            os.mkdir(cfg.IMAGES_PATH)

        ind = 1
        code = []
        beauty = []
        gender = []
        face_shape = [-1]
        flag = 0
        log.debug("image_urls_length:{}".format(len(image_urls)))
        for img_url in image_urls:
            try:
                img_res = urllib.request.urlopen(img_url).read()  # 如果图片获取不到，放弃该图片
            except Exception as e:
                print("can't get image:\n")
                print(e, img_url)
                continue
            log.debug("is_baidu:{}".format(is_baidu))
            if is_baidu:
                result = get_beauty(base64.b64encode(img_res).decode())
                # code.append(result['code'] if isinstance(result['code'], int) else 444444)
                # beauty.append(result['beauty'])
                log.debug("get_beauty:{}".format(result))
                if result['code'] == 0:
                    code.append(result['code'])
                    beauty.append(result['beauty'])
                    gender.append(G.index(result['gender']))
                    face_shape.append(result['face_shape'])
                    flag = 1
                    if is_save:
                        image_name = os.path.join(cfg.IMAGES_PATH, '{}_{}.jpg'.format(user_id, ind))
                        print("write image")
                        print("image name:",image_name)
                        save_image(image_name, img_res)
                    ind += 1
                else:
                    image_name = os.path.join(cfg.IMAGES_PATH, '{}_{}.jpg'.format(user_id, ind))
                    print("write image")
                    print("image name:",image_name)
                    save_image(image_name, img_res)
                ind += 1
            else:
                if is_save:
                    image_name = os.path.join(cfg.IMAGES_PATH, '{}_{}.jpg'.format(user_id, ind))
                    save_image(image_name, img_res)
                ind += 1

        if flag:
            return {'code': min(code), 'beauty': np.round(max(beauty)), 'gender': np.round(np.mean(gender)),
                    'counter': len(gender), 'face_shape': face_shape[-1]}
        else:
            return {'code': 444444, 'beauty': -1, 'gender': -1, 'counter': 0, 'face_shape': -1}
    else:
        return {'code': 444444, 'beauty': -1, 'gender': -1, 'counter': 0, 'face_shape': -1}


if __name__ == '__main__':
    print(get_image_and_beauty('123', ['https://pic2.zhimg.com/v2-6238a498f790a5bae2d1c9c20789f799_r.jpg']))
