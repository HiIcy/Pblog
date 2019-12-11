import aiomysql
# from config import Config as CF
from pathlib import Path
import asyncio
semp = asyncio.Semaphore(value=220)
# 抓取数据到文件
root_path = r"F:\Resources\kdata\blogp"
async def fetch(semp,root_path):
    mysql_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "123456",
        "db": "pblog",
    }
    conn = await aiomysql.connect(**mysql_config)
    cur = await conn.cursor()
    sql = "select title,content from article_info"
    await cur.execute(sql)
    results = await cur.fetchmany(size=200)
    r = []
    for result in results:
        r.append(writeFile(semp,root_path,result[0],result[1]))
    await asyncio.gather(*r)


async def writeFile(semp,root_path,title,content):
    async with semp:
        target = Path(root_path)/(title+".html")
        with open(str(target),"w",encoding='utf-8',errors="ignore") as f:
            f.write(content)

loop = asyncio.get_event_loop()
loop.run_until_complete(fetch(semp,root_path))
import simplejson as json
async def fetcher(root_path):
    mysql_config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "123456",
        "db": "pblog",
    }
    conn = await aiomysql.connect(**mysql_config)
    cur = await conn.cursor()
    sql = "select title,content from article_info"
    await cur.execute(sql)
    results = await cur.fetchmany(size=100)
    r = []
    for result in results:
        r.append(result[1])
    json.dump(r,open(root_path,'w',encoding="utf-8"),ensure_ascii=False)

# lp = asyncio.get_event_loop()
# lp.run_until_complete(fetcher(root_path))
