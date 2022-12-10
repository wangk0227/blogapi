import redis
import random
from redis.exceptions import RedisError

# 需要修改ip
POOL = redis.ConnectionPool(decode_responses=True, max_connections=10, host='127.0.0.1', port=6379, )
CONN = redis.Redis(connection_pool=POOL,)


class CacheTTLBase(object):
    '''过期时间偏差'''
    TTL = 2 * 60 * 60  # 默认过期时间
    MAX_DELTA = 10 * 60  # 偏差时间

    @classmethod
    def get_val(cls):  # 返回
        return cls.TTL + random.randint(0, cls.MAX_DELTA)


class RedisCache:
    @staticmethod
    def redis_save_val(redis_key, redis_val):
        try:
            redis_val = str(redis_val)
            start = CONN.setex(redis_key, CacheTTLBase.get_val(), redis_val)  # 将值存到数据库中
        except RedisError as e:
            # 书写日志
            start = False
        return start

    @staticmethod
    def redis_get_val(redis_key):
        '''获取当前redis数据'''
        try:
            redis_val = CONN.get(str(redis_key))

        except RedisError as e:
            # logger.error(e)
            redis_val = None
        if redis_val:
            return redis_val
        else:
            return redis_val

    @classmethod
    def redis_clear_val(cls, redis_key, redis_val):
        '''当数据库的值更新的情况下，清除原有缓存'''
        CONN.delete(redis_key)  # 清空原有数据
        cls.redis_save_val(redis_key, str(redis_val))  # 在设置新的内容

    @staticmethod
    def article_num_update(id):
        key = 'article_read_num_%s' % id
        CONN.incr(key)

    @staticmethod
    def redis_delete_val(redis_key):
        '''当数据库的值更新的情况下，清除原有缓存'''
        CONN.delete(redis_key)  # 清空原有数据

    @staticmethod
    def article_num_delete(id):
        key = 'article_read_num_%s' % id
        if CONN.exists(key):
            CONN.delete(key)
