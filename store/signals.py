from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from .core.notifications import send_order_notification

@receiver(post_save, sender=Order)
def order_status_update_notification(sender, instance, created, **kwargs):
    """
    Triggers notifications when an order status is updated.
    """
    if created:
        # Initial order confirmation is handled in the view already
        return

    # Check for specific status changes
    # Status values are case-insensitive or exact matches depending on admin usage
    status = instance.status.lower()
    
    if 'shipped' in status:
        try:
            send_order_notification(instance, type="shipped")
        except Exception as e:
            print(f"Error in 'shipped' status signal: {e}")
            
    elif 'delivered' in status:
        try:
            send_order_notification(instance, type="delivered")
        except Exception as e:
            print(f"Error in 'delivered' status signal: {e}")
