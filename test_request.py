import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()
from store.views import product_list
import unittest.mock as mock

def test():
    req = mock.Mock()
    req.GET = {'category': 'perfume'}
    req.user.is_authenticated = False
    req.COOKIES = {}
    
    try:
        product_list(req)
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
