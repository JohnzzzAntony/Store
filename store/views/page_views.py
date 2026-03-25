from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import HttpRequest
import datetime
from store.models import (Product, Customer, Order, OrderItem, ShippingAddress, Category, Brand,
                         BlogPost, ContactMessage, PromoBanner, OfferSection, CategoryOffer, BOGOOffer, FrontendMedia)
from store.utils import cartData
from django.conf import settings

def store(request, *args, **kwargs):
    """Home page with hero carousel, banners, offers, and featured products."""
    data = cartData(request)
    cartItems = data['cartItems']
    store_obj = getattr(request, 'current_store', None)

    now = datetime.datetime.now()

    featured_products = Product.objects.filter(store=store_obj, is_featured=True, in_stock=True)[:6]
    all_products = Product.objects.filter(store=store_obj, in_stock=True)[:8]
    latest_blogs = BlogPost.objects.filter(store=store_obj).order_by('-published_at')[:3]
    categories = Category.objects.filter(store=store_obj)[:3]

    promo_banners = PromoBanner.objects.filter(store=store_obj, is_active=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
    offer_sections = OfferSection.objects.filter(store=store_obj, is_active=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))
    category_offers = CategoryOffer.objects.filter(store=store_obj, is_active=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now)).select_related('category')
    bogo_offers = BOGOOffer.objects.filter(store=store_obj, is_active=True).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now))

    media_assets = FrontendMedia.objects.filter(store=store_obj, is_active=True)
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
    store_obj = getattr(request, 'current_store', None)

    products = Product.objects.filter(store=store_obj, in_stock=True)
    categories = Category.objects.filter(store=store_obj)

    category_slug = request.GET.get('category', '')
    gender = request.GET.get('gender', '')
    scent = request.GET.get('scent', '')
    price_max = request.GET.get('price_max', '')
    sort_by = request.GET.get('sort', '')

    if category_slug: products = products.filter(category__slug=category_slug)
    if gender: products = products.filter(gender=gender)
    if scent: products = products.filter(scent_profile=scent)
    
    brand_slug = request.GET.get('brand', '')
    if brand_slug: products = products.filter(brand__slug=brand_slug)
    
    # Task 6: BOGO filtering
    bogo_id = request.GET.get('bogo', '')
    if bogo_id:
        try:
            bogo = BOGOOffer.objects.get(id=bogo_id)
            if bogo.applicable_products.exists():
                products = products.filter(id__in=bogo.applicable_products.all())
            elif bogo.applicable_categories.exists():
                products = products.filter(category__in=bogo.applicable_categories.all())
        except BOGOOffer.DoesNotExist:
            pass

    if price_max:
        try: products = products.filter(price__lte=float(price_max))
        except ValueError: pass

    if sort_by == 'price_asc': products = products.order_by('price')
    elif sort_by == 'price_desc': products = products.order_by('-price')
    elif sort_by == 'name': products = products.order_by('name')
    else: products = products.order_by('-created_at')

    context = {
        'products': products,
        'categories': categories,
        'cartItems': cartItems,
        'selected_gender': gender,
        'selected_scent': scent,
        'selected_price_max': price_max,
        'selected_sort': sort_by,
        'selected_brand': brand_slug,
        'brands': Brand.objects.filter(store=store_obj),
        'scent_choices': Product.SCENT_CHOICES,
    }
    return render(request, 'store/product_list.html', context)

def product_detail(request, pk, *args, **kwargs):
    data = cartData(request)
    cartItems = data['cartItems']
    product = get_object_or_404(Product, pk=pk, store=getattr(request, 'current_store', None))
    related_products = Product.objects.filter(store=product.store, category=product.category, in_stock=True).exclude(pk=pk)[:4]
    context = {'product': product, 'related_products': related_products, 'cartItems': cartItems}
    return render(request, 'store/product_detail.html', context)

def about(request, *args, **kwargs):
    data = cartData(request)
    return render(request, 'store/about.html', {'cartItems': data['cartItems']})

def brand_list(request):
    data = cartData(request)
    store_obj = getattr(request, 'current_store', None)
    brands = Brand.objects.filter(store=store_obj).order_by('name') if store_obj else Brand.objects.all().order_by('name')
    return render(request, 'store/brand_list.html', {'brands': brands, 'cartItems': data['cartItems']})

def brand_detail(request, slug):
    data = cartData(request)
    store_obj = getattr(request, 'current_store', None)
    brand = get_object_or_404(Brand, slug=slug, store=store_obj)
    
    products = Product.objects.filter(brand=brand, in_stock=True)
    categories = Category.objects.filter(store=store_obj)
    
    context = {
        'brand': brand,
        'products': products,
        'categories': categories,
        'brands': Brand.objects.filter(store=store_obj),
        'cartItems': data['cartItems'],
        'scent_choices': Product.SCENT_CHOICES,
        'selected_brand': brand.slug,
    }
    return render(request, 'store/product_list.html', context)

def terms(request, *args, **kwargs):
    data = cartData(request)
    return render(request, 'store/terms.html', {'cartItems': data['cartItems']})

def blog_list(request, *args, **kwargs):
    data = cartData(request)
    store_obj = getattr(request, 'current_store', None)
    blogs = BlogPost.objects.filter(store=store_obj).order_by('-published_at')
    return render(request, 'store/blog_list.html', {'blogs': blogs, 'cartItems': data['cartItems']})

def blog_detail(request, slug, *args, **kwargs):
    data = cartData(request)
    store_obj = getattr(request, 'current_store', None)
    blog = get_object_or_404(BlogPost, slug=slug, store=store_obj)
    related = BlogPost.objects.filter(store=store_obj).exclude(slug=slug).order_by('-published_at')[:3]
    return render(request, 'store/blog_detail.html', {'blog': blog, 'related': related, 'cartItems': data['cartItems']})

def contact(request, *args, **kwargs):
    data = cartData(request)
    if request.method == 'POST':
        name, email = request.POST.get('name', ''), request.POST.get('email', '')
        message = request.POST.get('message', '')
        if name and email and message:
            ContactMessage.objects.create(store=getattr(request, 'current_store', None), name=name, email=email, message=message)
            from django.contrib import messages
            messages.success(request, 'Your message has been sent!')
        return redirect('contact')
    return render(request, 'store/contact.html', {'cartItems': data['cartItems']})

def cart(request, *args, **kwargs):
    data = cartData(request)
    return render(request, 'store/cart.html', {'items': data['items'], 'order': data['order'], 'cartItems': data['cartItems']})

def checkout(request, *args, **kwargs):
    data = cartData(request)
    context = {'items': data['items'], 'order': data['order'], 'cartItems': data['cartItems'], 'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY}
    return render(request, 'store/checkout.html', context)

def order_success(request):
    transaction_id = request.GET.get('transaction_id')
    order, items = None, []
    if transaction_id:
        try:
            order = Order.objects.get(transaction_id=transaction_id)
            items = order.orderitem_set.all()
        except Order.DoesNotExist: pass
    categories = Category.objects.all()[:3]
    return render(request, 'store/order_success.html', {'order': order, 'items': items, 'categories': categories})

def get_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/invoice.html', {
        'order': order, 'items': order.orderitem_set.all(), 
        'shipping': order.shippingaddress_set.first(), 'total': order.get_cart_total,
        'date': order.date_ordered.strftime('%b %d, %Y')
    })
