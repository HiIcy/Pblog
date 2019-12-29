import aiomysql
# from config import Config as CF
from pathlib import Path
import asyncio
import simplejson as json

# semp = asyncio.Semaphore(value=220)
# # 抓取数据到文件
# root_path = r"F:\Resources\kdata\blogp"
# async def fetch(semp,root_path):
#     mysql_config = {
#         "host": "localhost",
#         "port": 3306,
#         "user": "root",
#         "password": "123456",
#         "db": "pblog",
#     }
#     conn = await aiomysql.connect(**mysql_config)
#     cur = await conn.cursor()
#     sql = "select title,content from article_info"
#     await cur.execute(sql)
#     results = await cur.fetchall()
#     r = []
#     for result in results:
#         r.append(writeFile(semp,root_path,result[0],result[1]))
#     await asyncio.gather(*r)


# async def writeFile(semp,root_path,title,content):
#     async with semp:
#         target = Path(root_path)/(title+".html")
#         with open(str(target),"w",encoding='utf-8',errors="ignore") as f:
#             f.write(content)
# # loop = asyncio.get_event_loop()
# # loop.run_until_complete(fetch(semp,root_path))
# import profile
# import simplejson as json

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
    rows = await cur.execute(sql)
    chunk = 6000
    results = []
    # cursor.fetchall()
    try:
        
        while rows > 0:
            if rows > chunk:
                res = await cur.fetchmany(chunk)
            else:
                res = await cur.fetchmany(rows)
            rows -= chunk
            for cont in res:
                results.append(cont[1])
        
        # result = await cur.fetchmany(size=chunk)
        # for res in result:
        #     results.append(res[1])
    except Exception:
        print('get data from db occur error')
    finally:
        await cur.close()
        conn.close()
    # results = await cur.fetchmany(size=100)
    json.dump(results,open(root_path,'w',encoding="utf-8"),ensure_ascii=False)

root_path = r"E:\deeper\GPT2-Chinese\data\train.json"
lp = asyncio.get_event_loop()
lp.run_until_complete(fetcher(root_path))

def convert2json():
    import os
    inputs_dir=r"F:\Resources\kdata\blogp\cleanTag"
    files = [os.path.join(inputs_dir,file) for file in os.listdir(inputs_dir)]
    r = []
    _path = r"E:\deeper\GPT2-Chinese\data\train.json"
    for file in files:
        with open(file, 'r',encoding='utf-8') as infile:
            content = infile.read()
            if content.strip(" ")=="":
                print('once')
                continue
            r.append(content)
    json.dump(r,open(_path,'w',encoding='utf-8'),ensure_ascii=False)
# convert2json()