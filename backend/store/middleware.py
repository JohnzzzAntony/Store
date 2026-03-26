from django.shortcuts import get_object_or_404
from .models import Store

class StoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Always default to the first active store for a single-store experience
        request.current_store = Store.objects.filter(is_active=True).first()

        response = self.get_response(request)
        return response
