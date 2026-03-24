"""
orders/views.py
Order management using Django models.

  POST   /api/orders/create/         — customer creates an order
  GET    /api/orders/                — customer: own orders | admin: all orders
  GET    /api/orders/<id>/           — owner or admin
  PATCH  /api/orders/<id>/status/    — admin only
"""

from datetime import datetime, timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from firebase_auth_app.permissions import IsFirebaseAdmin
from store.models import Order, OrderItem, Product, Customer, ShippingAddress
from store.core.notifications import send_order_notification
from django.contrib.auth.models import User


VALID_STATUSES = {"Pending", "Paid", "Shipped", "Delivered", "Cancelled"}


# ── POST /api/orders/create/ ─────────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Frontend sends:
    {
      "items": [{"productId": "abc", "quantity": 2}],
      "shippingAddress": {"line1": "...", "city": "...", "country": "..."}
    }
    """
    items = request.data.get("items", [])
    if not items:
        return Response({"error": "Order must contain at least one item."}, status=400)

    # Get Django user
    try:
        user = User.objects.get(username=request.user.uid)
        customer = Customer.objects.get(user=user)
    except (User.DoesNotExist, Customer.DoesNotExist):
        return Response({"error": "User not found."}, status=400)

    validated_items = []
    total_amount = 0.0

    for item in items:
        pid = item.get("productId")
        try:
            qty = int(item.get("quantity", 1))
            assert qty >= 1
        except (ValueError, AssertionError):
            return Response({"error": f"Invalid quantity for item: {item}"}, status=400)

        if not pid:
            return Response({"error": "Each item must have a 'productId'."}, status=400)

        try:
            prod = Product.objects.get(id=pid, in_stock=True)
        except Product.DoesNotExist:
            return Response({"error": f"Product '{pid}' not found or out of stock."}, status=404)

        unit_price = float(prod.price)
        validated_items.append({
            "product": prod,
            "quantity": qty,
            "price": unit_price,
            "subtotal": round(unit_price * qty, 2),
        })
        total_amount += unit_price * qty

    # Create order
    order = Order.objects.create(
        customer=customer,
        complete=False,
        transaction_id="",
        payment_method="",
        status="Pending",
    )

    # Create order items
    for item in validated_items:
        OrderItem.objects.create(
            product=item["product"],
            order=order,
            quantity=item["quantity"],
        )

    # Create shipping address
    shipping_data = request.data.get("shippingAddress", {})
    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        full_name=shipping_data.get("full_name", ""),
        phone=shipping_data.get("phone", ""),
        address=shipping_data.get("line1", ""),
        city=shipping_data.get("city", ""),
        state=shipping_data.get("state", ""),
        zipcode=shipping_data.get("zipcode", ""),
        country=shipping_data.get("country", "UAE"),
    )

    data = {
        "id": order.id,
        "userId": request.user.uid,
        "items": [
            {
                "productId": str(item["product"].id),
                "name": item["product"].name,
                "quantity": item["quantity"],
                "price": item["price"],
                "subtotal": item["subtotal"],
            } for item in validated_items
        ],
        "totalAmount": round(total_amount, 2),
        "status": order.status,
        "shippingAddress": shipping_data,
        "paymentIntentId": "",
        "createdAt": order.date_ordered.isoformat(),
    }

    # Send notification
    try:
        if order.status == 'Paid' or order.status == 'Pending':
            send_order_notification(order, type="confirmation")
    except Exception as e:
        print(f"API Order Notification Error: {e}")

    return Response(data, status=status.HTTP_201_CREATED)


# ── GET /api/orders/ ─────────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_orders(request):
    if request.user.is_admin:
        orders_qs = Order.objects.all()
    else:
        try:
            user = User.objects.get(username=request.user.uid)
            customer = Customer.objects.get(user=user)
            orders_qs = Order.objects.filter(customer=customer)
        except (User.DoesNotExist, Customer.DoesNotExist):
            return Response([])

    orders_qs = orders_qs.order_by('-date_ordered')

    orders = []
    for order in orders_qs:
        items = []
        for oi in order.orderitem_set.all():
            items.append({
                "productId": str(oi.product.id),
                "name": oi.product.name,
                "quantity": oi.quantity,
                "price": oi.product.price,
                "subtotal": oi.get_total,
            })
        shipping = order.shippingaddress_set.first()
        shipping_data = {
            "full_name": shipping.full_name if shipping else "",
            "phone": shipping.phone if shipping else "",
            "line1": shipping.address if shipping else "",
            "city": shipping.city if shipping else "",
            "state": shipping.state if shipping else "",
            "zipcode": shipping.zipcode if shipping else "",
            "country": shipping.country if shipping else "",
        }
        data = {
            "id": order.id,
            "userId": request.user.uid,
            "items": items,
            "totalAmount": order.get_cart_total,
            "status": order.status,
            "shippingAddress": shipping_data,
            "paymentIntentId": order.transaction_id,
            "createdAt": order.date_ordered.isoformat(),
        }
        orders.append(data)

    return Response(orders)


# ── GET /api/orders/<id>/ ────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=404)

    if not request.user.is_admin:
        try:
            user = User.objects.get(username=request.user.uid)
            customer = Customer.objects.get(user=user)
            if order.customer != customer:
                return Response({"error": "Forbidden."}, status=403)
        except (User.DoesNotExist, Customer.DoesNotExist):
            return Response({"error": "Forbidden."}, status=403)

    items = []
    for oi in order.orderitem_set.all():
        items.append({
            "productId": str(oi.product.id),
            "name": oi.product.name,
            "quantity": oi.quantity,
            "price": oi.product.price,
            "subtotal": oi.get_total,
        })
    shipping = order.shippingaddress_set.first()
    shipping_data = {
        "full_name": shipping.full_name if shipping else "",
        "phone": shipping.phone if shipping else "",
        "line1": shipping.address if shipping else "",
        "city": shipping.city if shipping else "",
        "state": shipping.state if shipping else "",
        "zipcode": shipping.zipcode if shipping else "",
        "country": shipping.country if shipping else "",
    }
    data = {
        "id": order.id,
        "userId": request.user.uid,
        "items": items,
        "totalAmount": order.get_cart_total,
        "status": order.status,
        "shippingAddress": shipping_data,
        "paymentIntentId": order.transaction_id,
        "createdAt": order.date_ordered.isoformat(),
    }
    return Response(data)


# ── PATCH /api/orders/<id>/status/ ───────────────────────────────────────────
@api_view(["PATCH"])
@permission_classes([IsFirebaseAdmin])
def update_order_status(request, order_id):
    new_status = request.data.get("status", "")
    if new_status not in VALID_STATUSES:
        return Response(
            {"error": f"Invalid status. Choose from: {', '.join(sorted(VALID_STATUSES))}"},
            status=400,
        )

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=404)

    order.status = new_status
    order.save()
    return Response({"message": f"Order '{order_id}' status → '{new_status}'."})
