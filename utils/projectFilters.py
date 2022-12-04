from django_filters import FilterSet, filters

from blog.models import Article

# 查询条件
class SearchFilters(FilterSet):
    '''按照文章表中的title作为搜索的字段'''
    search = filters.CharFilter(field_name='title', lookup_expr='contains')

    class Meta:
        model = Article
        fields = ['search',]
