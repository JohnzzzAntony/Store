import csv
import random

# Get actual data from DB (mocking it here since I verified it)
stores = ['Default Luxe Store'] # Verified via shell
categories = ['Perfumes', 'Body Mist', 'Room Spray']
scents = ['floral', 'woody', 'oriental', 'fresh', 'citrus', 'musky', 'aquatic']
genders = ['M', 'W', 'U']
sizes = [30, 50, 100, 150, 200]

names_prefixes = ["Golden", "Midnight", "Aqua", "Velvet", "Royal", "Desert", "Oceanic", "Wild", "Mystic", "Pure", "Silver", "Eternal", "Imperial", "Solar", "Black", "White", "Celestial", "Radiant", "Nomad", "Infinity"]
names_suffixes = ["Oud", "Musk", "Rose", "Sandalwood", "Amber", "Citrus", "Breeze", "Spirit", "Nights", "Dream", "Essence", "Soul", "Bloom", "Shadow", "Gold", "Diamond", "Pearl", "Elegance", "Passion", "Obsession"]

products = []

for i in range(1, 101):
    prefix = random.choice(names_prefixes)
    suffix = random.choice(names_suffixes)
    name = f"{prefix} {suffix}"
    
    # Ensure name uniqueness in the sample
    if any(p[0] == name for p in products):
        name = f"{name} {i}"
        
    slug = name.lower().replace(" ", "-")
    store = random.choice(stores)
    category = random.choice(categories)
    price = random.randint(150, 1200)
    description = f"Experience the {prefix.lower()} allure of {suffix}. A masterfully crafted {random.choice(scents)} fragrance that evokes {random.choice(['timeless elegance', 'modern sophistication', 'natural beauty', 'bold confidence'])}."
    gender = random.choice(genders)
    scent_profile = random.choice(scents)
    size_ml = random.choice(sizes)
    in_stock = "TRUE"
    is_featured = "TRUE" if random.random() < 0.2 else "FALSE"
    digital = "FALSE"
    
    products.append([name, slug, price, store, category, description, gender, scent_profile, size_ml, in_stock, is_featured, digital])

# Write to CSV
with open('c:/Users/johns/Music/ecom/django_ecommerce_mod5-master/import_products_100.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['name', 'slug', 'price', 'store', 'category', 'description', 'gender', 'scent_profile', 'size_ml', 'in_stock', 'is_featured', 'digital'])
    writer.writerows(products)

print(f"Successfully generated 100 products in c:/Users/johns/Music/ecom/django_ecommerce_mod5-master/import_products_100.csv")
