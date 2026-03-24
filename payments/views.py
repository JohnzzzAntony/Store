"""
payments/views.py
Stripe payment integration.

  GET  /api/payments/config/          — returns Stripe publishable key
  POST /api/payments/create-intent/   — creates PaymentIntent for an order
  POST /api/payments/webhook/         — Stripe webhook handler
"""

import json

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from store.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY


# ── GET /api/payments/config/ ────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([AllowAny])
def stripe_config(request):
    """Frontend calls this on load to initialise Stripe.js with the publishable key."""
    return Response({"publishableKey": settings.STRIPE_PUBLISHABLE_KEY})


# ── POST /api/payments/create-intent/ ───────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """
    Frontend sends: { "orderId": "<orderId>" }

    Steps:
      1. Load + validate the order from Django
      2. Create Stripe PaymentIntent (amount in cents)
      3. Store paymentIntentId on the order
      4. Return { clientSecret, paymentIntentId, amount }
    """
    order_id = request.data.get("orderId")
    if not order_id:
        return Response({"error": "'orderId' is required."}, status=400)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=404)

    # Ownership check
    try:
        from django.contrib.auth.models import User
        from store.models import Customer
        user = User.objects.get(username=request.user.uid)
        customer = Customer.objects.get(user=user)
        if not request.user.is_admin and order.customer != customer:
            return Response({"error": "Forbidden."}, status=403)
    except (User.DoesNotExist, Customer.DoesNotExist):
        return Response({"error": "Forbidden."}, status=403)

    if order.status != "Pending":
        return Response(
            {"error": f"Cannot pay — order status is '{order.status}'."},
            status=400,
        )

    # Stripe uses smallest currency unit (cents for USD)
    amount_cents = int(round(float(order.get_cart_total) * 100))

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=getattr(settings, "STRIPE_CURRENCY", "usd"),
            metadata={
                "orderId": str(order_id),
                "userId":  request.user.uid,
            },
            automatic_payment_methods={"enabled": True},
        )
    except stripe.StripeError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    # Persist the intent ID on the order
    order.transaction_id = intent.id
    order.save()

    return Response({
        "clientSecret":    intent.client_secret,
        "paymentIntentId": intent.id,
        "amount":          amount_cents,
        "currency":        getattr(settings, "STRIPE_CURRENCY", "usd"),
    })


# ── POST /api/payments/webhook/ ─────────────────────────────────────────────
@csrf_exempt
def stripe_webhook(request):
    """
    Register this URL in Stripe Dashboard → Developers → Webhooks.
    Listens for:
      payment_intent.succeeded      → order status = 'Paid'
      payment_intent.payment_failed → order status = 'Pending' (no change)
      payment_intent.canceled       → order status = 'Cancelled'
    """
    payload    = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    secret     = settings.STRIPE_WEBHOOK_SECRET

    try:
        if secret:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        else:
            # Development — no signature check
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError:
        return HttpResponse("Invalid payload.", status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature.", status=400)

    intent   = event["data"]["object"]
    order_id = (intent.get("metadata") or {}).get("orderId")

    if not order_id:
        return HttpResponse("No orderId in metadata — ignored.", status=200)

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse("Order not found.", status=200)

    event_type = event["type"]

    if event_type == "payment_intent.succeeded":
        order.status = "Paid"
        order.complete = True
        order.save()

    elif event_type == "payment_intent.canceled":
        order.status = "Cancelled"
        order.save()

    # payment_intent.payment_failed — leave as 'Pending' so user can retry

    return HttpResponse(status=200)
