# coding:utf-8
# __user__ = hiicy redldw
# __time__ = 2019/11/22
# __file__ = ippool
# __desc__ =
from collections import OrderedDict
import execjs
from bs4 import BeautifulSoup
import requests
import random
import sys,os
path = os.path.dirname(os.path.dirname(__file__))
sys.path.append(path)
from spiders.Items import UserItems
# from config import Config as CF
# from .Logger import Logger as log
from utils.decorators import Singleton
from utils import USER_AGENT_LIST, JS_CODE, COOKIES
# from .Logger import Logger as log
from lxml import etree

__all__ = ['get_random_ip', 'update_cookie']


class IPpool(Singleton):

    def __init__(self, url, headers):
        self._counter = 0
        self.ip_list = ['']
        self.ip_list += self._get_ip_list(url, headers)

    def _get_ip_list(self, url, headers):
        web_data = requests.get(url, headers=headers)
        soup = BeautifulSoup(web_data.text, 'lxml')
        ips = soup.find_all('tr')
        ip_list = []
        for i in range(1, len(ips)):
            ip_info = ips[i]
            tds = ip_info.find_all('td')
            if tds[5].text == "http":
                ip_list.append(tds[5].text + '://' + tds[1].text + ':' + tds[2].text)
        return ip_list

    def get_random_ip(self):
        # for ip in self.ip_list:
        #     proxy_list.append('http://' + ip)
        while True:
            proxy_ip: str = random.choice(self.ip_list)
            # if proxy_ip.startswith("HTTPS"):
            #     proxyies = {"https":prxy_ip.lower()}
            if (proxy_ip and self._ping_ip(proxy_ip) or not proxy_ip):
                break
            self._counter += 1
            if self._counter > 20:
                # # log.warn("get gaoci proxy fail")
                proxy_ip = ''
                self._counter = 0
                break
        return proxy_ip

    def _ping_ip(self, proxyip):
        status_code = requests.get("https://www.baidu.com/", headers={'User-Agent': random.choice(USER_AGENT_LIST)},
                                   proxies={'http': proxyip}).status_code
        if status_code == 200:
            return True
        else:
            return False


def get_proxy():
    return requests.get("http://127.0.0.1:5010/get/").json()


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


def get_random_ip():
    try_count = 8
    while try_count > 0:
        # types = [0,1,2]
        retry_count = 2
        proxy = get_proxy().get('proxy')
        while retry_count > 0:
            # i = random.randint(1,10)
            #
            # url = f"http://127.0.0.1:8000/?types={random.choice(types)}&count={random.randint(i,i+random.randint(1,10))}"
            try:
                html = requests.get(r"https://www.baidu.com/", headers={
                    'User-Agent': random.choice(USER_AGENT_LIST)
                }, proxies={"http": "http://{}".format(proxy)}).text
                if "<title>百度一下，你就知道 </title>" in html:
                    print('success')
                    return "http://{}".format(proxy)
                else:
                    retry_count -= 1
            except Exception:
                retry_count -= 1
        # 出错5次, 删除代理池中代理
        delete_proxy(proxy)
        try_count -= 1
    return ""


def update_cookie(arg1=None):
    ck = COOKIES.split(";")
    cks = {}
    for i in ck:
        i = i.strip()
        k, v = i.split("=", 1)
        cks[k] = v
    if arg1:
        ctx = execjs.compile(JS_CODE)
        arg2 = ctx.call('getArg2', arg1)
        print(arg1, arg2)
        cks['acw_sc__v2'] = arg2
        return cks
    return cks


if __name__ == '__main__':

    import re
    from lxml import etree
    headers = {
        'User-Agent': random.choice(USER_AGENT_LIST)
    }
    url = r"https://blog.csdn.net/qq_43625764"
    arg1 = None
    re_try = 3
    for i in range(re_try):
        ip = ""
        print(ip)
        rep = requests.get(url, headers=headers, proxies={"http": ip}, cookies=update_cookie(arg1))
        text = rep.text
        if "arg1" in text:
            arg1 = re.compile("(?<=arg1=)['\"](.*)['\"]").search(text).group(1)
            print(arg1)
        else:
            break
    user_item = UserItems()
    content = etree.HTML(text)
    profile = content.xpath('//*[@id="asideProfile"]')[0]
    # user_item['url'] = user_url
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
    print(user_item.unapply())
