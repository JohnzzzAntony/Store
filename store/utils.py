import json
from .models import Product, Customer, Order, OrderItem

def cookieCart(request):
	# Create empty cart for now for non-logged in user
	try:
		cart_cookie = request.COOKIES.get('cart', '{}')
		cart = json.loads(cart_cookie)
	except (ValueError, KeyError, TypeError):
		cart = {}
		print('CART error reading cookie:', cart)

	items = []
	order = {'get_cart_total': 0.0, 'get_cart_items': 0, 'shipping': False}
	cartItems = 0

	for i in cart:
		# We use try block to prevent items in cart that may have been removed from causing error
		try:
			# Extra safety for IDE analyzer
			item_data = cart.get(i)
			if isinstance(item_data, dict) and int(item_data.get('quantity', 0)) > 0:
				quantity = int(item_data['quantity'])
				cartItems += quantity

				product = Product.objects.get(id=i)
				total = (product.price * quantity)

				order['get_cart_total'] += total
				order['get_cart_items'] += quantity

				# Task 2: Remove zero-priced fragrance items
				if product.price == 0 and 'fragrance' in product.name.lower():
					continue

				item = {
					'id': product.id,
					'product': {
						'id': product.id,
						'name': product.name, 
						'price': product.price, 
						'imageURL': product.imageURL
					}, 
					'quantity': quantity,
					'digital': product.digital,
					'get_total': total,
				}
				items.append(item)

				if product.digital == False:
					order['shipping'] = True
		except Exception as e:
			print(f"Error processing item {i}: {e}")
			
	return {'cartItems': int(cartItems), 'order': order, 'items': items}


def cartData(request):
	store = getattr(request, 'current_store', None)
	if request.user.is_authenticated:
		customer, created = Customer.objects.get_or_create(user=request.user, defaults={'store': store})
		if created:
			customer.name = request.user.username
			customer.email = request.user.email
			customer.save()
		order = Order.objects.filter(customer=customer, store=store, complete=False).first()
		if not order:
			# Return a dummy context object instead of a database record
			order = {
				'get_cart_total': 0.0, 
				'get_cart_items': 0, 
				'shipping': False,
				'id': None
			}
			items = []
		else:
			# Existing order logic
			items = order.orderitem_set.all()
			filtered_items = []
			for item in items:
				if item.product and item.product.price == 0 and 'fragrance' in item.product.name.lower():
					continue
				filtered_items.append(item)
			
			items = filtered_items
			cartItems = sum([item.quantity for item in items])
	else:
		cookieData = cookieCart(request)
		cartItems = cookieData['cartItems']
		order = cookieData['order']
		items = cookieData['items']

	return {'cartItems':cartItems ,'order':order, 'items':items}

	
def guestOrder(request, data):
	name = data['form']['name']
	email = data['form']['email']
	store = getattr(request, 'current_store', None)

	cookieData = cookieCart(request)
	items = cookieData['items']

	customer, created = Customer.objects.get_or_create(
			email=email,
			defaults={'store': store, 'name': name}
			)
	if not created:
		customer.name = name
		customer.save()

	order = Order.objects.create(
		customer=customer,
		store=store,
		complete=False,
		)

	for item in items:
		if not isinstance(item, dict):
			continue
		
		product_id = item.get('id')
		if not product_id:
			continue

		product = Product.objects.get(id=product_id)
		quantity = int(item.get('quantity', 1))
		
		orderItem = OrderItem.objects.create(
			product=product,
			order=order,
			quantity=(quantity if quantity > 0 else -1 * quantity), # negative quantity = freebies
		)
	return customer, order


