from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response


from utils.baseResponse import BaseResponse


class BaseViewApi(APIView):
    '''api父类,接口中没有实现的方法统一返回没有实现'''

    def response(self):
        res = BaseResponse()
        res.error = 'Not Implemented'
        res.code = status.HTTP_501_NOT_IMPLEMENTED
        return Response(res.dict)

    def get(self, request, *args, **kwargs):
        return self.response()

    def post(self, request, *args, **kwargs):
        return self.response()

    def put(self, request, *args, **kwargs):
        return self.response()

    def delete(self, request, *args, **kwargs):
        return self.response()

    def patch(self, request, *args, **kwargs):
        return self.response()


