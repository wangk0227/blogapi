import jwt
from rest_framework import status
from datetime import datetime, timedelta
from rest_framework.authentication import BaseAuthentication

from blog import models

from utils.redisCache import RedisCache
from utils.publicConfig import SECRET
from utils.baseResponse import BaseResponse
from utils.customException import BlogException


class JwtToken:

    def __init__(self):
        self.expiry = datetime.utcnow()

    @staticmethod
    def generate_jwt(payload, expiry, secret=None):
        '''使用jwt模块生成token'''
        _payload = {'exp': expiry}
        _payload.update(payload)
        token = jwt.encode(_payload, secret, algorithm='HS256')
        return token

    @staticmethod
    def verify_jwt(token, secret):
        '''token的验签'''

        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.PyJWTError:
            payload = None
        return payload

    def generate_token(self, user_id, refresh=False):
        # 生成请求token 有效期2个小时 hours
        expiry = self.expiry + timedelta(days=1)
        token = self.generate_jwt({'user_id': user_id}, expiry, SECRET)

        # 生成刷新token 有效期 14天
        if refresh:
            refresh_expiry = self.expiry + timedelta(days=14)
            refresh_token = self.generate_jwt({'user_id': user_id, 'is_refresh': True}, refresh_expiry, SECRET)
        else:
            refresh_token = None

        return token, refresh_token


class UserAuth(BaseAuthentication):
    code = status.HTTP_401_UNAUTHORIZED

    def authenticate(self, request):
        res = BaseResponse()
        rec = RedisCache()
        jwt_token = JwtToken()
        token = request.META.get('HTTP_ACCEPTTOKEN')

        if not token:
            res.error = '请登录!'
            res.code = self.code
            raise BlogException(res.dict)
        verify_token = rec.redis_get_val(token)
        if not verify_token:
            res.error = '用户认证异常,请重新登录!'
            res.code = self.code
            raise BlogException(res.dict)
        verify_redis_token = jwt_token.verify_jwt(verify_token, SECRET)
        if not verify_redis_token:
            res.error = '用户认证已过期,请重新登录!'
            res.code = self.code
            raise BlogException(res.dict)
        user_obj = models.UserAccount.objects.filter(id=verify_redis_token.get('user_id')).first()

        return user_obj, token
