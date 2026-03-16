import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
from django.conf import settings

# Path to your Firebase service account key file
# The user should place their serviceAccountKey.json in the project root or configure the path
SERVICE_ACCOUNT_KEY = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')

if not firebase_admin._apps:
    try:
        if os.path.exists(SERVICE_ACCOUNT_KEY):
            cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin Initialized with Service Account Key.")
        else:
            # Only try default credentials if not local - else skip to avoid crash
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                firebase_admin.initialize_app()
                print("Firebase Admin Initialized with Default Credentials.")
            else:
                print("Firebase Admin NOT initialized: serviceAccountKey.json missing. Backend sync will be disabled.")
    except Exception as e:
        print(f"Firebase Admin Initialization Failed: {e}")

try:
    db = firestore.client()
except Exception:
    db = None

def verify_token(id_token):
    """Verifies a Firebase ID token and returns the decoded token."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying Firebase token: {e}")
        return None

def sync_user_to_firestore(user_data):
    """Syncs user data to Firestore."""
    if db is None:
        return
    user_ref = db.collection('users').document(user_data['uid'])
    user_ref.set({
        'email': user_data.get('email'),
        'name': user_data.get('name'),
        'last_login': firestore.SERVER_TIMESTAMP
    }, merge=True)

def save_order_to_firestore(order_data):
    """Saves order data to Firestore for real-time tracking."""
    if db is None:
        return
    order_ref = db.collection('orders').document(str(order_data['transaction_id']))
    order_ref.set(order_data)
