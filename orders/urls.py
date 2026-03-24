"""
orders/urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    path("",                              views.list_orders,         name="order-list"),
    path("create/",                       views.create_order,        name="order-create"),
    path("<str:order_id>/",               views.get_order,           name="order-detail"),
    path("<str:order_id>/status/",        views.update_order_status, name="order-status"),
]
