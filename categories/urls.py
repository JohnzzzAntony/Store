"""
categories/urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    path("",                             views.list_categories,  name="category-list"),
    path("create/",                      views.create_category,  name="category-create"),
    path("<str:category_id>/update/",    views.update_category,  name="category-update"),
    path("<str:category_id>/delete/",    views.delete_category,  name="category-delete"),
]
