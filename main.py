# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/21
__File__      :  main.py
__Desc__      :
"""
from spiders import Crawler
from config import Config as CF

if __name__ == "__main__":
	Crawler.crawler(CF.root_url)