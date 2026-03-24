"""
firebase_auth_app/views.py
User profile sync between Firebase Auth and Firestore.
"""

from datetime import datetime, timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .firebase_init import db
from firebase_auth_app.permissions import IsFirebaseAdmin


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sync_user(request):
    """
    Called by the frontend immediately after Firebase sign-in / sign-up.
    Creates the Firestore /users/{uid} document if it doesn't exist,
    otherwise updates mutable fields.
    """
    from .firebase_init import db
    if db is None:
        return Response({"error": "Firebase not configured."}, status=500)

    user = request.user
    uid  = user.uid
    ref  = db.collection("users").document(uid)
    snap = ref.get()

    if snap.exists:
        ref.update({
            "displayName": request.data.get("displayName", user.display_name),
            "photoURL":    request.data.get("photoURL", ""),
        })
        return Response({"message": "Profile updated.", "uid": uid})

    # First login — create document
    new_user = {
        "uid":         uid,
        "email":       user.email,
        "displayName": request.data.get("displayName", ""),
        "photoURL":    request.data.get("photoURL", ""),
        "role":        "customer",
        "createdAt":   datetime.now(timezone.utc).isoformat(),
    }
    ref.set(new_user)
    return Response({"message": "User created.", "uid": uid}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_me(request):
    """Returns the current user's Firestore profile."""
    from .firebase_init import db
    if db is None:
        return Response({"error": "Firebase not configured."}, status=500)

    doc = db.collection("users").document(request.user.uid).get()
    if not doc.exists:
        return Response({"error": "User not found."}, status=404)
    return Response(doc.to_dict())


@api_view(["GET"])
@permission_classes([IsFirebaseAdmin])
def list_users(request):
    """Admin only — all users."""
    from .firebase_init import db
    if db is None:
        return Response({"error": "Firebase not configured."}, status=500)

    docs  = db.collection("users").stream()
    users = [doc.to_dict() for doc in docs]
    return Response(users)


@api_view(["PATCH"])
@permission_classes([IsFirebaseAdmin])
def set_user_role(request, uid):
    """Admin only — promote / demote user."""
    role = request.data.get("role")
    if role not in ("admin", "customer"):
        return Response({"error": "role must be 'admin' or 'customer'."}, status=400)

    ref = db.collection("users").document(uid)
    if not ref.get().exists:
        return Response({"error": "User not found."}, status=404)

    ref.update({"role": role})
    return Response({"message": f"Role set to '{role}' for {uid}."})
