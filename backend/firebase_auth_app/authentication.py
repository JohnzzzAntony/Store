"""
firebase_auth_app/authentication.py
DRF Authentication class — validates Firebase ID tokens.

Frontend must send every authenticated request with:
    Authorization: Bearer <firebase_id_token>
"""

from django.conf import settings
from firebase_admin import auth as firebase_auth
from .firebase_init import db
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class FirebaseUser:
    """Minimal user object DRF attaches to request.user."""

    is_anonymous = False

    def __init__(self, uid, email, role="customer", display_name=""):
        self.uid          = uid
        self.email        = email
        self.role         = role
        self.display_name = display_name

    @property
    def is_authenticated(self):
        return True

    @property
    def is_admin(self):
        admin_email = getattr(settings, "STORE_ADMIN_EMAIL", "")
        return self.role == "admin" or (admin_email and self.email == admin_email)

    def __str__(self):
        return f"FirebaseUser({self.uid}, {self.email}, role={self.role})"


class FirebaseAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None

        id_token = auth_header[7:].strip()
        if not id_token:
            return None

        try:
            decoded = firebase_auth.verify_id_token(id_token)
        except firebase_auth.ExpiredIdTokenError:
            raise AuthenticationFailed("Firebase token has expired.")
        except firebase_auth.InvalidIdTokenError:
            raise AuthenticationFailed("Invalid Firebase token.")
        except Exception as exc:
            raise AuthenticationFailed(f"Token verification failed: {exc}")

        uid   = decoded["uid"]
        email = decoded.get("email", "")

        # Fetch role from Firestore (non-blocking — defaults to 'customer')
        role, display_name = "customer", ""
        try:
            snap = db.collection("users").document(uid).get()
            if snap.exists:
                data         = snap.to_dict()
                role         = data.get("role", "customer")
                display_name = data.get("displayName", "")
        except Exception:
            pass

        return (FirebaseUser(uid, email, role, display_name), None)
