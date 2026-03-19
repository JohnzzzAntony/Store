from django.shortcuts import get_object_or_404
from .models import Store

class StoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Identify store from path: /s/store-slug/...
        path_parts = request.path.strip('/').split('/')
        store = None
        
        if len(path_parts) >= 2 and path_parts[0] == 's':
            store_slug = path_parts[1]
            try:
                store = Store.objects.get(slug=store_slug, is_active=True)
                request.current_store = store
            except Store.DoesNotExist:
                request.current_store = None
        else:
            # Check if we should default to a specific store for the root domain
            # or keep it as None (global view)
            request.current_store = Store.objects.filter(is_active=True).first()

        response = self.get_response(request)
        return response
