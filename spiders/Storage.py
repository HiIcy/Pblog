# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/15
__File__      :  Storage.py
__Desc__      :
"""
import time
import asyncio
from contextlib import asynccontextmanager
import aiomysql
import pymysql
# REW:PooledDB 线程间共享
from DBUtils.PooledDB import PooledDB
import os,sys
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(path)
from spiders.Items import UserItems,ArticleItems
from config import Config as CF
__all__ = ["ADBC"]

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


class ADBC(metaclass=Singleton):

    def __init__(self):
        self.pool = None
        self.conn = None
        self.cur = None

    async def initpool(self,**cfg):
        _pool = await aiomysql.create_pool(**cfg)
        self.pool = _pool
        return _pool

    @asynccontextmanager
    async def auto_db(self):
        try:
            conn: aiomysql.Connection = await self.pool.acquire()
            cur: aiomysql.Cursor = await conn.cursor()
            yield (cur,conn)
        finally:
            if cur:
                await cur.close()
            if conn:
                await self.pool.release(conn)

    # 插入\更新\删除sql
    async def insert(self, cur,con,sql):
        await cur.execute(sql)
        # FIXME: 优化
        await con.commit()
        insert_num = cur.rowcount
        return insert_num

    # 查询
    async def select(self,cur, sql):
        await cur.execute(sql)  # 执行sql
        (select_res,) = await cur.fetchall()  # 返回结果为字典
        return select_res

    # 释放资源
    async def dispose(self):
        if self.conn:
            await self.conn.close()
        if self.cur:
            await self.cur.close()
        self.pool.close()
        await self.pool.wait_closed()

# 因为协程也只是一个线程，
class PDBC(metaclass=Singleton):
    __pool = None
    def __init__(self,cfg):
        self.cfg = cfg
        self.conn = None
        # 构造函数，创建数据库连接、游标
        # self.coon = PDBC.getmysqlconn(**cfg)  # REW:静态方法
        self.cur = None

    # 数据库连接池连接
    @staticmethod
    def getmysqlconn(**cfg):
        if PDBC.__pool is None:
            PDBC.__pool = PooledDB(creator=pymysql,**cfg)
        return PDBC.__pool.connection()

    def __enter__(self):
        time.sleep(15)
        self.conn = PDBC.getmysqlconn(**self.cfg)
        self.cur = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        PDBC.__pool.cache(self.conn)

    # 插入\更新\删除sql
    def insert(self, sql):
        insert_num = self.cur.execute(sql)
        # FIXME: 优化
        self.conn.commit()
        return insert_num

    # 查询
    def select(self, sql):
        self.cur.execute(sql)  # 执行sql
        select_res = self.cur.fetchall()  # 返回结果为字典
        return select_res

    # 释放资源
    def dispose(self):
        if self.conn:
            self.conn.close()
        if self.cur:
            self.cur.close()
        PDBC.__pool.close()

async def Testaiomysql(adb,i):

    sql = f"insert into tmpt values({i},'sfsf')"
    async with adb.auto_db() as ad:
        q = await adb.insert(*ad, sql)
        print(f"execute {i} success")

if __name__ == "__main__":
    # pass
    # import requests
    # 数据库连接池
    # pool_config = CF.mysql_config.copy()
    # pool_config.update(CF.mysql_cached_config)
    import asyncio

    mysql_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "123456",
        "db": "pblog"
    }
    loop = asyncio.get_event_loop()
    adbc = ADBC()
    pool = loop.run_until_complete(adbc.initpool(**mysql_config))
    adbc.pool = pool
    print(pool)
    time.sleep(5)
    r = []
    for i in range(50):
        r.append(asyncio.ensure_future(Testaiomysql(adbc,i)))
    loop.run_until_complete(asyncio.gather(*r))
