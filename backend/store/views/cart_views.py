import json
import datetime
from django.http import JsonResponse
from django.contrib.auth.models import User
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from store.models import Product, Customer, Order, OrderItem, ShippingAddress
from store.utils import cartData, guestOrder
from store.core.notifications import send_order_notification
from store.core.firebase_utils import save_order_to_firestore
from store.core.payment_providers import payment_registry

def updateItem(request, *args, **kwargs):
    """AJAX endpoint to add/remove cart items."""
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    quantity = data.get('quantity', 1)

    if request.user.is_authenticated:
        store = getattr(request, 'current_store', None)
        customer, created = Customer.objects.get_or_create(user=request.user, defaults={'store': store})
        product = Product.objects.get(id=productId, store=store)
        order, created = Order.objects.get_or_create(customer=customer, store=store, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            orderItem.quantity = (orderItem.quantity + quantity)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)

        orderItem.save()
        if orderItem.quantity <= 0:
            orderItem.delete()

    return JsonResponse('Item was added', safe=False)

@api_view(['POST'])
def apply_coupon(request):
    data = json.loads(request.body)
    coupon_code = data.get('coupon', '').strip()
    
    # Identify the store
    store = getattr(request, 'current_store', None)
    
    # Search for an offer section or bogo offer with this code
    from store.models import OfferSection, BOGOOffer, Order
    
    offer = OfferSection.objects.filter(store=store, promo_code=coupon_code, is_active=True).first()
    if not offer:
        offer = BOGOOffer.objects.filter(store=store, promo_code=coupon_code, is_active=True).first()
        
    if not offer:
        return JsonResponse({'success': False, 'error': 'Invalid or expired coupon code.'})

    # Get the order
    from store.utils import cartData
    cart_data = cartData(request)
    order_data = cart_data['order']
    
    if request.user.is_authenticated:
        # Update the actual Django model
        order = order_data # In cartData, order is the model instance for auth users
        order.coupon = coupon_code
        
        # Calculate discount
        discount = 0.0
        if hasattr(offer, 'discount_value'):
            if offer.offer_type == 'percent':
                # Use order.get_cart_total (before discount)
                current_total = sum([item.get_total for item in order.orderitem_set.all()])
                discount = (offer.discount_value / 100) * current_total
            else:
                discount = offer.discount_value
        else:
            # BOGO logic might be more complex, for now let's assume a sample flat discount or a message
            discount = 10.0 # Placeholder
            
        order.discount = discount
        order.save()
        return JsonResponse({'success': True, 'discount': discount})
    else:
        # We don't have a way to persist discount in cookie order dict easily without updating cookieCart
        # For now, let's say it requires login or we could update the cookie.
        return JsonResponse({'success': False, 'error': 'Please login to apply coupons.'})

def processOrder(request, *args, **kwargs):
    """Process the order (billing + shipping info)."""
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    form_data = data.get('form', {})
    
    name = form_data.get('name')
    email = form_data.get('email')
    phone = form_data.get('phone')
    total = float(form_data.get('total', 0))
    payment_method = form_data.get('payment_method', 'cod')

    store = getattr(request, 'current_store', None)
    
    # Logic: Always use form name/email even if logged in
    if request.user.is_authenticated:
        customer, created = Customer.objects.get_or_create(user=request.user, defaults={'store': store})
        if name: customer.name = name
        if email: customer.email = email
        if phone: customer.phone = phone
        customer.save()
        
        # Check if they have an active DB order
        order, created = Order.objects.get_or_create(customer=customer, store=store, complete=False)
        
        # SPECIAL CASE: If they are staff/admin browsing as guest, they might have items in COOKIE
        # but the DB order might be empty.
        if order.get_cart_items == 0:
            cookie_data = cookieCart(request)
            for item in cookie_data['items']:
                product = Product.objects.get(id=item['id'])
                OrderItem.objects.create(
                    product=product,
                    order=order,
                    quantity=int(item['quantity'])
                )
    else:
        customer, order = guestOrder(request, data)

    order.transaction_id = transaction_id
    order.payment_method = payment_method
    
    if payment_method == 'cod':
        order.complete = True
        order.status = 'Confirmed - COD'
    elif payment_method in ['tabby', 'tamara']:
        order.complete = False
        order.status = 'Payment Pending'
    else:
        order.complete = abs(total - order.get_cart_total) < 0.01
        order.status = 'Processing'
    
    order.save()

    provider = payment_registry.get_provider(payment_method)
    payment_result = {}
    if provider:
        payment_result = provider.process(order, data)
        redirect_url = payment_result.get('redirect_url')
        
        if payment_method in ['tabby', 'tamara'] and redirect_url:
            full_redirect_url = request.build_absolute_uri(redirect_url)
            try:
                subject = f"Complete your {payment_method.capitalize()} Payment - Order #{order.id}"
                message = f"Hello,\n\nPlease click the link below to complete your payment:\n{full_redirect_url}"
                recipient = data['form'].get('email') or (customer.email if customer else None)
                if recipient:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
            except Exception as e:
                print(f"Mail Error: {e}")

    if order.shipping:
        ShippingAddress.objects.update_or_create(
            order=order,
            defaults={
                'customer': customer,
                'full_name': data['shipping'].get('full_name', ''),
                'phone': data['shipping'].get('phone', ''),
                'address': data['shipping'].get('address', ''),
                'city': data['shipping'].get('city', ''),
                'state': data['shipping'].get('state', ''),
                'zipcode': data['shipping'].get('zipcode', ''),
                'country': data['shipping'].get('country', 'UAE'),
            }
        )

    save_order_to_firestore({
        'transaction_id': str(transaction_id),
        'store_id': store.id if store else None,
        'order_id': order.id,
        'customer_email': data['form'].get('email', (customer.email if customer else "Guest")),
        'total': total,
        'payment_method': payment_method,
        'status': order.status,
        'timestamp': datetime.datetime.now().isoformat()
    })

    success_redirect_url = f"/order-success/?transaction_id={transaction_id}"
    
    if provider and payment_result.get('status') == 'redirect':
        emi_redirect = payment_result.get('redirect_url', f'/payment/{payment_method}/')
        final_redirect = emi_redirect
        if '?' not in final_redirect: final_redirect += f"?order_id={order.id}"
        if 'total' not in final_redirect: final_redirect += f"&total={total}"
            
        try: send_order_notification(order, type="confirmation")
        except: pass

        return JsonResponse({'status': 'success', 'redirect_url': final_redirect, 'order_id': order.id})
    
    try:
        if order.complete or payment_method == 'cod':
            send_order_notification(order, type="confirmation")
    except: pass

    return JsonResponse({'status': 'success', 'redirect_url': success_redirect_url, 'order_id': order.id})
