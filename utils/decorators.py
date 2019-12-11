# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/10
__File__      :  decorators.py
__Desc__      :
"""
from datetime import datetime as dt
from functools import wraps
from datetime import timedelta

# def ensure_key(func):
#     @wraps(func)
#     def wrapper(cls, *args, **kwargs):
#         pass


class Singleton:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            # if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


def cau_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = dt.now()
        try:
            func(*args,**kwargs)
        except Exception as e:
            print(e)
        end = dt.now()
        delta = end - start
        print(f"{func.__name__} 执行耗时:{delta.total_seconds()}")
        # print(f'历经',strf_time(timedelta(delta.da).))
    return wrapper

# def strf_time(delta:dt):
#     strs = ''
#     if delta.month:
#         strs += str(f"{delta.month}月 ")
#     if delta.day:
#         strs += str(f"{delta.day}天 ")
#     if delta.hour:
#         strs += str(f"{delta.hour}小时")
#     if delta.minute:
#         strs += str(f"{delta.minute}分钟")
#     if delta.second:
#         strs += str(f"{delta.second}秒")


if __name__ == "__main__":
    s1 = Singleton()
    s2 = Singleton()
    print(s1 is s2)
