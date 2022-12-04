# 配置redis 隐藏  需要修改mysqlip 与redi ip
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # 执行的redis环境包
        'LOCATION': 'redis://127.0.0.1:6379',  # 需要改为内网ip地址
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',  # 客户端类环境包
            # 'PASSWORD': 'wangkaixin',  # 密码
        }
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST':'127.0.0.1', # 服务器外网，上传到服务器后需要改成内网
        'PORT':'3306', # mysql的端口
        'USER':'root', # mysql的账户
        'PASSWORD':'123456', # mysql的密码
        'NAME':'blog' # mysql的数据库，在django中创建的表在那个数据库进行存储
    },
}