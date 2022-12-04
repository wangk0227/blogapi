from django.db import models

__all__ = ['Category', 'Article', 'ArticleMessage', 'Links', 'UserAccount', 'BloggerContent']


class Category(models.Model):
    '''分类表'''
    title = models.CharField(max_length=32, unique=True, verbose_name='分类标题', help_text='当前的分类表,文章要归属与当前的分类',
                             db_index=True)
    category_doc = models.TextField(max_length=255, verbose_name='分类说明')
    create_date_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    order = models.PositiveSmallIntegerField(default=1, verbose_name='排序字段')
    STATE_CHOICES = (('Y', '隐藏'), ('N', '不隐藏'))
    is_show = models.CharField(max_length=16, default='Y', choices=STATE_CHOICES, verbose_name='是否隐藏',
                               help_text='Y隐藏,N不隐藏')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '分类表'
        db_table = 'category'


class Article(models.Model):
    '''文章表'''
    title = models.CharField(max_length=64, verbose_name='文章名称', db_index=True)  # 需要通过文章名进行搜索 需要添加上索引
    excerpt = models.TextField(max_length=255, blank=True, verbose_name='文章摘要')
    create_date_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_date_time = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    order = models.PositiveSmallIntegerField(default=1, verbose_name='排序字段')
    RECOMMEND_CHOICES = ((0, '未发布'), (1, '已发布'))
    recommend_state = models.SmallIntegerField(choices=RECOMMEND_CHOICES, default=0, verbose_name='文章推荐状态')
    # 删除分类后使绑定文章为空，未分类状态
    article_category = models.ForeignKey(to='Category', related_name='category_article', on_delete=models.SET_NULL,
                                         verbose_name='当前文章归属', blank=True, null=True)
    header = models.TextField(verbose_name='设置锚点信息')
    content = models.TextField(verbose_name='博客正文')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '文章表'
        db_table = 'article'


class ArticleMessage(models.Model):
    '''文章留言表'''
    message_name = models.CharField(max_length=32, verbose_name='留言人的名称', help_text='用来记录当前留言的的昵称')
    create_date_time = models.DateTimeField(auto_now_add=True, verbose_name='留言时间')
    message_content = models.TextField(max_length=255, verbose_name='留言的主内容')
    article = models.ForeignKey(to='Article', related_name='message_article', on_delete=models.CASCADE,
                                verbose_name='留言的归属', help_text='这条留言归属与那篇文章')

    def __str__(self):
        return self.message_name

    class Meta:
        verbose_name = '留言表'
        db_table = 'article_message'


# 友情链接表
class Links(models.Model):
    link_name = models.CharField(max_length=32, verbose_name='链接名称')
    link = models.CharField(max_length=64, verbose_name='链接地址')
    STATE_CHOICES = (('Y', '隐藏'), ('N', '不隐藏'))
    is_show = models.CharField(max_length=16, default='Y', choices=STATE_CHOICES, verbose_name='是否隐藏',
                               help_text='Y隐藏,N不隐藏')

    def __str__(self):
        return self.link_name

    class Meta:
        verbose_name = '友情链接'
        db_table = 'links'


# 博主信息表(只是作为登录使用)
class UserAccount(models.Model):
    name = models.CharField(max_length=32, verbose_name='用户名', default='匿名用户')
    username = models.CharField(max_length=32, verbose_name="用户登录账户", unique=True)
    pwd = models.CharField(max_length=32, verbose_name="密文密码")
    user_img = models.ImageField(upload_to="project_image/picture", verbose_name='个人头像',
                                 default='project_image/picture/default.png',
                                 null=True)
    USER_ROLE = ((0, '管理员'), (1, '普通会员'), (2, '游客'))  # 开放一个接口直接获取
    role = models.SmallIntegerField(choices=USER_ROLE, verbose_name='角色说明')
    STATE_CHOICES = (('Y', '停用'), ('N', '启用'))
    is_show = models.CharField(max_length=16, default='Y', choices=STATE_CHOICES, verbose_name='是否隐藏',
                               help_text='Y停用,N启用')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户表'
        db_table = 'user_account'


# 网站建站
class BloggerContent(models.Model):
    '''当前网站建站这的信息表 网站的名称 网站的log 网站的说明 网站的建站者的qq邮箱微信二维码'''
    created_web_email = models.CharField(max_length=32, verbose_name='建站者联系邮箱')
    created_web_qq = models.CharField(max_length=32, verbose_name='建站者qq')
    created_web_wechat = models.ImageField(upload_to='project_image/wechat', verbose_name='建站者微信二维码',
                                           default='project_image/wechat/default.jpg')
    STATE_CHOICES = (('Y', '隐藏'), ('N', '不隐藏'))
    is_show = models.CharField(max_length=16, default='Y', choices=STATE_CHOICES, verbose_name='是否隐藏',
                               help_text='Y隐藏,N不隐藏')

    def __str__(self):
        return self.created_web_email

    class Meta:
        verbose_name = '网站信息表'
        db_table = 'blogger_content'
