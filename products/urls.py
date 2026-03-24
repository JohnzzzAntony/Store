"""
products/urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    path("",                            views.list_products,  name="product-list"),
    path("create/",                     views.create_product, name="product-create"),
    path("<str:product_id>/",           views.get_product,    name="product-detail"),
    path("<str:product_id>/update/",    views.update_product, name="product-update"),
    path("<str:product_id>/patch/",     views.patch_product,  name="product-patch"),
    path("<str:product_id>/delete/",    views.delete_product, name="product-delete"),
]
