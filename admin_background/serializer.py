import datetime
from rest_framework import serializers

from blog import models


# 注册使用的序列化器
class UserGetSerializers(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = models.UserAccount
        fields = '__all__'

        extra_kwargs = {
            'pwd': {'write_only': True},  # 不读 只写
        }

    def get_role(self, obj):
        return obj.get_role_display()


class UserPutCreateSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.UserAccount
        fields = '__all__'
        extra_kwargs = {
            'pwd': {'write_only': True},  # 不读 只写
        }


class BloggerContentSerializers(serializers.ModelSerializer):
    created_web_wechat_url = serializers.SerializerMethodField()

    class Meta:
        model = models.BloggerContent
        fields = ['id', 'created_web_email', 'created_web_qq', 'created_web_wechat', 'is_show',
                  'created_web_wechat_url']

    def get_created_web_wechat_url(self, obj):
        return 'media/' + str(obj.created_web_wechat)


class LinksSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Links
        fields = '__all__'


class CategorySerializers(serializers.ModelSerializer):
    create_date_time = serializers.SerializerMethodField()

    class Meta:
        model = models.Category
        fields = '__all__'

    def get_create_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y-%m-%d")
        return data


class ArticleSerializers(serializers.ModelSerializer):
    create_date_time = serializers.SerializerMethodField()
    update_date_time = serializers.SerializerMethodField()
    article_category_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Article
        fields = ['id', 'create_date_time', 'update_date_time', 'article_category_name', 'content', 'title',
                  'article_category', 'order', 'excerpt', 'recommend_state']
        extra_kwargs = {
            'order': {'write_only': True},  # 只写 不读
            'content': {'write_only': True},
            'article_category': {'write_only': True}
        }

    def get_create_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y-%m-%d")
        return data

    def get_update_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y-%m-%d")
        return data

    def get_article_category_name(self, obj):
        if obj.article_category_id:
            return obj.article_category.title
        return '未分类'


class ArticleUpdateSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = ['id', 'title', 'excerpt', 'order', 'recommend_state', 'content', 'article_category','header']


class ArticleMessageSerializers(serializers.ModelSerializer):
    article = serializers.SerializerMethodField()
    create_date_time = serializers.SerializerMethodField()

    class Meta:
        model = models.ArticleMessage
        fields = '__all__'

    def get_article(self, obj):
        return obj.article.title

    def get_create_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y-%m-%d")
        return data
