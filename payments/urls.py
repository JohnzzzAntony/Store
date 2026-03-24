"""
payments/urls.py
"""
from django.urls import path
from . import views

urlpatterns = [
    path("config/",          views.stripe_config,          name="stripe-config"),
    path("create-intent/",   views.create_payment_intent,  name="stripe-create-intent"),
    path("webhook/",         views.stripe_webhook,         name="stripe-webhook"),
]
