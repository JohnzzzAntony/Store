import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category
from django.utils.text import slugify

categories = ['Perfumes', 'Body Mist', 'Room Spray']
for name in categories:
    slug = slugify(name)
    category, created = Category.objects.get_or_create(
        slug=slug,
        defaults={'name': name}
    )
    if created:
        print(f"Created category: {name}")
    else:
        print(f"Category already exists: {name}")
