from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpRequest
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
import json
import datetime
from .models import (Product, Customer, Order, OrderItem, ShippingAddress, Category,
                     BlogPost, ContactMessage, PromoBanner, OfferSection, CategoryOffer, BOGOOffer, FrontendMedia)
from .utils import cookieCart, cartData, guestOrder
from .firebase_utils import verify_token, sync_user_to_firestore, save_order_to_firestore
from .payment_providers import payment_registry
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string

stripe.api_key = settings.STRIPE_SECRET_KEY


def firebase_login_sync(request, *args, **kwargs):
    """Verifies Firebase token and logs user into Django."""
    data = json.loads(request.body)
    id_token = data.get('id_token')
    
    decoded_token = verify_token(id_token)
    if decoded_token:
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')

        # Get or create Django user
        user, created = User.objects.get_or_create(username=uid, defaults={'email': email})
        if created:
            user.set_unusable_password()
            user.save()
            
        Customer.objects.get_or_create(user=user, defaults={'name': name, 'email': email})
        
        login(request, user)
        sync_user_to_firestore(decoded_token)
        return JsonResponse({'status': 'success', 'user': email})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid token'}, status=400)


def store(request, *args, **kwargs):
    """Home page with hero carousel, banners, offers, and featured products."""
    data = cartData(request)
    cartItems = data['cartItems']
    store = getattr(request, 'current_store', None)

    now = datetime.datetime.now()

    featured_products = Product.objects.filter(store=store, is_featured=True, in_stock=True)[:6]
    all_products = Product.objects.filter(store=store, in_stock=True)[:8]
    latest_blogs = BlogPost.objects.filter(store=store).order_by('-published_at')[:3]
    categories = Category.objects.filter(store=store)[:3]

    # Promotional content — only active, not yet expired
    promo_banners = PromoBanner.objects.filter(
        store=store, is_active=True
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )

    offer_sections = OfferSection.objects.filter(
        store=store, is_active=True
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )

    category_offers = CategoryOffer.objects.filter(
        store=store, is_active=True
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    ).select_related('category')

    bogo_offers = BOGOOffer.objects.filter(
        store=store, is_active=True
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gt=now)
    )

    # Frontend Media
    media_assets = FrontendMedia.objects.filter(store=store, is_active=True)
    media = {asset.section_name: asset for asset in media_assets}

    context = {
        'featured_products': featured_products,
        'all_products': all_products,
        'latest_blogs': latest_blogs,
        'categories': categories,
        'cartItems': cartItems,
        'promo_banners': promo_banners,
        'offer_sections': offer_sections,
        'category_offers': category_offers,
        'bogo_offers': bogo_offers,
        'media': media,
    }
    return render(request, 'store/store.html', context)



def product_list(request: HttpRequest, *args, **kwargs):
    """Product listing page with gender/scent/price filters."""
    data = cartData(request)
    cartItems = data['cartItems']
    store = getattr(request, 'current_store', None)

    products = Product.objects.filter(store=store, in_stock=True)
    categories = Category.objects.filter(store=store)

    # Apply filters
    category_slug = request.GET.get('category', '')
    gender = request.GET.get('gender', '')
    scent = request.GET.get('scent', '')
    price_max = request.GET.get('price_max', '')
    sort_by = request.GET.get('sort', '')

    if category_slug:
        products = products.filter(category__slug=category_slug)
    if gender:
        products = products.filter(gender=gender)
    if scent:
        products = products.filter(scent_profile=scent)
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    else:
        products = products.order_by('-created_at')

    context = {
        'products': products,
        'categories': categories,
        'cartItems': cartItems,
        'selected_gender': gender,
        'selected_scent': scent,
        'selected_price_max': price_max,
        'selected_sort': sort_by,
        'scent_choices': Product.SCENT_CHOICES,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, pk, *args, **kwargs):
    """Product detail page with images, description, size, add to cart."""
    data = cartData(request)
    cartItems = data['cartItems']

    product = get_object_or_404(Product, pk=pk, store=getattr(request, 'current_store', None))
    related_products = Product.objects.filter(
        store=product.store, category=product.category, in_stock=True
    ).exclude(pk=pk)[:4]

    context = {
        'product': product,
        'related_products': related_products,
        'cartItems': cartItems,
    }
    return render(request, 'store/product_detail.html', context)


def about(request, *args, **kwargs):
    """About Us page."""
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/about.html', context)


def terms(request, *args, **kwargs):
    """Terms and Conditions page."""
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/terms.html', context)


def blog_list(request, *args, **kwargs):
    """Blog listing page."""
    data = cartData(request)
    cartItems = data['cartItems']
    store = getattr(request, 'current_store', None)
    blogs = BlogPost.objects.filter(store=store).order_by('-published_at')
    context = {'blogs': blogs, 'cartItems': cartItems}
    return render(request, 'store/blog_list.html', context)


def blog_detail(request, slug, *args, **kwargs):
    """Individual blog post."""
    data = cartData(request)
    cartItems = data['cartItems']
    store = getattr(request, 'current_store', None)
    blog = get_object_or_404(BlogPost, slug=slug, store=store)
    related = BlogPost.objects.filter(store=store).exclude(slug=slug).order_by('-published_at')[:3]
    context = {'blog': blog, 'related': related, 'cartItems': cartItems}
    return render(request, 'store/blog_detail.html', context)


def contact(request, *args, **kwargs):
    """Contact Us page with form."""
    data = cartData(request)
    cartItems = data['cartItems']

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        store = getattr(request, 'current_store', None)
        if name and email and message:
            ContactMessage.objects.create(store=store, name=name, email=email, message=message)
            messages.success(request, 'Your message has been sent successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')
        return redirect('contact')

    context = {'cartItems': cartItems}
    return render(request, 'store/contact.html', context)


def cart(request, *args, **kwargs):
    """Cart page."""
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


@login_required(login_url='login')
def checkout(request, *args, **kwargs):
    """Billing address / checkout page."""
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']
    
    context = {
        'items': items,
        'order': order,
        'cartItems': cartItems,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    }
    return render(request, 'store/checkout.html', context)


def login_view(request, *args, **kwargs):
    """Login / Register page."""
    data = cartData(request)
    cartItems = data['cartItems']

    if request.user.is_authenticated:
        return redirect('store')

    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'login':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'store')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')

        elif action == 'register':
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            username = request.POST.get('reg_username', '')
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')

            if password1 != password2:
                messages.error(request, 'Passwords do not match.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
            else:
                user = User.objects.create_user(
                    username=username, email=email,
                    password=password1, first_name=first_name, last_name=last_name
                )
                Customer.objects.create(
                    store=getattr(request, 'current_store', None),
                    user=user,
                    name=f"{first_name} {last_name}".strip(),
                    email=email
                )
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('store')

    context = {'cartItems': cartItems}
    return render(request, 'store/login.html', context)


from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def dashboard(request, *args, **kwargs):
    """Real-time Firebase Dashboard."""
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/dashboard.html', context)


def logout_view(request, *args, **kwargs):
    """Logout."""
    logout(request)
    return redirect('store')


def updateItem(request, *args, **kwargs):
    """AJAX endpoint to add/remove cart items."""
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    quantity = data.get('quantity', 1)

    print('Action:', action)
    print('Product:', productId)
    print('Quantity:', quantity)

    if request.user.is_authenticated:
        customer = request.user.customer
        store = getattr(request, 'current_store', None)
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

    return JsonResponse('Item was updated', safe=False)


@login_required
def clear_products(request):
    """Secret/Admin view to clear all products for re-import"""
    count = Product.objects.all().count()
    Product.objects.all().delete()
    from django.contrib import messages
    messages.success(request, f"Successfully deleted {count} products.")
    return redirect('admin:store_product_changelist')


def tabby_payment(request):
    """Mock Tabby Payment Page"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            total = order.get_cart_total
        except Order.DoesNotExist:
            return redirect('store')
    else:
        data = cartData(request)
        order = data['order']
        if hasattr(order, 'get_cart_total'):
            total = order.get_cart_total
        else:
            total = order.get('get_cart_total', 0.0)
        
    context = {'total': total, 'installment': round(total / 4, 2)}
    return render(request, 'store/tabby_payment.html', context)


def tamara_payment(request):
    """Mock Tamara Payment Page"""
    order_id = request.GET.get('order_id')
    if order_id:
        try:
            order = Order.objects.get(id=order_id)
            total = order.get_cart_total
        except Order.DoesNotExist:
            return redirect('store')
    else:
        data = cartData(request)
        order = data['order']
        if hasattr(order, 'get_cart_total'):
            total = order.get_cart_total
        else:
            total = order.get('get_cart_total', 0.0)
        
    context = {'total': total}
    return render(request, 'store/tamara_payment.html', context)


def create_payment_intent(request):
    """Creates a Stripe PaymentIntent and returns the client secret."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed'}, status=405)

    try:
        if settings.STRIPE_SECRET_KEY == 'sk_test_placeholder' or not settings.STRIPE_SECRET_KEY:
            # Return a simulated client secret for the frontend to progress in "demo mode"
            return JsonResponse({
                'clientSecret': 'pi_mock_secret_123456789_secret_placeholder',
                'mock_mode': True 
            })

        body_data = json.loads(request.body)
        data = cartData(request)
        total = data['order'].get_cart_total
        
        # Stripe expects amount in cents
        amount = int(total * 100)

        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='AED',
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'customer_email': body_data['form'].get('email', ''),
                'total': total,
                'shipping_name': body_data['shipping'].get('full_name', ''),
                'shipping_address': f"{body_data['shipping'].get('address', '')}, {body_data['shipping'].get('city', '')}",
            }
        )
        return JsonResponse({
            'clientSecret': intent['client_secret']
        })
    except Exception as e:
        print(f"Stripe Error: {e}")
        return JsonResponse({'error': str(e)}, status=403)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        customer_email = intent['metadata'].get('customer_email')
        
        # Here you would typically match the order and mark it as fulfilled.
        # Since we are using finalizeOrder on the frontend, this serves as a backup.
        # If we had stored an order_id, we could do:
        # order_id = intent['metadata'].get('order_id')
        # order = Order.objects.get(id=order_id)
        # order.complete = True
        # order.save()
        
        print(f"PaymentIntent was successful for {customer_email}")

    return HttpResponse(status=200)


from .firebase_utils import save_order_to_firestore
from .payment_providers import payment_registry

def processOrder(request, *args, **kwargs):
    """Process the order (billing + shipping info)."""
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    store = getattr(request, 'current_store', None)
    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, store=store, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    payment_method = data['form'].get('payment_method', 'cod')
    order.transaction_id = transaction_id
    order.payment_method = payment_method
    order.status = 'Payment Pending' if payment_method in ['tabby', 'tamara'] else 'Processing'

    if total == order.get_cart_total:
        order.complete = True if payment_method == 'cod' else False
    order.save()

    # Process via payment provider registry
    provider = payment_registry.get_provider(payment_method)
    payment_result = {}
    if provider:
        payment_result = provider.process(order, data)
        redirect_url = payment_result.get('redirect_url')
        
        # SEND EMAIL LINK if Tabby/Tamara
        if payment_method in ['tabby', 'tamara'] and redirect_url:
            full_redirect_url = request.build_absolute_url(redirect_url)
            try:
                subject = f"Complete your {payment_method.capitalize()} Payment - Order #{order.id}"
                message = f"Hello,\n\nPlease click the link below to complete your payment using {payment_method.capitalize()}:\n{full_redirect_url}\n\nThank you for shopping with Saleel."
                recipient = data['form'].get('email') or (customer.email if customer else None)
                if recipient:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
                    print(f"DEBUG: Sent payment link to {recipient}: {full_redirect_url}")
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

    # Sync to Firebase for real-time tracking
    save_order_to_firestore({
        'transaction_id': str(transaction_id),
        'store_id': store.id if store else None,
        'store_name': store.name if store else "Unknown",
        'order_id': order.id,
        'customer_email': data['form'].get('email', (customer.email if customer else "Guest")),
        'total': total,
        'payment_method': payment_method,
        'status': order.status,
        'timestamp': datetime.datetime.now().isoformat()
    })

    # Return the payment result back to the frontend for handling redirects/success
    success_redirect_url = f"/order-success/?transaction_id={transaction_id}"
    
    if provider and payment_result.get('status') == 'redirect':
        return JsonResponse(payment_result)
    
    return JsonResponse({'status': 'success', 'redirect_url': success_redirect_url})

def order_success(request):
    """Page shown after successful order placement"""
    transaction_id = request.GET.get('transaction_id')
    order = None
    items = []
    
    if transaction_id:
        try:
            order = Order.objects.get(transaction_id=transaction_id)
            items = order.orderitem_set.all()
        except Order.DoesNotExist:
            pass
            
    # Recommendations (categories or featured)
    categories = Category.objects.all()[:3]
    
    context = {
        'order': order,
        'items': items,
        'categories': categories,
    }
    return render(request, 'store/order_success.html', context)