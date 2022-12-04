from django.urls import path, re_path
from blog import views

urlpatterns = [

    path('links/', views.LinksApi.as_view()),
    path('search/', views.SearchApi.as_view({'get': 'list', })),
    path('category/', views.CategoryApi.as_view()),
    path('article/', views.ArticleApi.as_view()),  # ?category_id=根据分类id 获取文章的全部内容
    path('recentArticle/', views.RecentArticleApi.as_view()), # 最近文章
    path('articleMessage/', views.ArticleMessageApi.as_view({'post': 'create'})),  # 留言
    path('articlecContent/<int:pk>/', views.ArticleContentApi.as_view()),  # 根据文章id进行获取当前的文章详情
    # 关于我的信息展示部分 同时需要写到缓存中
    path('blogger_content/', views.BloggerContentApi.as_view()),
    re_path('(.*)/', views.BlogMatchApi.as_view()),
]
