# coding:utf-8
# __user__ = hiicy redldw
# __time__ = 2019/12/3
# __file__ = clean
# __desc__ =

import redis
import pymysql
import sys,os
path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)
from config import Config as CF

conn = pymysql.connect(**CF.mysql_config)
cursor = conn.cursor()
rds = redis.Redis(CF.redis_url,CF.redis_port)
def clean_user():
    rurls: set = rds.smembers("user")
    rurls = {rurl.decode("utf-8") for rurl in rurls}
    cursor.execute("select url from article_info")
    murls = cursor.fetchall()
    mmurls = {url[0] for url in murls}
    durls = rurls.difference(mmurls)
    rds.srem('user',*durls)
def clean_blog():
    rurls:set = rds.smembers("blog")
    rurls = {rurl.decode("utf-8") for rurl in rurls}
    cursor.execute("select url from article_info")
    murls = cursor.fetchall()
    mmurls = {url[0] for url in murls}
    durls = rurls.difference(mmurls)
    rds.srem("blog",*durls)

def clean_url():
    rurls: set = rds.smembers("blog")
    rurls = [rurl.decode("utf-8") for rurl in rurls]
    prefix = "https://blog.csdn.net/"
    rurls = [url.split(".net/")[1] for url in rurls]
    print(rurls[:2])
    rds.delete("blog")
    rds.sadd("blog",*rurls)
cursor.close()
conn.close()
