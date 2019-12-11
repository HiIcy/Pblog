# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/5
__File__      :  crawler.py
__Desc__      :
"""
import codecs
import sys
import asyncio
import random
import time
import traceback
import pymysql
import requests
from spiders import get_line
from utils import USER_AGENT_LIST
from utils.decorators import cau_time
from .Filter import URLFilter as uft
from .Logger import Logger as log
from .Storage import PDBC
from .Middle import get_random_ip, update_cookie
from .Items import UserItems, ArticleItems
import aiohttp
from aiohttp import TCPConnector
from lxml import etree
from threading import Thread
import urllib.parse
from functools import partial
from config import Config as CF
import simplejson as json
import re
from queue import Queue,PriorityQueue

# import aiomysql

__all__ = ["crawler", "run"]

# 每个线程可以有一个loop
# loop执行会挂起线程
user_mq = Queue(maxsize=300)  # REW: 线程级安全 可以共享
article_mq = Queue(maxsize=300)


# tcpConnector = TCPConnector(ssl=False,limit=CF.concurrency) # 非线程级 所以没法直接用


def start_loop(loop):
    log.info("start loop forever on second thread")
    asyncio.set_event_loop(loop)
    loop.run_forever()


# FIXME: async with : __aenter__ __aexit__
# https://blog.csdn.net/tinyzhao/article/details/52684473
def construct_param():
    headers = {  # "refer": "https://blog.csdn.net/",
        "Connection": "keep-alive",
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    # proxy = {'proxy':ipo.get_random_ip().values()[0]}
    return {'headers': headers}


async def get_categories(session: aiohttp.ClientSession, root_url, semaphore):
    async with semaphore:
        # async with session.get(root_url, headers={"Connection": "keep-alive",
        #                                           "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}) as response:
        with open(r"E:\javascript\pblog\main.html", "r", encoding='utf-8') as fi:
            text = fi.read()
            nodes = etree.fromstring(text, etree.HTMLParser())
            log.info(f"get_root_categorie start {root_url}")
            # text = await response.text()
            navs = nodes.xpath(f"//nav[@id='nav']//ul/li")
            # navs = nodes.xpath("//*[@id='nav']/div/div/ul/li")
            for i, nav in enumerate(navs):
                if i == 0:
                    continue
                # a_text = nav.xpath("a/text()")[0]
                a_text = nav.xpath("a")[0].text  # 不需要再用/开头 直接子节点开头
                href = nav.xpath("a")[0].attrib.get("href")
                if "watchers" in href:
                    continue
                if "blockchain" in href or "ai" in href or "cloud" in href:
                    t_href = href
                else:
                    t_href = urllib.parse.urljoin(root_url, href)
                try:
                    asyncio.ensure_future(
                        get_category_urls(session, t_href, a_text, semaphore))
                # log.info("put category url success - {}".format(a_text))
                except Exception as e:
                    log.error(f"put category url error\n{e}", get_line())
                    # print(traceback.format_exc())


async def get_category_urls(session: aiohttp.ClientSession, href, category, semaphore):
    async with semaphore:
        async with session.get(href, **construct_param()) as response:
            text = await response.text()
            if "arg1" in text:
                log.error("session expire")
                session.cookie_jar.update_cookies(
                    get_updated_cookie(href)
                )
                asyncio.ensure_future(get_category_urls(session, href, category, semaphore))
                return
            log.info("get category url {}".format(category))

            efeedlist = etree.HTML(text)
            feedlists = efeedlist.xpath(f'//*[starts-with(@class,"feedlist_mod")]/li[@class="clearfix"]')
            for blog in feedlists:
                try:
                    blog_div = blog.xpath("div[contains(@class,'list_con')]")[0]
                    article_href = blog_div.xpath(f"div[@class='title']/h2/a/@href")[0]
                    user_href = blog_div.xpath(f"dl[@class='list_userbar']/"
                                               f"dd[@class='name']/a/@href")[0]
                    # 通过队列方式放任务就好
                    # TODO:我发现甚至可以不用队列直接ensure_future 注入到loop里去
                    article_mq.put(article_href)
                    user_mq.put(user_href)
                except Exception as e:
                    log.error("get category url fail")


# response = await session.get(CF.blog_api)
# i = 0
# while not response or response.status != 200:
#     i+=1
#     await asyncio.sleep(1)
#     response = await session.get(CF.blog_api)
#     log.warn(f"get dynamic api fail,try {i} 次")
#     if i >20:
#         break
# content = response.text()
# content = json.loads(content)
# articles = content.get("articles")
# for article in articles:
#     userurl = article.get("user_url")
#     article_url = article.get("url")
#     article_mq.put_nowait(article_url)
#     user_mq.put_nowait(userurl)


async def parse_user_articles(session, user_url, db, semaphore):
    if uft.filter(user_url, 'user'):
        async with semaphore:
            # 只要原创
            async with session.get(user_url, params={"t": "1"}, **construct_param()) as response:
                content = await response.text()
                if 'arg1' in content:
                    log.error("session expire")
                    session.cookie_jar.update_cookies(
                        get_updated_cookie(user_url)
                    )
                    user_mq.put(user_url)
                    uft.remove(user_url,'user')
                else:
                    # log.info("start parse user info ")
                    user_me_url = user_url.replace("blog", "me")
                    scheme, path = user_me_url.rsplit("/", 1)
                    path = "follow/" + path
                    me_follow_url = urllib.parse.urljoin(scheme, path)
                    asyncio.ensure_future(parse_user_concern(session, me_follow_url, semaphore))
                    content = etree.HTML(content)
                    user_item = UserItems()
                    try:
                        profile = content.xpath('//*[@id="asideProfile"]')[0]
                        user_item['url'] = user_url
                        user_item['name'] = profile.xpath("div[contains(@class,'profile-intro')]/div[contains(@class,'user-info')] \
							              //span/a/text()")[0].strip('\n\t ')
                        data_info = profile.xpath("div[contains(@class,'data-info')]")[0]
                        user_item['creates'] = data_info.xpath("dl[1]/@title")[0]
                        user_item['fans'] = data_info.xpath("dl[2]/@title")[0]
                        user_item['praises'] = data_info.xpath("dl[3]/@title")[0]
                        user_item['comments'] = data_info.xpath("dl[4]/@title")[0]
                        user_item['visits'] = data_info.xpath("dl[last()]/@title")[0]
                        grade_box = profile.xpath("div[contains(@class,'grade-box')]")[0]
                        user_item['grade'] = grade_box.xpath("dl[1]/dd/a/@title")[0][0]
                        credits = grade_box.xpath("dl[3]/dd/@title")[0]
                        try:
                            credits = int(credits)
                        except:
                            credits = 0
                        user_item['credits'] = credits
                        # FIXME:已解析具体的18万+
                        ranks = grade_box.xpath("dl[last()]/@title")[0]
                        try:
                            ranks = int(ranks)
                        except:
                            ranks = 0
                        user_item['ranks'] = ranks
                        badges = profile.xpath(".//div[contains(@class,'badge-box')]/div[2]/div[@class='icon-badge']")
                        badgestr = ""
                        for badge in badges:
                            badgestr += badge.attrib.get("title") + "/"
                        user_item['badges'] = badgestr[:-1]

                        # fixme: 用js破解;已经找出解决办法
                        pageObj = content.xpath("/html/body/script[6]/text()")[0]
                        p = re.compile("(?<=listTotal).*?(\d+) *;")
                        list_total = int(p.search(pageObj).group(1).strip())
                        p = re.compile("(?<=pageSize).*?(\d+) *;")
                        page_size = int(p.search(pageObj).group(1).strip())
                        if (list_total / page_size) > (list_total // page_size):
                            page_count = (list_total // page_size) + 1
                        else:
                            page_count = list_total // page_size
                    except Exception:
                        log.error(f"parse user info fail \n{user_url}\n{traceback.format_exc()}")
                        uft.remove(user_url,'user')
                    else:
                        log.info('parse user info success')
                        try:
                            fix_url: str = user_url + "/article/list/"
                            # urls = []
                            for i in range(1, page_count):
                                # TODO:3.7用create_task
                                asyncio.ensure_future(get_article_list(session, urllib.parse.urljoin(
                                    fix_url, str(i)), semaphore))  # REW:加入事件循环器
                            result = user_item.unapply()
                            sql = "insert into user_info values (null,'{}','{}','{}','{}','{}','{}'," \
                                  "'{}','{}','{}','{}','{}')".format(*result)
                            r = db.insert(sql)
                            if r <= 0:
                                log.error(f"write into user_info table fail {user_url}")
                            else:
                                log.info("write user info  success")
                        except:
                            uft.remove(user_url, 'user')
                            log.error(f"operate user_info table fail\n{user_url}\n{traceback.format_exc()}")


async def parse_user_concern(session, me_url, semaphore):
    async with semaphore:
        async with session.get(me_url, **construct_param()) as response:
            content = await response.text()
            if 'arg1' in content:
                log.error("session expire")
                session.cookie_jar.update_cookies(
                    get_updated_cookie(me_url)
                )
                # 再次放进loop循环里
                asyncio.ensure_future(parse_user_concern(session, me_url, semaphore))
            else:
                content = etree.HTML(content)
                concerners = content.xpath("//*[contains(@class,'chanel_det_list')]/ul/li")
                for concerner in concerners:
                    me_href = concerner.xpath("a/@href")[0]
                    user_url = me_href.replace("me", "blog")
                    user_mq.put(user_url)
                    log.info("put user url success")


async def get_article_list(session, url, semaphore):
    async with semaphore:
        # 只要原创
        try:
            async with session.get(url, params={"t": "1"}) as response:
                content = await response.text()
                if 'arg1' in content:
                    log.error("session expire")
                    session.cookie_jar.update_cookies(
                        get_updated_cookie(url)
                    )
                    # REW:也可以await，但是这种写法可以节约一个semaphore
                    asyncio.ensure_future(get_article_list(session, url, semaphore))
                else:
                    content = etree.HTML(content)
                    articles = content.xpath("//*[@class='article-list']/div[contains(@class,'article-item-box')]")
                    for article_box in articles:
                        article_item = article_box.xpath("h4/a/@href")[0]
                        article_mq.put(article_item)
                        log.info("put article url success")
        except:
            log.error(f'visit user_article url occur error \n{url}\n{traceback.format_exc()}')


# TODO:给协程加装饰器
async def get_article_detail(session, url, semaphore):
    if uft.filter(url):
        async with semaphore:
            async with session.get(url) as response:
                content = await response.text()
                if 'arg1' in content:
                    log.error("session expire")
                    uft.remove(url)
                    # REW:session 大家都是用的一个函数 我这里更新了cookie,你们都用新的
                    #  跟semaphore 里的value计数器一个意义
                    session.cookie_jar.update_cookies(
                        get_updated_cookie(url)
                    )
                    article_mq.put(url)
                    uft.remove(url)
                    return None
                else:
                    return content


def parse_blog(db, future):
    text = future.result()
    if text == None:
        return
    article_item = ArticleItems()
    content: etree._ElementTree = etree.HTML(text)
    try:
        box = content.xpath("//*[@id='mainBox']/main/div[1]")[0]

        url = content.xpath("/html/head/link[1]")[0].attrib.get('href')
        article_item['url'] = url
        header = box.xpath("div[1]")[0]
        title_box = header.xpath("div[1]/div[1]")[0]
        article_item['nature'] = title_box.xpath("span[contains(@class,'article-type')]/text()")[0]
        title = title_box.xpath("h1/text()")[0]
        article_item['title'] = title
        info_box = header.xpath("div[1]/div[2]")[0]
        # TODO:时间格式整理
        article_item['create_time'] = info_box.xpath("div[1]/span[@class='time']/text()")[0]
        read_count = info_box.xpath("div[1]/span[@class='read-count']/text()")[0]
        read_count = re.search(re.compile("(?<=阅读数)\s*(\d*)"), read_count)
        article_item['read_count'] = read_count.group(1)
        article_item['user_name'] = info_box.xpath("div[1]/a/text()")[0]

        body: etree._Element = box.xpath("article/div[1]/div[@id='content_views']")[0]
        try:
            detail = etree.tostring(body, encoding='unicode')
        except Exception:
            detail = etree.tounicode(body)
        detail = pymysql.escape_string(detail)  # REW:转义字符串 同时插入单、双引号
        article_item['content'] = detail

        menu = content.xpath("//*[starts-with(@class,'tool-box')]/ul")[0]
        article_item['praises'] = menu.xpath("li[1]/button/p")[0].text
        cments = menu.xpath("li[3]/a/p")[0].text
        cments = cments.strip("\r\n\t ")
        article_item['comments'] = 0 if cments == "" else cments
    except:
        u = ''
        if 'url' in vars().keys():
            u += url
        if 'title' in vars().keys():
            u+=" "+title
        log.error(f"parse article info fail,\n{u}\n{traceback.format_exc()}")
        if 'url' in vars().keys():
            uft.remove(url)
    else:
        try:
            result = article_item.unapply()
            sql = "insert into article_info values (null,'{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(*result)
            # log.info(sql)
            r = db.insert(sql)
            if r <= 0:
                log.error("write article info occur error", get_line())
            else:
                log.info("write article info success")
        except Exception as e:
            uft.remove(url)
            log.error(f"operate article_info table fail\n{url} - {title}\n{e}")
            # traceback.print_exc(file=error_file)


def get_updated_cookie(url):
    """
    # with 语句 一跳出范围 就结束对象了
    # TODO:Client Tracing
    async with aiohttp.ClientSession(connector=TCPConnector(ssl=False),
                                    cookies=update_cookie(arg1)) as session:
    """
    re_try = 3
    arg1 = None
    for i in range(re_try):
        cookies = update_cookie(arg1)
        response = requests.get(url, headers={"User-Agent": random.choice(USER_AGENT_LIST),
                                              "Connection": "keep-alive",
                                              'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},
                                cookies=cookies)
        text = response.text
        if "arg1" in text:
            arg1 = re.compile("(?<=arg1=)['\"](.*?)['\"]").search(text).group(1)
        else:
            return cookies
    return {}


# TODO:异步mysql
@cau_time
def crawler(root_url):
    root_url = root_url
    # 开线程启动loop
    newloop = asyncio.new_event_loop()
    thread = Thread(target=start_loop, args=(newloop,))
    thread.setDaemon(True)
    thread.start()

    # 数据库连接池
    pool_config = CF.mysql_config.copy()
    pool_config.update(CF.mysql_cached_config)
    pdbc = PDBC(pool_config)
    log.info("mysql configure !", get_line())

    # 获取会话对象
    newloop.set_debug(True)
    semaphore = asyncio.Semaphore(CF.concurrency, loop=newloop)
    cookies = get_updated_cookie(CF.root_url)
    session = aiohttp.ClientSession(connector=TCPConnector(loop=newloop, ssl=False),
                                    cookies=cookies,
                                    headers={
                                             "Connection": "keep-alive",
                                             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    if not session or session.closed:
        log.error("can't request target!", get_line())
        newloop.stop()
        newloop.close()
        exit(0)
    asyncio.run_coroutine_threadsafe(get_categories(session, root_url, semaphore), newloop)  # 这里后面会无限循环去取url，不怕这里堵到

    sleep_seeds = [1, 0, 0, 2, 3, 0, 1, 0, 1, 0]

    try:
        while True:
            if not article_mq.empty():
                article_url = article_mq.get_nowait()  # 避免堵塞后面的user_url
                if article_url:
                    task: asyncio.Future = asyncio.run_coroutine_threadsafe(
                        get_article_detail(session, article_url, semaphore), loop=newloop)  # REW:ensure_future可以指定loop
                    task.add_done_callback(partial(parse_blog, pdbc))  # 用偏函数为回调加入多个参数
                    article_mq.task_done()
                    time.sleep(random.choice(sleep_seeds))
            if not user_mq.empty():
                user_url = user_mq.get_nowait()
                if user_url:
                    asyncio.run_coroutine_threadsafe(parse_user_articles(session, user_url, pdbc, semaphore),
                                                     newloop)
                    user_mq.task_done()
                    time.sleep(random.choice(sleep_seeds))
            else:
                time.sleep(1.5)
                log.info("entire wait 1s")
    except KeyboardInterrupt:
        tasks = asyncio.Task.all_tasks()
        group = asyncio.gather(*tasks, return_exceptions=True)  # 把错误信息打印出来
        group.cancel()
        curloop = asyncio.get_event_loop()
        curloop.run_until_complete(session.close())
        newloop.stop()
        curloop.close()
        pdbc.dispose()


def run(root_url):
    # 开线程启动loop
    newloop = asyncio.new_event_loop()
    thread = Thread(target=start_loop, args=(newloop,))
    # thread.setDaemon(True)
    thread.start()
    # 数据库连接池

    pool_config = CF.mysql_config.copy()
    pool_config.update(CF.mysql_cached_config)
    pdbc = PDBC(pool_config)

    log.info("mysql configure !", get_line())


if __name__ == "__main__":
    pass
