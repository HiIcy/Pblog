# _*_ coding:utf-8 _*_
"""
__Author__    :  Icy ldw
__Date__      :  2019/11/5
__File__      :  parser.py
__Desc__      :
"""
from spiders import get_line
import logging
import logging.handlers
from config import Config as CF
from utils.decorators import Singleton
__all__ = ["Logger"]


# FIXME:使用日志配置文件管理
# FIXME：使用yml文件+字典配置


class errFilter(logging.Filter):
    def filter(self, record):
        if record.levelname == "ERROR":
            return True

class noterrFiter(logging.Filter):
    def fitlter(self,record:logging.LogRecord):
        if record.levelname.upper() != "ERROR":
            return True

class LinenumLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = self.extra
        return msg, kwargs


# FIXME:还需要再改改
class Logger(Singleton, logging.getLoggerClass()):
    logger = logging.getLogger(CF.logger_name)
    logger.setLevel(logging.DEBUG)

    fi_handler = logging.handlers.RotatingFileHandler(
        CF.logger_path,backupCount=7,
        maxBytes=1024*1024*16,encoding='utf-8')
    formatter = logging.Formatter(CF.logger_fmt)
    fi_handler.setFormatter(formatter)
    fi_handler.addFilter(noterrFiter())

    # er_handler = logging.handlers.RotatingFileHandler(
    #     CF.error_output,backupCount=7,
    #     maxBytes=1024*1024*16,encoding='utf-8')
    er_handler = logging.handlers.TimedRotatingFileHandler(
        CF.error_output,backupCount=20,encoding='utf-8',
    )
    eformatter = logging.Formatter(CF.logger_errfmt)
    er_handler.setFormatter(eformatter)
    # 还有个过滤器，还可以增加错误处理器发邮件给我
    er_handler.addFilter(errFilter())

    # 日志记录器添加多个处理器，处理到不同位置
    logger.addHandler(fi_handler)
    logger.addHandler(er_handler)

    logger = LinenumLoggerAdapter(logger, {"linenum": "-"})

    @classmethod
    def _process(cls, *arg):
        if len(arg) == 0:
            return {}
        assert len(arg) == 1
        return {"extra": {"linenum": str(arg)}}

    # FIXME: 更优雅地加入上下文动态添加的功能
    @classmethod
    def debug(cls, message, *args):
        cls.logger.debug(message, **cls._process(*args))

    @classmethod
    def info(cls, message, *args):
        cls.logger.info(message, **cls._process(*args))

    @classmethod
    def warn(cls, message, *args):
        cls.logger.warning(message, **cls._process(*args))

    @classmethod
    def error(cls, message, *args):
        cls.logger.error(message, **cls._process(*args))


if __name__ == "__main__":
    print(get_line())
    # print("区块链")
    try:
        a = 6/0
    except Exception as e:
        Logger.error(f"sf\n{e}")