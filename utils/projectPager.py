from math import ceil
from rest_framework import status
from rest_framework.response import Response
from django.core.paginator import InvalidPage
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination

from utils.baseResponse import BaseResponse


class ProjectPagination(PageNumberPagination):
    max_page = 5  # 前端页码显示最大长度
    page_size_query_param = 'size'
    page_query_param = 'page'  # 查询页码参数
    page_size = 10
    max_page_size = 10
    page_number = None  # 当前访问页码

    def paginate_queryset(self, queryset, request, view=None):
        '''重写当前方法防止报错'''
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)
        self.page_number = int(page_number)
        data_len = len(queryset)
        if int(page_number) < 1 or int(page_number) > ceil(data_len / int(page_size)):
            page_number = 1
        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            self.display_page_controls = True
        self.request = request
        return list(self.page)

    def get_paginated_response(self, data, *args, **kwargs):
        '''重写分页类，当前方法只适用于ListModelMixin类'''
        res = BaseResponse()
        data_count = self.page.paginator.count  # 数据总数量
        page_count = ceil(data_count / self.page_size)  # 计算总页码

        if self.page_number < 1 or self.page_number > page_count:
            self.page_number = 1
        start_page = self.page_number - self.max_page  # 起始页码范围
        end_page = self.page_number + self.max_page  # 结束页码范围
        res.data = data
        res.code = status.HTTP_200_OK
        res.page_count = page_count  # 总页码
        res.page_data_count = data_count # 数据总数量
        res.present_page = self.page_number  # 当前页码
        res.start_page = start_page if start_page > 1 else 1  # 计算 起始页码
        res.end_page = end_page if end_page < page_count else page_count  # 计算 终止页码
        return Response(res.dict)
