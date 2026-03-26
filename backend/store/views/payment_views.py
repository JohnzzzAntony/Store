import json
import stripe
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from store.models import Order
from store.utils import cartData

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def tabby_payment(request):
    order_id = request.GET.get('order_id')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        transaction_id = request.POST.get('transaction_id', f'TABBY_{order_id}')
        try:
            order = Order.objects.get(id=order_id)
            order.complete = True
            order.transaction_id = transaction_id
            order.status = 'Confirmed - Tabby'
            order.save()
            return redirect(f'/order-success/?transaction_id={transaction_id}')
        except Order.DoesNotExist: return redirect('store')

    phone, email, total = "Guest", "", 0.0
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            total = order.get_cart_total
            shipping = order.shippingaddress_set.first()
            if shipping and shipping.phone: phone = shipping.phone
            if order.customer: email = order.customer.email
        except Order.DoesNotExist: return redirect('store')
            
    masked_phone = phone
    if len(phone) > 4: masked_phone = phone[:4] + "*" * (len(phone) - 8) + phone[-4:]
        
    context = {'total': total, 'installment': round(total / 4, 2), 'order_id': order_id, 'masked_phone': masked_phone, 'email': email}
    return render(request, 'store/tabby_payment.html', context)

@csrf_exempt
def tamara_payment(request):
    order_id = request.GET.get('order_id')
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        transaction_id = request.POST.get('transaction_id', f'TAMARA_{order_id}')
        try:
            order = Order.objects.get(id=order_id)
            order.complete = True
            order.transaction_id = transaction_id
            order.status = 'Confirmed - Tamara'
            order.save()
            return redirect(f'/order-success/?transaction_id={transaction_id}')
        except Order.DoesNotExist: return redirect('store')

    total, phone = 0.0, "Guest"
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            total = order.get_cart_total
            shipping = order.shippingaddress_set.first()
            if shipping and shipping.phone: phone = shipping.phone
        except Order.DoesNotExist: return redirect('store')
            
    masked_phone = phone
    if len(phone) > 4: masked_phone = phone[:4] + "*" * (len(phone) - 8) + phone[-4:]
            
    context = {'total': total, 'order_id': order_id, 'masked_phone': masked_phone}
    return render(request, 'store/tamara_payment.html', context)

def create_payment_intent(request):
    if request.method != 'POST': return JsonResponse({'error': 'Only POST requests allowed'}, status=405)
    try:
        if settings.STRIPE_SECRET_KEY == 'sk_test_placeholder' or not settings.STRIPE_SECRET_KEY:
            return JsonResponse({'clientSecret': 'pi_mock_secret_123456789_secret_placeholder', 'mock_mode': True})
        body_data = json.loads(request.body)
        data = cartData(request)
        total = data['order'].get_cart_total
        amount = int(total * 100)
        intent = stripe.PaymentIntent.create(
            amount=amount, currency='AED', automatic_payment_methods={'enabled': True},
            metadata={
                'customer_email': body_data['form'].get('email', ''),
                'shipping_name': body_data['shipping'].get('full_name', ''),
            }
        )
        return JsonResponse({'clientSecret': intent['client_secret']})
    except Exception as e: return JsonResponse({'error': str(e)}, status=403)

@csrf_exempt
def stripe_webhook(request):
    payload, sig_header = request.body, request.META.get('HTTP_STRIPE_SIGNATURE')
    try: event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except: return HttpResponse(status=400)
    if event['type'] == 'payment_intent.succeeded':
        print(f"PaymentIntent successful for {event['data']['object']['metadata'].get('customer_email')}")
    return HttpResponse(status=200)
