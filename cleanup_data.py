import os
import django

# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import Customer, Order, OrderItem, ShippingAddress

def cleanup():
    print("Starting data cleanup...")
    
    # Delete all shipping addresses
    ShippingAddress.objects.all().delete()
    print("Deleted all shipping addresses.")
    
    # Delete all order items
    OrderItem.objects.all().delete()
    print("Deleted all order items.")
    
    # Delete all orders
    Order.objects.all().delete()
    print("Deleted all orders.")
    
    # Delete all customers
    Customer.objects.all().delete()
    print("Deleted all customers.")
    
    # Delete all non-staff users
    deleted_users = User.objects.filter(is_staff=False).delete()
    print(f"Deleted {deleted_users[0]} non-staff users.")
    
    print("Cleanup complete.")

if __name__ == '__main__':
    cleanup()
