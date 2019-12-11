# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/15
__File__      :  Storage.py
__Desc__      :
"""
import asyncio
import aiomysql
import pymysql
# REW:PooledDB 线程间共享
from DBUtils.PooledDB import PooledDB
import os,sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)
from spiders.Items import UserItems,ArticleItems
from config import Config as CF
__all__ = ["PDBC"]

async def register_pool(cfg):
    try:
        pool = await aiomysql.create_pool(**cfg)
        return pool
    except asyncio.CancelledError:
        raise asyncio.CancelledError
    except Exception as e:
        return False


async def get_conn(pool):
    conn = await pool.acquire()
    cursor = await conn.cursor()
    return conn, cursor


class Singleton(type):  # REW: 元类单例
    def __init__(cls, *args, **kwargs):
        cls._instance=None
        super(Singleton, cls).__init__(*args, **kwargs)

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance


class PDBC(metaclass=Singleton):
    __pool = None

    def __init__(self,cfg):
        # 构造函数，创建数据库连接、游标
        self.coon = PDBC.getmysqlconn(**cfg)  # REW:静态方法
        self.cur = self.coon.cursor(cursor=pymysql.cursors.DictCursor)

    # 数据库连接池连接
    @staticmethod
    def getmysqlconn(**cfg):
        if PDBC.__pool is None:
            __pool = PooledDB(creator=pymysql,**cfg)
        return __pool.connection()

    # 插入\更新\删除sql
    def insert(self, sql):
        insert_num = self.cur.execute(sql)
        self.coon.commit()
        return insert_num

    # 查询
    def select(self, sql):
        self.cur.execute(sql)  # 执行sql
        select_res = self.cur.fetchone()  # 返回结果为字典
        return select_res

    # 释放资源
    def dispose(self):
        self.coon.close()
        self.cur.close()


if __name__ == "__main__":
    # pass
    # import requests
    # 数据库连接池
    pool_config = CF.mysql_config.copy()
    pool_config.update(CF.mysql_cached_config)
    pdbc = PDBC(pool_config)
    user_item = UserItems()
    a_item = ArticleItems()
    user_item['url'] = "sf"
    user_item['name'] = "sf"
    user_item['creates'] = 3
    user_item['fans'] ="2"
    user_item['praises'] = 5
    user_item['comments'] = 1
    user_item['visits'] = "3"
    user_item['grade'] =5
    user_item['credits'] = "6"
    # todo:解析具体的18万+
    user_item['ranks'] = "13"
    user_item['badges'] = "圣手"

    a_item['title'] = "fs"
    a_item['create_tiem"'] = '2019-08-12'
    a_item['read_count'] = 3
    a_item['nature'] = "sf"
    a_item['content'] = "hhhhhhhhhhhhh"
    a_item['praises'] = 3
    a_item['comments'] = 5
    a_item['url'] = "https://blog.csdn.net/anqixiang/article/details/102727604"
    a_item['user_name'] = "iiiiiii"

    result = user_item.unapply()
    sql = "insert into user_info  values (null,'{}','{}','{}','{}','{}','{}'," \
          "'{}','{}','{}','{}','{}')".format(*result)
    r = pdbc.insert(sql)
    print(r)