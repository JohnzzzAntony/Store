# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn, firestore_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app, firestore

initialize_app()
set_global_options(max_instances=10)

@firestore_fn.on_document_created(document="orders/{orderId}")
def on_order_created(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    """Triggered when a new order is created in Firestore."""
    if event.data is None:
        return
    
    order_data = event.data.to_dict()
    print(f"New Order Detected: {event.params['orderId']} for {order_data.get('customer_email')}")
    
    # Example: Send notification or update analytics
    db = firestore.client()
    stats_ref = db.collection("analytics").document("overall_stats")
    stats_ref.set({
        "total_orders": firestore.Increment(1),
        "total_revenue": firestore.Increment(order_data.get("total", 0))
    }, merge=True)

@firestore_fn.on_document_created(document="user_sessions/{uid}")
def on_user_login(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    """Track user login frequency."""
    if event.data is None:
        return
        
    db = firestore.client()
    user_ref = db.collection("users").document(event.params["uid"])
    user_ref.set({"login_count": firestore.Increment(1)}, merge=True)