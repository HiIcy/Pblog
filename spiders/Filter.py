# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/8
__File__      :  Filter.py
__Desc__      :
"""
import time
from .Logger import Logger
import redis
import urllib.parse as up
import traceback
from config import Config as CF

__all__ = ["URLFilter"]


# TODO:应该先检测持久化环境 放在redis启动上
# 持久化开启，那么启动redis时就会恢复数据

def _get_redis_pool():
	pool = redis.ConnectionPool()
	rds = redis.Redis(CF.redis_url,CF.redis_port,connection_pool=pool)
	if rds.ping():
		print('connect redis success')
	else:
		print('connect redis fail')
	return rds


class URLFilter(object):
	rds = _get_redis_pool()

	@classmethod
	def _filter(cls, url, meta="blog"):
		# FIXME:用三级哈希把url变小，存进数组
		# FIXME:
		r = cls.rds.sadd(meta, url)
		if r == 1:
			return True
		elif r == 0:
			return False
		else:
			pass

	@classmethod
	def remove(cls,url,meta="blog"):
		_,url = url.split(".net/")
		try:
			if cls.rds.sismember(url,meta):
				cls.rds.srem(meta,url)
		except Exception:
			Logger.error(traceback.format_exc())


	@classmethod
	def filter(cls, url, meta="blog"):
		"""
		返回ture 表示需要访问
		访问接口判断情况，具体核心再封装一次
		"""
		try:
			urlresult = up.urlparse(url)
			assert urlresult.scheme in ['http', 'https'], "访问url出错"
			_, turl = url.split(".net/")
		except Exception as e:
			print(url)
			Logger.error(traceback.format_exc())
		else:
			# 装饰模式 再给_filter装饰一遍
			return cls._filter(turl, meta=meta)

	@classmethod
	def save(cls):
		while True:
			try:
				if cls.rds.save():
					break
			except:
				time.sleep(1)


if __name__ == "__main__":
	pass
