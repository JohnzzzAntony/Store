import os
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from store.models import Order, OrderItem
import datetime

# For SMS (using a hypothetical or common provider like Twilio)
# from twilio.rest import Client

def send_sms(phone, message):
    """
    Placeholder function for SMS service.
    Integrate with Twilio, Nexmo, or any other provider here.
    """
    account_sid = os.environ.get('SMS_ACCOUNT_SID')
    auth_token = os.environ.get('SMS_AUTH_TOKEN')
    from_number = os.environ.get('SMS_FROM_NUMBER')
    
    if not phone:
        return
        
    print(f"DEBUG SMS: TO {phone} | MSG: {message}")
    
    # Example Twilio integration:
    # try:
    #     client = Client(account_sid, auth_token)
    #     client.messages.create(body=message, from_=from_number, to=phone)
    # except Exception as e:
    #     print(f"SMS Error: {e}")

def send_order_notification(order: Order, type="confirmation"):
    """
    Universal notification trigger (Email + SMS).
    Types: confirmation, shipped, delivered.
    """
    customer = order.customer
    if not customer or not customer.email:
        return
        
    items = order.orderitem_set.all()
    shipping = order.shippingaddress_set.first()
    
    context = {
        'order': order,
        'items': items,
        'shipping': shipping,
        'total': order.get_cart_total,
        'store_name': order.store.name if order.store else "Saleel Luxury",
        'date': datetime.datetime.now().strftime('%b %d, %Y'),
    }

    # 1. EMAIL NOTIFICATION
    subject_map = {
        'confirmation': f"Order Confirmation #{order.id} - {context['store_name']}",
        'shipped': f"Your Order #{order.id} Has Shipped! - {context['store_name']}",
        'delivered': f"Your Order #{order.id} Has Been Delivered! - {context['store_name']}",
    }
    
    template_map = {
        'confirmation': 'store/emails/order_confirmation.html',
        'shipped': 'store/emails/order_shipped.html',
        'delivered': 'store/emails/order_delivered.html',
    }
    
    subject = subject_map.get(type, "Order Update")
    template = template_map.get(type, 'store/emails/generic_update.html')
    
    html_content = render_to_string(template, context)
    
    email = EmailMessage(
        subject,
        html_content,
        settings.DEFAULT_FROM_EMAIL,
        [customer.email]
    )
    email.content_subtype = "html"
    
    # Attach Invoice PDF if it's confirmation (Optional/Premium feature)
    # from .utils import generate_invoice_pdf
    # pdf = generate_invoice_pdf(order)
    # email.attach(f"invoice_{order.id}.pdf", pdf, "application/pdf")
    
    try:
        email.send()
        print(f"DEBUG EMAIL: {type} sent to {customer.email}")
    except Exception as e:
        print(f"Email Error: {e}")

    # 2. SMS NOTIFICATION
    phone = shipping.phone if shipping else customer.phone
    if phone:
        sms_msg_map = {
            'confirmation': f"Thanks for your purchase! Order #{order.id} is confirmed. Total: AED {order.get_cart_total}.",
            'shipped': f"Good news! Your order #{order.id} from {context['store_name']} has been shipped.",
            'delivered': f"Success! Order #{order.id} has been delivered. We hope you love your fragrance!",
        }
        send_sms(phone, sms_msg_map.get(type))
