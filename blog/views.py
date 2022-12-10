import json
from math import ceil
from rest_framework import status  # 前后端分离自带的的状态码

from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, CreateModelMixin

from blog import models
from utils.publicConfig import *
from utils.baseApi import BaseViewApi
from utils.projectFilters import SearchFilters
from utils.redisCache import RedisCache
from utils.projectPager import ProjectPagination
from utils.baseResponse import BaseResponse
from utils.projectThrottling import ArticleMessageThrottling
from blog.serializer import CategorySerializers, ArticleSerializers, ArticleContentSerializers, LinksSerializers, \
    ArticleMessageSerializers, BloggerContentSerializers, RecentArticlesSerializers


class CategoryApi(BaseViewApi):
    # 展示文章分类信息 可以将内容作为缓存

    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache
        res_variable = RedisVariable()
        redis_key = res_variable.category_list
        val = rec.redis_get_val(redis_key)
        if val:
            res.data = json.loads(val)
            res.code = status.HTTP_200_OK
            return Response(res.dict)
        else:
            queryset = models.Category.objects.filter(is_show='N').all().order_by('order')
            ser_obj = CategorySerializers(queryset, many=True)
            rec.redis_save_val(redis_key, json.dumps(ser_obj.data))
            res.data = ser_obj.data
            res.code = status.HTTP_200_OK
        return Response(res.dict)


class ArticleApi(BaseViewApi):
    '''展现首页文章的内容，根据分类id获取当前分类的文章内容(不能时草稿状态,不能被删除状态)'''

    # 需要分页处理
    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        category_id = request.query_params.get('category_id', 0)
        if category_id == 0:
            # 设置了如果关联分类删除，那么关联分类的字段就变为了空，需要将关联分类的字段给排除掉
            queryset = models.Article.objects.filter(
                recommend_state=1, article_category__isnull=False).all().order_by(
                'order')

        else:
            queryset = models.Article.objects.filter(article_category=category_id,
                                                     recommend_state=1).all().order_by('order')

            if not queryset:
                res.data = []
                res.code = status.HTTP_200_OK
                return Response(res.dict)

        # 分页器
        page = ProjectPagination()
        # 分页计算
        pagination_queryset = page.paginate_queryset(queryset, request, self)
        ser_obj = ArticleSerializers(pagination_queryset, many=True)
        res.data = ser_obj.data
        res.code = status.HTTP_200_OK
        res.data_count = page.page.paginator.count  # 数据总数量
        return Response(res.dict)


class ArticleContentApi(BaseViewApi):
    '''根据当前文章id找到1对1的文章正题内容,将每一个文章进行缓存到redis中'''

    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()
        res_variable = RedisVariable()
        article_id = kwargs.get('pk', None)
        if article_id is None:
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '抱歉访问的资源不存在!'
            return Response(res.dict)
        redis_key = res_variable.article_key % article_id  # 缓存的key
        val = rec.redis_get_val(redis_key)
        if val:
            '''每次点击都会添加阅读量'''
            rec.article_num_update(article_id)  # 将文章的key进行存储
            key = 'article_read_num_%s' % article_id
            article_read_num = rec.redis_get_val(key)
            data = json.loads(val)
            data['article_read_num'] = article_read_num
            res.data = data
            res.code = status.HTTP_200_OK
            return Response(res.dict)
        else:
            queryset = models.Article.objects.filter(id=article_id).first()
            if queryset is None:
                res.code = status.HTTP_404_NOT_FOUND
                res.error = '抱歉访问的资源不存在!'
                return Response(res.dict)
            rec.article_num_update(article_id)  # 文章真实存在阅读量+1操作
            ser_obj = ArticleContentSerializers(queryset)
            rec.redis_save_val(redis_key, json.dumps(ser_obj.data))  # 存起来
            res.data = ser_obj.data
            res.code = status.HTTP_200_OK
        return Response(res.dict)


class RecentArticleApi(BaseViewApi):
    '''最新新上传的文章显示'''

    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()
        res_variable = RedisVariable()
        redis_key = res_variable.newest_create_article_list
        val = rec.redis_get_val(redis_key)
        if val:
            res.data = json.loads(val)
            res.code = status.HTTP_200_OK
            return Response(res.dict)
        else:
            queryset = models.Article.objects.filter(recommend_state='1').all().order_by('create_date_time')[
                       0:9]  # 按照创建时间进行排序
            ser_obj = RecentArticlesSerializers(queryset, many=True)
            rec.redis_save_val(redis_key, json.dumps(ser_obj.data))
            res.data = ser_obj.data
            res.code = status.HTTP_200_OK
        return Response(res.dict)


class LinksApi(BaseViewApi):
    '''友情链接展示接口 只展示10条链接'''

    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()
        res_variable = RedisVariable()
        redis_key = res_variable.link_list
        val = rec.redis_get_val(redis_key)
        if val:
            res.data = json.loads(val)
            res.code = status.HTTP_200_OK
            return Response(res.dict)
        else:
            queryset = models.Links.objects.filter(is_show='N').all().order_by('id')[0:9]
            ser_obj = LinksSerializers(queryset, many=True)
            rec.redis_save_val(redis_key, json.dumps(ser_obj.data))
            res.data = ser_obj.data
            res.code = status.HTTP_200_OK
        return Response(res.dict)


class SearchApi(GenericViewSet, ListModelMixin):
    '''搜索接口 需要分页处理'''
    queryset = models.Article.objects.all().order_by('order')
    serializer_class = ArticleSerializers
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = SearchFilters  # 将自定义的filterset类进行配置上
    pagination_class = ProjectPagination


'''
搜索没办法作为缓存进行处理(水平不到)
首页展示没有做分页内容
'''


# 留言接口，限制每个留言人的每天的留言次数

class ArticleMessageApi(CreateModelMixin, GenericViewSet):
    queryset = models.ArticleMessage.objects.all()
    serializer_class = ArticleMessageSerializers
    throttle_classes = [ArticleMessageThrottling, ]

    # 前端必须传入3个字段 1. 用户的名称(可以为空) 2.留言言的内容不能为空 3.对那一片文章的留言不能为空 有问题：如果使用不同的用户名进行留言就会出现可以一直留言的问题(添加一个字段进行处理)

    def create(self, request, *args, **kwargs):
        res = BaseResponse()
        data = request.data
        if not data.get('message_name'):  # 没有填写用户名的处理
            _mutable = data._mutable
            data._mutable = True
            data['message_name'] = '匿名用户' + request.META['REMOTE_ADDR']
            data._mutable = _mutable
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            print(e)
            res.code = status.HTTP_412_PRECONDITION_FAILED
            res.error = '留言内容不能为空!'
            return Response(res.dict)
        self.perform_create(serializer)
        res.data = '留言成功!感谢支持!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 关于我的信息
class BloggerContentApi(BaseViewApi):

    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()
        res_variable = RedisVariable()
        redis_key = res_variable.blogger_content  # 关于我的缓存变量
        val = rec.redis_get_val(redis_key)
        if val:
            res.data = json.loads(val)
            res.code = status.HTTP_200_OK
            return Response(res.dict)
        else:
            queryset = models.BloggerContent.objects.filter(is_show='N').order_by('-id').first()  # 只显示1条记录
            ser_obj = BloggerContentSerializers(queryset)
            rec.redis_save_val(redis_key, json.dumps(ser_obj.data))
            res.code = status.HTTP_200_OK
            res.data = ser_obj.data
        return Response(res.dict)


# 文章详情
class ArticleDetailApi(BaseViewApi):
    def get(self, request, *args, **kwargs):
        res = BaseResponse()
        article_id = request.query_params.get('article_id', 0)
        if article_id == 0:
            res.error = '资源错误!',
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        else:
            queryset = models.Article.objects.filter(id=article_id).first()
            if not queryset:
                res.error = '文章不存在!',
                res.code = status.HTTP_404_NOT_FOUND
                return Response(res.dict)


# 处理匹配不到的url
class BlogMatchApi(BaseViewApi):
    pass
