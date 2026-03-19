import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Store, Product, Category

# Create Default Store
store, created = Store.objects.get_or_create(
    slug='default-store',
    defaults={
        'name': 'Default Luxe Store',
        'details': 'Our primary luxury perfume outlet.',
        'primary_color': '#2D5A5A',
        'secondary_color': '#1E3E3E',
        'font_family': 'serif',
    }
)

if created:
    print(f"Created store: {store.name}")
else:
    print(f"Store {store.name} already exists.")

# Assign existing products and categories to this store
Category.objects.filter(store__isnull=True).update(store=store)
Product.objects.filter(store__isnull=True).update(store=store)

print("Updated existing products and categories.")
