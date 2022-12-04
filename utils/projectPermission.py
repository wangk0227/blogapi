from rest_framework import permissions

from rest_framework.permissions import BasePermission


class BlogPermission(BasePermission):

    def has_permission(self, request, view):
        user_grade = request.user
        if request.method == 'POST':
            if user_grade.role == 0:
                return True
            return False
        if user_grade:  # 如果当前name = 1 那么就有权限 否则就没有权限
            return True  # 有权限，api才能访问
        else:
            return False  # 无权访问, api无权访问

    def has_object_permission(self, request, view, obj):
        '''将权限控制到路由层面'''
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.user.role == 0:  # 权限为管理员的情况下，修改删除的操作
            return True
        else:
            return False
