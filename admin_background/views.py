# 隐藏后台对网站的增删改查 开始处理登录注修改删除操作的后端行为
import os
import re
import uuid
from math import ceil
from django.conf import settings
from rest_framework import status
from django.db.models.query import QuerySet
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin,
                                   UpdateModelMixin)
from utils.publicConfig import *
from utils.pwdMd5 import pwd_md5
from utils.redisCache import CONN
from utils.errorLog import logger
from utils.baseApi import BaseViewApi
from utils.redisCache import RedisCache
from utils.loginCaptcha import generatecode
from utils.baseResponse import BaseResponse
from utils.authToken import JwtToken, UserAuth  # 生成token值 用户认证
from utils.projectPager import ProjectPagination
from utils.projectPermission import BlogPermission
from utils.projectThrottling import CodeImgThrottling
from blog.models import UserAccount, BloggerContent, Links, Category, Article, ArticleMessage
from admin_background.serializer import UserGetSerializers, UserPutCreateSerializers, BloggerContentSerializers, \
    LinksSerializers, CategorySerializers, ArticleSerializers, ArticleUpdateSerializers, ArticleMessageSerializers


# 用户登录
class LoginApi(BaseViewApi):
    '''用户的登录接口 不需要进行权限认证和登录认证操作，这一步相当于其他的全部'''

    def post(self, request, *args, **kwargs):
        res = BaseResponse()
        jwt = JwtToken()
        user_name = request.data.get('username', '')
        user_pwd = pwd_md5(user_name, request.data.get('pwd', ''))  # 多次加密
        # user_pwd = request.data.get('pwd', '')
        # 如果存在那么就会获取对象，如果不存在就没有
        user_obj = UserAccount.objects.filter(username=user_name, pwd=user_pwd).first()
        if not user_obj:
            res.error = '用户名密码错误,请重新输入!'
            res.code = status.HTTP_403_FORBIDDEN
            return Response(res.dict)
        elif user_obj.is_show == 'Y':  # Y代表无法登录
            res.error = '抱歉你的账户无法使用'
            res.code = status.HTTP_403_FORBIDDEN
            return Response(res.dict)
        try:
            # 生成两种token
            uuid_token = str(uuid.uuid4())  # 使用uuid作为token
            token, refresh_token = jwt.generate_token(user_obj.id, refresh=False)
            CONN.setex(uuid_token, 86400, token)  # 设置过期时间1天 如果关闭浏览器会自动删除cookie 防止出现问题 设置过期时间
            res.user_data = {'username': user_obj.name, 'user_picture': 'media/' + str(user_obj.user_img),
                             'user_role': user_obj.get_role_display()}
            res.token = uuid_token
            res.data = '登录成功!'
            res.code = status.HTTP_200_OK
        except Exception as e:
            print(e)
            logger.error(e)
            res.code = status.HTTP_401_UNAUTHORIZED
            res.error = '创建登录令牌失败'
        return Response(res.dict)


# 退出登录
class LoginQuitApi(BaseViewApi):

    def delete(self, request, *args, **kwargs):
        '''清除redis中的认证信息'''
        res = BaseResponse()
        rec = RedisCache()
        token = request.META.get(TOKENNAME, None)
        if not token:
            res.code = status.HTTP_401_UNAUTHORIZED
            res.error = '未携带认证信息!'
            return Response(res.dict)
        rec.redis_delete_val(token)
        res.code = status.HTTP_200_OK
        res.data = '退出成功!'
        return Response(res.dict)


# 用户的新增
class RegisterApi(BaseViewApi):
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def post(self, request, *args, **kwargs):
        '''当前注册端口，必须传入的值有1.用户名 2.用户密码(密文) 3.用户的角色信息'''
        res = BaseResponse()
        pic = request.FILES.get('user_img')
        data = self.request.data
        _mutable = data._mutable
        data._mutable = True
        data['pwd'] = pwd_md5(data.get('username'), data.get('pwd'))
        data._mutable = _mutable
        ser_obj = UserPutCreateSerializers(data=data)
        if ser_obj.is_valid():
            if not pic:
                ser_obj.save()
                res.code = status.HTTP_200_OK
                res.data = '新建用户成功!'
            else:
                ser_obj.user_img = pic
                ser_obj.save()
                res.code = status.HTTP_200_OK
                res.data = '新建用户成功!'
        else:
            res.code = status.HTTP_401_UNAUTHORIZED
            res.error = '用户添加失败,用户名重复!'
        return Response(res.dict)


# 用户删除，查看列表 查看单个 查看单个数据 ?user_id=1
class UserDeleteListApi(BaseViewApi):
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        res = BaseResponse()
        queryset = UserAccount.objects
        if user_id:
            user_obj = queryset.filter(id=user_id).first()
            if not user_obj:
                res.error = '用户不存在'
                res.code = status.HTTP_404_NOT_FOUND
                return Response(res.dict)
            ser_obj = UserPutCreateSerializers(user_obj)
            res.data = ser_obj.data
            res.code = status.HTTP_200_OK
            return Response(res.dict)

        queryset = queryset.all().order_by('id')

        # 分页器
        page = ProjectPagination()
        # 分页计算
        page_count = ceil(len(queryset) / page.page_size)  # 总页码 ceil 方法只要有余数就进1
        present_page = int(request.query_params.get('page', 1))  # 当前所在页码
        if present_page < 1 or present_page > page_count:
            present_page = 1
        start_page = present_page - page.max_page  # 起始页码范围
        end_page = present_page + page.max_page  # 结束页码范围

        pagination_queryset = page.paginate_queryset(queryset, request, self)

        ser_obj = UserGetSerializers(pagination_queryset, many=True)
        res.data = ser_obj.data
        res.code = status.HTTP_200_OK
        res.page_count = page_count
        res.present_page = present_page
        res.start_page = start_page if start_page > 1 else 1  # 计算
        res.end_page = end_page if end_page < page_count else page_count  # 计算
        res.page_data_count = page.page.paginator.count  # 数据的总数量

        return Response(res.dict)

    def delete(self, request, *args, **kwargs):
        res = BaseResponse()
        user_id = request.query_params.get('user_id')
        user_obj = UserAccount.objects.filter(id=user_id)
        if not user_obj.first():
            res.error = '用户不存在或者已经被删除!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        user_obj.delete()
        res.data = '删除成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 用户的更新 user_update/1/
class UserUpdateApi(UpdateModelMixin, GenericViewSet):
    authentication_classes = [UserAuth, ]
    queryset = UserAccount.objects.all().order_by('-id')
    serializer_class = UserPutCreateSerializers
    permission_classes = [BlogPermission, ]

    def update(self, request, *args, **kwargs):
        res = BaseResponse()
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Exception as e:
            logger.error(e)
            res.error = str(e)
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        data = self.request.data
        _mutable = data._mutable
        data._mutable = True
        username = data.get('username')
        r_pwa = pwd_md5(data.get('username'), data.get('r_pwd'))  # 前端后端同时加密
        user_obj = UserAccount.objects.filter(username=username, pwd=r_pwa).first()
        if not user_obj:
            res.error = '原账户密码不正确!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        data['pwd'] = pwd_md5(data.get('username'), data.get('pwd'))
        del data['r_pwd']
        data._mutable = _mutable

        serializer = self.get_serializer(instance, data=data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(e)
            res.error = '缺少必填内容!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        self.perform_update(serializer)
        res.data = '用户修改成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 文章：1对1序列化器没办法进行显示储存
# 需要传入字段：title excerpt order recommend_state article_category
# title recommend_state content 强制字段
# 查询将全部字段都给查询到了 也需要删除对应的缓存内容
# 文章1
class ArticleApis(GenericViewSet, ListModelMixin, CreateModelMixin):
    queryset = Article.objects.all().order_by('order')
    serializer_class = ArticleSerializers
    pagination_class = ProjectPagination
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def create(self, request, *args, **kwargs):
        rec = RedisCache()  # 缓存
        res = BaseResponse()
        rec_variable = RedisVariable()
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(e)
            res.error = '缺少必须填写内容!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        self.perform_create(serializer)
        rec.redis_delete_val(rec_variable.newest_create_article_list)
        res.data = '文章添加成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 文章2
class ArticleApi(GenericViewSet, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    queryset = Article.objects.all().order_by('order')
    serializer_class = ArticleUpdateSerializers
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def retrieve(self, request, *args, **kwargs):
        res = BaseResponse()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        serializer = self.get_serializer(instance)
        res.code = status.HTTP_200_OK
        res.data = serializer.data
        return Response(res.dict)

    def update(self, request, *args, **kwargs):
        '''重写源码,返回自己想要的数据结构'''
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        partial = kwargs.pop('partial', False)
        rec_variable = RedisVariable()
        data = request.data
        if not data.get('excerpt', None) and data.get('content'):
            _mutable = data._mutable
            data._mutable = True
            summary = re.sub(r'<.*?>', u'', data['content'])[0:240]
            data['excerpt'] = ''.join(summary.split()).replace('&nbsp;', '')
            data._mutable = _mutable
        try:
            instance = self.get_object()
            article_id = instance.id
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        serializer = self.get_serializer(instance, data=data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '缺少必填内容!'
            return Response(res.dict)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        rec.redis_delete_val(rec_variable.article_key % article_id)
        rec.redis_delete_val(rec_variable.newest_create_article_list)
        res.code = status.HTTP_200_OK
        res.data = '修改成功!'
        return Response(res.dict)

    def destroy(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        try:
            instance = self.get_object()
            article_id = instance.id
            # 删除文章时现将图片匹配到，全部删除
            img_name_list = re.findall('[a-z0-9]{32}.[a-z]{3}', instance.content)
            for img_name in img_name_list:
                file_path = os.path.join(settings.MEDIA_ROOT, "editor_image", img_name)  # 项目下的图片路径拼接
                if os.path.exists(file_path):
                    os.remove(file_path)
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        rec.redis_delete_val(rec_variable.article_key % article_id)
        rec.redis_delete_val(rec_variable.newest_create_article_list)
        rec.article_num_delete(article_id)  # 删除阅读量
        self.perform_destroy(instance)
        res.code = status.HTTP_200_OK
        res.data = '删除成功!'
        return Response(res.dict)


# 留言查看
class ArticleMessageApis(GenericViewSet, ListModelMixin):
    queryset = ArticleMessage.objects.all().order_by('-id')
    serializer_class = ArticleMessageSerializers
    pagination_class = ProjectPagination
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def get_queryset(self):
        article_id = self.request.query_params.get('article_id', 0)
        assert self.queryset is not None, (
                "'%s' should either include a `queryset` attribute, "
                "or override the `get_queryset()` method."
                % self.__class__.__name__
        )

        queryset = self.queryset
        if isinstance(queryset, QuerySet):
            if article_id == 0:
                queryset = queryset.all()
            else:
                queryset = queryset.filter(article=article_id)
        return queryset


# 留言删除
class ArticleMessageApi(GenericViewSet, DestroyModelMixin):
    queryset = ArticleMessage.objects.all().order_by('id')
    serializer_class = ArticleMessageSerializers
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def destroy(self, request, *args, **kwargs):
        res = BaseResponse()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        self.perform_destroy(instance)
        res.code = status.HTTP_200_OK
        res.data = '删除成功!'
        return Response(res.dict)


# 友情链接1
class LinksApis(GenericViewSet, CreateModelMixin, ListModelMixin):
    authentication_classes = [UserAuth, ]
    queryset = Links.objects.all().order_by('-id')
    serializer_class = LinksSerializers
    pagination_class = ProjectPagination
    permission_classes = [BlogPermission, ]

    def create(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(e)
            res.error = '缺少填写内容!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        self.perform_create(serializer)
        rec.redis_delete_val(rec_variable.link_list)
        res.data = '链接添加成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 友情链接2
class LinksApi(GenericViewSet, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    authentication_classes = [UserAuth, ]
    queryset = Links.objects.all().order_by('-id')
    serializer_class = LinksSerializers
    permission_classes = [BlogPermission, ]

    def retrieve(self, request, *args, **kwargs):
        res = BaseResponse()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        serializer = self.get_serializer(instance)
        res.code = status.HTTP_200_OK
        res.data = serializer.data
        return Response(res.dict)

    def update(self, request, *args, **kwargs):
        '''重写源码,返回自己想要的数据结构'''
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '缺少必填内容!'
            return Response(res.dict)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        rec.redis_delete_val(rec_variable.link_list)
        res.code = status.HTTP_200_OK
        res.data = '链接修改成功!'
        return Response(res.dict)

    def destroy(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        self.perform_destroy(instance)
        rec.redis_delete_val(rec_variable.link_list)
        res.code = status.HTTP_200_OK
        res.data = '链接删除成功!'
        return Response(res.dict)


# 分类1
class CategoryApis(GenericViewSet, CreateModelMixin, ListModelMixin):
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializers
    pagination_class = ProjectPagination

    def create(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(e)
            res.error = '缺少必填字段或者分类名称重复!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        self.perform_create(serializer)
        rec.redis_delete_val(rec_variable.category_list)
        res.data = '分类添加成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 分类2

class CategoryApi(GenericViewSet, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    authentication_classes = [UserAuth, ]
    queryset = Category.objects.all().order_by('order')
    serializer_class = CategorySerializers
    permission_classes = [BlogPermission, ]

    def retrieve(self, request, *args, **kwargs):
        res = BaseResponse()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '数据不存在!'
            return Response(res.dict)
        serializer = self.get_serializer(instance)
        res.code = status.HTTP_200_OK
        res.data = serializer.data
        return Response(res.dict)

    def update(self, request, *args, **kwargs):
        '''重写源码,返回自己想要的数据结构'''
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '缺少必填字段或者分类名称重复!'
            return Response(res.dict)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        rec.redis_delete_val(rec_variable.category_list)
        res.code = status.HTTP_200_OK
        res.data = '分类修改成功!'
        return Response(res.dict)

    def destroy(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        self.perform_destroy(instance)
        rec.redis_delete_val(rec_variable.category_list)
        res.code = status.HTTP_200_OK
        res.data = '分类删除成功!'
        return Response(res.dict)


# 个人网站信息1

class BloggerContentApis(GenericViewSet, CreateModelMixin, ListModelMixin):
    authentication_classes = [UserAuth, ]
    queryset = BloggerContent.objects.all().order_by('-id')
    serializer_class = BloggerContentSerializers
    pagination_class = ProjectPagination
    permission_classes = [BlogPermission, ]

    def create(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(e)
            res.error = '缺少填写字段!'
            res.code = status.HTTP_404_NOT_FOUND
            return Response(res.dict)
        self.perform_create(serializer)
        rec.redis_delete_val(rec_variable.blogger_content)
        res.data = '信息添加成功!'
        res.code = status.HTTP_200_OK
        return Response(res.dict)


# 个人网站信息2
class BloggerContentApi(GenericViewSet, UpdateModelMixin, RetrieveModelMixin, DestroyModelMixin):
    authentication_classes = [UserAuth, ]
    queryset = BloggerContent.objects.all().order_by('-id')
    serializer_class = BloggerContentSerializers
    permission_classes = [BlogPermission, ]

    def retrieve(self, request, *args, **kwargs):
        res = BaseResponse()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        serializer = self.get_serializer(instance)
        res.code = status.HTTP_200_OK
        res.data = serializer.data
        return Response(res.dict)

    def update(self, request, *args, **kwargs):
        '''重写源码,返回自己想要的数据结构'''
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '缺少必填内容!'
            return Response(res.dict)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        rec.redis_delete_val(rec_variable.blogger_content)
        res.code = status.HTTP_200_OK
        res.data = '修改成功!'
        return Response(res.dict)

    def destroy(self, request, *args, **kwargs):
        res = BaseResponse()
        rec = RedisCache()  # 缓存
        rec_variable = RedisVariable()
        try:
            instance = self.get_object()
        except Exception as e:  # 截取当前源码异常 返回当前自定义内容
            logger.error(e)
            res.code = status.HTTP_404_NOT_FOUND
            res.error = str(e)
            return Response(res.dict)
        rec.redis_delete_val(rec_variable.blogger_content)
        self.perform_destroy(instance)
        res.code = status.HTTP_200_OK
        res.data = '信息删除成功!'
        return Response(res.dict)


'''返回登录图片'''


class LoginCodeApi(BaseViewApi):
    throttle_classes = [CodeImgThrottling,]

    # 需要加上限流组件
    def post(self, request, *args, **kwargs):
        res = BaseResponse()
        code_num, code_img_url = generatecode()
        res.code = status.HTTP_200_OK
        res.url = code_img_url
        res.captcha = code_num
        return Response(res.dict)

    def delete(self, request, *args, **kwargs):
        # 登录成功后删除全部的验证码图片
        path = os.path.join(settings.MEDIA_ROOT, "login_captcha")
        for root, dirs, files in os.walk(path):
            for name in files:
                if name.endswith(".png"):
                    os.remove(os.path.join(root, name))
        res = BaseResponse()
        res.code = status.HTTP_200_OK
        res.data = 'ok'
        return Response(res.dict)


'''富文本编辑器上传图片'''


class EditorImgApi(BaseViewApi):
    authentication_classes = [UserAuth, ]
    permission_classes = [BlogPermission, ]

    def post(self, request, *args, **kwargs):
        res = BaseResponse()
        image_obj = request.FILES.get('editorImageName')
        if not image_obj:
            res.code = status.HTTP_404_NOT_FOUND
            res.error = '上传图片对象不存在!'
            return Response(res.dict)
        img_name = image_obj.name  # 获取图片的name属性
        path = os.path.join(settings.MEDIA_ROOT, "editor_image", img_name)
        with open(path, 'wb') as file:
            for line in image_obj:
                file.write(line)
        # 拼接路径进行返回
        file_path = os.path.join('media/editor_image', img_name)
        res.code = status.HTTP_200_OK
        res.url = file_path
        res.alt = img_name
        res.href = '无'
        return Response(res.dict)

    def delete(self, request, *args, **kwargs):
        # 删除编辑器中的图片
        res = BaseResponse()
        data = request.data
        if not request.user.role == 0:
            res.code = status.HTTP_403_FORBIDDEN
            res.error = '无权删除!'
            return Response(res.dict)
        for img_name in data:
            file_path = os.path.join(settings.MEDIA_ROOT, "editor_image", img_name)  # 项目下的图片路径拼接
            if os.path.exists(file_path):
                os.remove(file_path)
        res.code = status.HTTP_200_OK
        res.data = 'ok'
        return Response(res.dict)


# 处理当前app匹配不到的url
class AdminMatchApi(BaseViewApi):
    pass
