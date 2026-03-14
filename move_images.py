import os
import shutil
import django
import sys

# Setup Django
sys.path.append(r'c:\Users\johns\Music\ecom\django_ecommerce_mod5-master')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product

def move_and_update():
    base_dir = r'c:\Users\johns\Music\ecom\django_ecommerce_mod5-master'
    static_images = os.path.join(base_dir, 'static', 'images')
    products_dir = os.path.join(static_images, 'products')
    
    # Files to move (Source, Destination Filename, DB Product Name)
    files = [
        (r'C:\Users\johns\.gemini\antigravity\brain\4c2850dc-7af0-4dfe-8114-166ff5dca22d\saleel_logo_1773436780056.png', 
         os.path.join(static_images, 'logo.png'), None),
        (r'C:\Users\johns\.gemini\antigravity\brain\4c2850dc-7af0-4dfe-8114-166ff5dca22d\swim_by_the_beach_perfume_1773438587904.png', 
         os.path.join(products_dir, 'swim.png'), 'Swim By The Beach'),
        (r'C:\Users\johns\.gemini\antigravity\brain\4c2850dc-7af0-4dfe-8114-166ff5dca22d\aqua_marine_perfume_1773438602691.png', 
         os.path.join(products_dir, 'aqua.png'), 'Aqua Marine'),
        (r'C:\Users\johns\.gemini\antigravity\brain\4c2850dc-7af0-4dfe-8114-166ff5dca22d\solaris_perfume_1773438639026.png', 
         os.path.join(products_dir, 'solaris.png'), 'Solaris')
    ]
    
    for src, dst, product_name in files:
        if os.path.exists(src):
            print(f"Copying {src} to {dst}")
            shutil.copy2(src, dst)
            
            if product_name:
                try:
                    product = Product.objects.get(name=product_name)
                    # Relative path to MEDIA_ROOT which is static/images
                    # So 'products/swim.png'
                    product.image = f"products/{os.path.basename(dst)}"
                    product.save()
                    print(f"Updated product {product_name} image path.")
                except Product.DoesNotExist:
                    print(f"Product {product_name} not found in DB.")
        else:
            print(f"Source file not found: {src}")

if __name__ == "__main__":
    move_and_update()
