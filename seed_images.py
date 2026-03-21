import os
import django
import shutil
import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import (Category, Product, Store, FrontendMedia, 
                          OfferSection, PromoBanner, CategoryOffer, BOGOOffer)
from django.conf import settings

def seed():
    # Associate first store found or dummy if none
    store = Store.objects.filter(is_active=True).first()
    if not store:
        store = Store.objects.create(name="Luxury Perfumes", slug="luxury-perfumes", is_active=True)
        print("Created new default store.")

    # 1. Update Existing Products if they have no store
    orphan_products = Product.objects.filter(store__isnull=True)
    if orphan_products.exists():
        orphan_products.update(store=store)
        print(f"Assigned store to {orphan_products.count()} orphan products.")

    # 2. Ensure at least some products are featured
    featured_count = Product.objects.filter(store=store, is_featured=True).count()
    if featured_count < 3:
        to_feature = Product.objects.filter(store=store, is_featured=False)[:3]
        for p in to_feature:
            p.is_featured = True
            p.save()
        print(f"Marked {to_feature.count()} products as featured.")

    # 3. Specifically create the products we need if not present
    products_data = [
        {'name': 'Royal Essence', 'price': 450, 'gender': 'W', 'image_path': 'products/her_luxury.png'},
        {'name': 'Imperial Forest', 'price': 520, 'gender': 'M', 'image_path': 'products/him_luxury.png'},
        {'name': 'Midnight Bloom', 'price': 480, 'gender': 'U', 'image_path': 'products/unisex_luxury.png'},
    ]
    
    for prod_info in products_data:
        prod, created = Product.objects.get_or_create(name=prod_info['name'], defaults={
            'price': prod_info['price'],
            'gender': prod_info['gender'],
            'is_featured': True,
            'store': store,
            'slug': prod_info['name'].lower().replace(' ', '-')
        })
        if not prod.image:
             prod.image = prod_info['image_path']
        prod.is_featured = True
        prod.save()

    print("Seeding/Fixing complete.")

if __name__ == '__main__':
    seed()
