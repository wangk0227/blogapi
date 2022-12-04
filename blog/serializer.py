import datetime
from rest_framework import serializers

from blog import models
from utils.redisCache import RedisCache


class CategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ['id', 'title']


class ArticleSerializers(serializers.ModelSerializer):
    article_read_num = serializers.SerializerMethodField()
    create_date_time = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = models.Article
        fields = ['id', 'title', 'excerpt', 'create_date_time', 'article_read_num', 'category']

    def get_article_read_num(self, obj):
        rec = RedisCache()
        key = 'article_read_num_%s' % obj.id
        val = rec.redis_get_val(key)
        return val or 0

    def get_create_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y年%m月%d日")
        return data

    def get_category(self, obj):
        return obj.article_category.title


class RecentArticlesSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = ['id', 'title']


class ArticleContentSerializers(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    article_read_num = serializers.SerializerMethodField()
    create_date_time = serializers.SerializerMethodField()

    class Meta:
        model = models.Article
        fields = ['title', 'content', 'article_read_num', 'category','create_date_time','header']

    def get_article_read_num(self, obj):
        rec = RedisCache()
        key = 'article_read_num_%s' % obj.id
        val = rec.redis_get_val(key)
        return val or 0

    def get_category(self, obj):
        return obj.article_category.title

    def get_create_date_time(self, obj):
        time = str(obj.create_date_time).split('.')[0]
        time_data = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)
        data = datetime.datetime.strftime(time_data, "%Y年%m月%d日")
        return data

class LinksSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Links
        fields = ['link_name', 'link']


class ArticleMessageSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.ArticleMessage
        fields = ['message_name', 'message_content', 'article']


class BloggerContentSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.BloggerContent
        fields = ['created_web_email', 'created_web_qq', 'created_web_wechat']
