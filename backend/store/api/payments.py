# Moved from payments/views.py
import json, stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from store.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(["GET"])
@permission_classes([AllowAny])
def stripe_config(request):
    return Response({"publishableKey": getattr(settings, "STRIPE_PUBLIC_KEY", "")})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    order_id = request.data.get("orderId")
    if not order_id: return Response({"error": "'orderId' is required."}, status=400)
    try: order = Order.objects.get(id=order_id)
    except Order.DoesNotExist: return Response({"error": "Order not found."}, status=404)
    try:
        from django.contrib.auth.models import User
        from store.models import Customer
        user, customer = User.objects.get(username=request.user.uid), Customer.objects.get(user=User.objects.get(username=request.user.uid))
        if not request.user.is_admin and order.customer != customer: return Response({"error": "Forbidden."}, status=403)
    except (User.DoesNotExist, Customer.DoesNotExist): return Response({"error": "Forbidden."}, status=403)
    if order.status != "Pending": return Response({"error": f"Cannot pay — order status is '{order.status}'."}, status=400)
    amount_cents = int(round(float(order.get_cart_total) * 100))
    try:
        intent = stripe.PaymentIntent.create(amount=amount_cents, currency=getattr(settings, "STRIPE_CURRENCY", "usd"), metadata={"orderId": str(order_id), "userId": request.user.uid}, automatic_payment_methods={"enabled": True})
    except stripe.StripeError as exc: return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    order.transaction_id = intent.id
    order.save()
    return Response({"clientSecret": intent.client_secret, "paymentIntentId": intent.id, "amount": amount_cents, "currency": getattr(settings, "STRIPE_CURRENCY", "usd")})

@csrf_exempt
def stripe_webhook(request):
    payload, sig_header, secret = request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""), settings.STRIPE_WEBHOOK_SECRET
    try:
        if secret: event = stripe.Webhook.construct_event(payload, sig_header, secret)
        else: event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except (ValueError, stripe.error.SignatureVerificationError): return HttpResponse(status=400)
    intent, order_id = event["data"]["object"], (event["data"]["object"].get("metadata") or {}).get("orderId")
    if not order_id: return HttpResponse(status=200)
    try: order = Order.objects.get(id=order_id)
    except Order.DoesNotExist: return HttpResponse(status=200)
    if event["type"] == "payment_intent.succeeded":
        order.status, order.complete = "Paid", True
        order.save()
    elif event["type"] == "payment_intent.canceled":
        order.status = "Cancelled"
        order.save()
    return HttpResponse(status=200)
