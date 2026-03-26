import json
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
from store.models import Customer
from store.core.firebase_utils import verify_token, sync_user_to_firestore
from store.utils import cartData

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
                next_url = request.GET.get('next') or request.POST.get('next') or 'store'
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
                phone = request.POST.get('phone', '')
                user = User.objects.create_user(
                    username=username, email=email,
                    password=password1, first_name=first_name, last_name=last_name
                )
                Customer.objects.create(
                    store=getattr(request, 'current_store', None),
                    user=user,
                    name=f"{first_name} {last_name}".strip(),
                    email=email,
                    phone=phone
                )
                login(request, user)
                messages.success(request, 'Account created successfully!')
                next_url = request.GET.get('next') or request.POST.get('next') or 'store'
                return redirect(next_url)

    context = {'cartItems': cartItems}
    return render(request, 'store/login.html', context)


def logout_view(request, *args, **kwargs):
    """Logout."""
    logout(request)
    return redirect('store')
