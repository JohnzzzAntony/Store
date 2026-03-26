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

    return {
        'current_store': store,
        'media': media_assets,  # Access via {{ media.hero_bg.image.url }}
    }
