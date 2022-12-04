from rest_framework import status
from django.core.cache import cache as cache_redis  # 导入redis缓存对象
from rest_framework.throttling import SimpleRateThrottle

from utils.baseResponse import BaseResponse
from utils.customException import BlogException


class BaseThrottling(SimpleRateThrottle):
    cache = cache_redis
    cache_format = '%(scope)s_%(ident)s'
    res = BaseResponse()
    error = ''
    scope = ''

    def get_cache_key(self, request, view):
        user_id = request.user
        if str(user_id) != 'AnonymousUser':  # 判断当前时否时登录的对象
            ident = user_id
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}  # 拼接唯一标识

    def throttle_failure(self):
        """限流异常抛出"""
        wait = self.wait()
        self.res.code = status.HTTP_504_GATEWAY_TIMEOUT
        self.res.error = self.error % int(wait)
        raise BlogException(self.res.dict)


# 访问限流
class BlogVisitThrottling(BaseThrottling):
    scope = 'blog_visit'
    error = '访问限流请等待%s秒后才能访问'


# 留言接口限流
class ArticleMessageThrottling(BaseThrottling):
    scope = 'article_message'
    error = '当天留言次数已经超出,请明天再来'


# 验证码图限流
class CodeImgThrottling(BaseThrottling):
    scope = 'code_img'
    error = '访问限流请等待%s秒后才能访问'
