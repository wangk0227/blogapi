import os
from pathlib import Path

path = os.path.join(Path(__file__).parent.parent, 'media\\blogs_logging')

FORMAT = '[%(asctime)s] [%(name)s]-[%(levelname)s] [ %(filename)s\\%(module)s\\%(lineno)d ] : %(message)s'  # 日志显示的内容

logging_dic = {
    'version': 1,  # 必须是个整数
    'formatters': {  # 日志的格式化器
        'blogs': {
            'format': FORMAT,  # 设置日志显示格式
            'datefmt': '%Y-%m-%d %H:%M:%S'  # 设置日志的显示时间
        }
    },
    'handlers': {
        'default': {
            'level': "DEBUG",
            'formatter': 'blogs',
            'class': "logging.handlers.RotatingFileHandler",
            'maxBytes': 1024 * 1024 * 5,
            'encoding': "utf-8",
            'backupCount': 2,  # 保留两个日志
            'filename': os.path.join(path,'logging-blog.txt'),  # 进行时间拼接

        },
    },
    "loggers": {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False,
        }

    }

}

from logging import config, getLogger

config.dictConfig(logging_dic)

logger = getLogger('blogs')

