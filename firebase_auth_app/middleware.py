"""
firebase_auth_app/middleware.py
Injects request.firebase_uid and request.firebase_email for use in
non-DRF Django views / signals.
"""


class FirebaseAuthMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from firebase_admin import auth as firebase_auth

        request.firebase_uid   = None
        request.firebase_email = None

        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            try:
                decoded                = firebase_auth.verify_id_token(token)
                request.firebase_uid   = decoded["uid"]
                request.firebase_email = decoded.get("email", "")
            except Exception:
                pass

        return self.get_response(request)
