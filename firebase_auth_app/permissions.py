"""
firebase_auth_app/permissions.py
"""

from rest_framework.permissions import BasePermission


class IsFirebaseAdmin(BasePermission):
    message = "Admin access required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_admin
        )


class IsFirebaseOwnerOrAdmin(BasePermission):
    message = "You do not have permission to access this resource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, dict):
            owner_id = obj.get("userId") or obj.get("uid")
        else:
            owner_id = getattr(obj, "userId", None) or getattr(obj, "uid", None)
        return request.user.is_admin or request.user.uid == owner_id
