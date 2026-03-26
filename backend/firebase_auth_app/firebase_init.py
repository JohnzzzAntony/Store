"""
firebase_init.py
Place at the ROOT of your Django project (same level as manage.py).
Initialises Firebase Admin SDK once — import anywhere via:

    from firebase_init import db, auth as firebase_auth
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from decouple import config

_initialized = False


def _init():
    global _initialized, db
    if _initialized or firebase_admin._apps:
        _initialized = True
        return

    try:
        sa_path = config("FIREBASE_SERVICE_ACCOUNT_PATH", default="")
        if sa_path and os.path.exists(sa_path):
            cred = credentials.Certificate(sa_path)
        else:
            # Check for individual vars
            project_id = config("FIREBASE_PROJECT_ID", default="")
            if not project_id:
                print("Firebase NOT initialized: Missing FIREBASE_PROJECT_ID in .env.")
                return

            cred = credentials.Certificate({
                "type":                        "service_account",
                "project_id":                  project_id,
                "private_key_id":              config("FIREBASE_PRIVATE_KEY_ID", default=""),
                "private_key":                 config("FIREBASE_PRIVATE_KEY", default="").replace("\\n", "\n"),
                "client_email":                config("FIREBASE_CLIENT_EMAIL", default=""),
                "client_id":                   config("FIREBASE_CLIENT_ID", default=""),
                "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
                "token_uri":                   "https://oauth2.googleapis.com/token",
            })

        firebase_admin.initialize_app(cred, {
            "projectId":     config("FIREBASE_PROJECT_ID", default=project_id),
            "storageBucket": config(
                "FIREBASE_STORAGE_BUCKET",
                default=f"{project_id}.appspot.com"
            ),
            "databaseId":    config("FIREBASE_DATABASE_ID", default="(default)"),
        })
        _initialized = True
        globals()['db'] = firestore.client()
    except Exception as e:
        print(f"Firebase Admin Initialization Failed: {e}")

_init()

try:
    db = firestore.client()
except Exception:
    db = None

from firebase_admin import auth as firebase_auth
auth = firebase_auth
