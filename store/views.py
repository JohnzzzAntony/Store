from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import json
import datetime
from .models import *
from .utils import cookieCart, cartData, guestOrder


def store(request):
    """Home page with hero carousel and featured products."""
    data = cartData(request)
    cartItems = data['cartItems']

    featured_products = Product.objects.filter(is_featured=True, in_stock=True)[:6]
    all_products = Product.objects.filter(in_stock=True)[:8]
    latest_blogs = BlogPost.objects.all().order_by('-published_at')[:3]

    context = {
        'featured_products': featured_products,
        'all_products': all_products,
        'latest_blogs': latest_blogs,
        'cartItems': cartItems,
    }
    return render(request, 'store/store.html', context)


def product_list(request):
    """Product listing page with gender/scent/price filters."""
    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.filter(in_stock=True)
    categories = Category.objects.all()

    # Apply filters
    gender = request.GET.get('gender', '')
    scent = request.GET.get('scent', '')
    price_max = request.GET.get('price_max', '')
    sort_by = request.GET.get('sort', '')

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


def product_detail(request, pk):
    """Product detail page with images, description, size, add to cart."""
    data = cartData(request)
    cartItems = data['cartItems']

    product = get_object_or_404(Product, pk=pk)
    related_products = Product.objects.filter(
        category=product.category, in_stock=True
    ).exclude(pk=pk)[:4]

    context = {
        'product': product,
        'related_products': related_products,
        'cartItems': cartItems,
    }
    return render(request, 'store/product_detail.html', context)


def about(request):
    """About Us page."""
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/about.html', context)


def terms(request):
    """Terms and Conditions page."""
    data = cartData(request)
    cartItems = data['cartItems']
    context = {'cartItems': cartItems}
    return render(request, 'store/terms.html', context)


def blog_list(request):
    """Blog listing page."""
    data = cartData(request)
    cartItems = data['cartItems']
    blogs = BlogPost.objects.all().order_by('-published_at')
    context = {'blogs': blogs, 'cartItems': cartItems}
    return render(request, 'store/blog_list.html', context)


def blog_detail(request, slug):
    """Individual blog post."""
    data = cartData(request)
    cartItems = data['cartItems']
    blog = get_object_or_404(BlogPost, slug=slug)
    related = BlogPost.objects.exclude(slug=slug).order_by('-published_at')[:3]
    context = {'blog': blog, 'related': related, 'cartItems': cartItems}
    return render(request, 'store/blog_detail.html', context)


def contact(request):
    """Contact Us page with form."""
    data = cartData(request)
    cartItems = data['cartItems']

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        if name and email and message:
            ContactMessage.objects.create(name=name, email=email, message=message)
            messages.success(request, 'Your message has been sent successfully!')
        else:
            messages.error(request, 'Please fill in all fields.')
        return redirect('contact')

    context = {'cartItems': cartItems}
    return render(request, 'store/contact.html', context)


def cart(request):
    """Cart page."""
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    """Billing address / checkout page."""
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def login_view(request):
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
                    user=user,
                    name=f"{first_name} {last_name}".strip(),
                    email=email
                )
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('store')

    context = {'cartItems': cartItems}
    return render(request, 'store/login.html', context)


def logout_view(request):
    """Logout."""
    logout(request)
    return redirect('store')


def updateItem(request):
    """AJAX endpoint to add/remove cart items."""
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']

    if request.user.is_authenticated:
        customer = request.user.customer
        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)

        orderItem.save()

        if orderItem.quantity <= 0:
            orderItem.delete()

    return JsonResponse('Item was updated', safe=False)


def processOrder(request):
    """Process the order (billing + shipping info)."""
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    payment_method = data['form'].get('payment_method', 'cod')
    order.transaction_id = transaction_id
    order.payment_method = payment_method

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            full_name=data['shipping'].get('full_name', ''),
            phone=data['shipping'].get('phone', ''),
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)