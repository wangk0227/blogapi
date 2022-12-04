class RedisVariable:
    """缓存所需要的redis变量"""

    def __init__(self):
        self.link_list = 'link_list'
        self.article_key = 'article_%s'
        self.category_list = 'category_list'
        self.blogger_content = 'blogger_content'  # 站点缓存
        self.newest_create_article_list = 'newest_create_article_list'


"""jwt秘钥配置"""
SECRET = 'www.kaixinblog.con'

"""前端携带的token名称"""
TOKENNAME = 'HTTP_ACCEPTTOKEN'

'''
后台服务器异常全部为5001
504超时错误
505是版本错误
511 身份验证错误
501 无当前接口
BooleanField 有问题

'''
