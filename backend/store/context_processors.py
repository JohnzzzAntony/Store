from .models import Store

def store_context(request):
    # Get store from middleware
    store = getattr(request, 'current_store', None)
    
    if not store:
        # Fallback for unexpected cases
        from .models import Store
        store = Store.objects.filter(is_active=True).first()
    
    # Pre-fetch media assets for the store
    media_assets = {}
    if store:
        # Cache this if possible for performance
        assets = store.media_assets.filter(is_active=True)
        for asset in assets:
            media_assets[asset.section_name] = asset

    # Determine if user is effectively a guest on the frontend
    is_guest = True
    if request.user.is_authenticated:
        from .models import Customer
        customer = Customer.objects.filter(user=request.user).first()
        is_staff = getattr(request.user, 'is_staff', False)
        # Only treat as NOT guest if they are not staff OR if they have a customer record
        if not is_staff or customer:
            is_guest = False

    return {
        'current_store': store,
        'media': media_assets,  # Access via {{ media.hero_bg.image.url }}
        'is_guest': is_guest,
    }
