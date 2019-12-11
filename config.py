# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/10/30
__File__      :  config.py
__Desc__      :
"""
from inspect import isfunction
class Config:
	root_url = "https://blog.csdn.net/"
	# root_url = "http://data.biancheng.net"
	redis_url = "localhost"
	redis_port = 6379
	concurrency = 220
	spider_name = "pblog"
	#error_output = r"E:\Data\ZResource\pblog\error_output\error.log"
	error_output = "F:\Resources\log\pblog\error_output\error.log"
	blog_api = "https://blog.csdn.net/api/articles?type=more&category=java&shown_offset=0"
	logger_name = "ppblog"
	logger_fmt = "[%(levelname)s]:%(asctime)s: %(message)s:%(linenum)s"
	# logger_errfmt = "[%(levelname)s]:%(asctime)s: %(message)s :%(pathname)s:%(linenum)s"
	logger_errfmt = "[%(levelname)s]:%(asctime)s: %(message)s  :%(linenum)s"
	# logger_path = r"E:\Data\ZResource\pblog\log\fulllog.log"
	logger_path = r"F:\Resources\log\pblog\log\fulllog.log"
	proxy_url = r'http://www.xicidaili.com/nn/'
	mysql_config = {
		"host":"localhost",
		"port":3306,
		"user":"root",
		"password":"123456",
		"db":"pblog"
	}
	# 1.mincached，最少的空闲连接数，如果空闲连接数小于这个数，pool会创建一个新的连接
	# 2.maxcached，最大的空闲连接数，如果空闲连接数大于这个数，pool会关闭空闲连接
	# 3.maxconnections，最大的连接数，
	# 4.blocking，当连接数达到最大的连接数时，在请求连接的时候，如果这个值是True，请求连接的程序会一直等待，直到当前连接数小于最大连接数，如果这个值是False，会报错，
	# 5.maxshared,当连接数达到这个数，新请求的连接会分享已经分配出去的连接
	mysql_cached_config = {
		"mincached":5,
		"maxcached":20,
		"maxshared":20,
		"maxconnections":20
	}

	@classmethod
	def print(cls):
		vuls = cls.__dict__
		for k,v in vuls.items():
			if k.startswith("__") or isfunction(v):
				continue
			print(f'{k} --> {v}',sep='\n')

if __name__ == "__main__":
	Config.print()
