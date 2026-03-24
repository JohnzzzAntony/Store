"""
firebase_auth_app/urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    path("sync-user/",             views.sync_user,     name="auth-sync-user"),
    path("me/",                    views.get_me,         name="auth-me"),
    path("users/",                 views.list_users,     name="auth-list-users"),
    path("users/<str:uid>/role/",  views.set_user_role,  name="auth-set-role"),
]
