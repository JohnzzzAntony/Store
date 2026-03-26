from django.urls import path
from . import products, categories, orders, payments

urlpatterns = [
    # Products API
    path('products/', products.list_products, name='api_list_products'),
    path('products/create/', products.create_product, name='api_create_product'),
    path('products/<int:product_id>/', products.get_product, name='api_get_product'),
    path('products/<int:product_id>/update/', products.update_product, name='api_update_product'),
    path('products/<int:product_id>/patch/', products.patch_product, name='api_patch_product'),
    path('products/<int:product_id>/delete/', products.delete_product, name='api_delete_product'),

    # Categories API
    path('categories/', categories.list_categories, name='api_list_categories'),
    path('categories/create/', categories.create_category, name='api_create_category'),
    path('categories/<int:category_id>/update/', categories.update_category, name='api_update_category'),
    path('categories/<int:category_id>/delete/', categories.delete_category, name='api_delete_category'),

    # Orders API
    path('orders/', orders.list_orders, name='api_list_orders'),
    path('orders/create/', orders.create_order, name='api_create_order'),
    path('orders/<int:order_id>/', orders.get_order, name='api_get_order'),
    path('orders/<int:order_id>/status/', orders.update_order_status, name='api_update_order_status'),

    # Payments API
    path('payments/config/', payments.stripe_config, name='api_stripe_config'),
    path('payments/create-intent/', payments.create_payment_intent, name='api_create_payment_intent'),
    path('payments/webhook/', payments.stripe_webhook, name='api_stripe_webhook'),
]
