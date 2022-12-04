from rest_framework import status
from rest_framework.versioning import URLPathVersioning

from utils.baseResponse import BaseResponse
from utils.customException import BlogException



# 重写版本控制的返回内容
class RewriteURLPathVersioning(URLPathVersioning):
    '''控制版本返回的内容是什么'''

    def determine_version(self, request, *args, **kwargs):
        res = BaseResponse()
        version = kwargs.get(self.version_param, self.default_version)
        if version is None:
            version = self.default_version
        if not self.is_allowed_version(version):
            res.error = '版本有误,请选择正确的版本!'
            res.code = status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED
            raise BlogException(res.dict)
        return version
