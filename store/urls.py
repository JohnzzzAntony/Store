from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.store, name='store'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Info pages
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('contact/', views.contact, name='contact'),

    # Blog
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),

    # Cart & Checkout
    path('cart/', views.cart, name='cart'),
    path('checkout/', views.checkout, name='checkout'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('firebase-sync/', views.firebase_login_sync, name='firebase-sync'),

    # AJAX
    path('update_item/', views.updateItem, name='update_item'),
    path('process_order/', views.processOrder, name='process_order'),
    path('order-success/', views.order_success, name='order_success'),
    path('clear_products/', views.clear_products, name='clear_products'),
    path('payment/tabby/', views.tabby_payment, name='tabby_payment'),
    path('payment/tamara/', views.tamara_payment, name='tamara_payment'),
    path('create-payment-intent/', views.create_payment_intent, name='create-payment-intent'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe-webhook'),
]