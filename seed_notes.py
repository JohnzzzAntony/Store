import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, Store

def seed_notes():
    # Example notes
    to_update = Product.objects.all()
    for p in to_update:
        if not p.top_notes:
            p.top_notes = "Bergamot, Pink Pepper"
        if not p.heart_notes:
            p.heart_notes = "Damask Rose, Patchouli"
        if not p.base_notes:
            p.base_notes = "Amber, Vanilla, Oud"
        p.save()
    print(f"Updated notes for {to_update.count()} products.")

if __name__ == '__main__':
    seed_notes()
