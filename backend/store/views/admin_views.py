from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from store.models import Product, Customer, Order, Category
from store.utils import cartData

@staff_member_required
def dashboard(request, *args, **kwargs):
    """Real-time Firebase Dashboard."""
    data = cartData(request)
    return render(request, 'store/dashboard.html', {'cartItems': data['cartItems']})

@staff_member_required
def clear_products(request):
    """Secret view to clear all products."""
    count = Product.objects.all().count()
    Product.objects.all().delete()
    messages.success(request, f"Successfully deleted {count} products.")
    return redirect('admin:store_product_changelist')

def admin_dashboard_stats(request):
    """Stats for Obsidian Admin Dashboard."""
    if not request.user.is_staff: return JsonResponse({'error': 'Unauthorized'}, status=403)
    completed_orders = Order.objects.filter(complete=True)
    total_sales = sum([order.get_cart_total for order in completed_orders])
    order_count, customer_count = completed_orders.count(), Customer.objects.count()
    
    today = timezone.now().date()
    labels, sales_values = [], []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        day_orders = completed_orders.filter(date_ordered__date=date)
        day_total = sum([o.get_cart_total for o in day_orders])
        labels.append(date.strftime('%b %d'))
        sales_values.append(float(day_total))

    categories = Category.objects.all()
    inv_labels = [c.name for c in categories]
    inv_data = [Product.objects.filter(category=c).count() for c in categories]

    activity = []
    for o in completed_orders.order_by('-date_ordered')[:5]:
        activity.append({
            'title': f"Order #{o.id} Verified",
            'desc': f"Amount: AED {o.get_cart_total} | Identity: {o.customer.name if o.customer else 'Guest'}",
            'time': o.date_ordered.strftime('%H:%M')
        })

    return JsonResponse({
        'total_sales': f"{total_sales:,.2f}",
        'order_count': f"{order_count}",
        'customer_count': f"{customer_count}",
        'chart_labels': labels,
        'chart_data': sales_values,
        'inv_labels': inv_labels,
        'inv_data': inv_data,
        'activity': activity
    })
