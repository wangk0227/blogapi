from django.urls import path, re_path
from admin_background import views

# 关于我的增删改查部分 同时修改时需要 更新redis 添加时需要更新redis
# 文章分类表增删改查部分 # 同时修改时需要 更新redis 添加时需要更新redis
# 文章增删改查 # 同时修改时需要 更新redis 添加时需要更新redis
# 友情链接的增删改查 # 同时修改时需要 更新redis 添加时需要更新redis
# 留言表的增删改查
urlpatterns = [
    path('users/quit/', views.LoginQuitApi.as_view()),  # 退出
    path('users/logins/', views.LoginApi.as_view()),  # 登录
    path('users/viewing/', views.UserDeleteListApi.as_view()),  # 删除 查看 查看部分
    path('users/register/', views.RegisterApi.as_view()),  # 注册
    path('users/update/<int:pk>/', views.UserUpdateApi.as_view({'put': 'update'})),  # 用户更新

    # 友情链接
    path('links/', views.LinksApis.as_view({'get': 'list', 'post': 'create'})),
    path('link/<int:pk>/', views.LinksApi.as_view({'put': 'update', 'delete': "destroy", 'get': 'retrieve'})),
    # 分类
    path('categorys/', views.CategoryApis.as_view({'get': 'list', 'post': 'create'})),
    path('category/<int:pk>/', views.CategoryApi.as_view({'put': 'update', 'delete': "destroy", 'get': 'retrieve'})),
    # 文章
    path('articles/', views.ArticleApis.as_view({'get': 'list', 'post': 'create'})),
    path('article/<int:pk>/', views.ArticleApi.as_view({'put': 'update', 'delete': "destroy", 'get': 'retrieve'})),
    # 关于网站信息表
    path('blogger/contents/', views.BloggerContentApis.as_view({'get': 'list', 'post': 'create'})),  # get 与 post
    path('blogger/content/<int:pk>/',
         views.BloggerContentApi.as_view({'put': 'update', 'delete': "destroy", 'get': 'retrieve'})),  # get 与 post
    # 留言
    path('articlesMessages/', views.ArticleMessageApis.as_view({'get': 'list'})),  # 传入的是文章的id?article_id  根据文章id获取留言内容
    path('articlesMessage/<int:pk>/', views.ArticleMessageApi.as_view({'delete': "destroy"})),

    # 生成随机的验证码
    path('loginCode/img/', views.LoginCodeApi.as_view()),

    # 富文本上传配置url
    path('editor/img/', views.EditorImgApi.as_view()),

    # 错误路由处理
    re_path('(.*)/', views.AdminMatchApi.as_view()),

]
