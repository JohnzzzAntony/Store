# Moved from categories/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from firebase_auth_app.permissions import IsFirebaseAdmin
from store.models import Category

@api_view(["GET"])
@permission_classes([AllowAny])
def list_categories(request):
    cats = [{"id": cat.id, "name": cat.name, "slug": cat.slug, "image": cat.image.url if cat.image else ""} for cat in Category.objects.all()]
    return Response(cats)

@api_view(["POST"])
@permission_classes([IsFirebaseAdmin])
def create_category(request):
    name, slug = (request.data.get("name") or "").strip(), (request.data.get("slug") or "").strip()
    if not name or not slug: return Response({"error": "'name' and 'slug' are required."}, status=400)
    cat = Category.objects.create(name=name, slug=slug, image=request.data.get("image", ""))
    return Response({"id": cat.id, "name": cat.name, "slug": cat.slug, "image": cat.image.url if cat.image else ""}, status=status.HTTP_201_CREATED)

@api_view(["PUT"])
@permission_classes([IsFirebaseAdmin])
def update_category(request, category_id):
    try: cat = Category.objects.get(id=category_id)
    except Category.DoesNotExist: return Response({"error": "Category not found."}, status=404)
    name, slug = (request.data.get("name") or "").strip(), (request.data.get("slug") or "").strip()
    if not name or not slug: return Response({"error": "'name' and 'slug' are required."}, status=400)
    cat.name, cat.slug, cat.image = name, slug, request.data.get("image", "")
    cat.save()
    return Response({"id": cat.id, "name": cat.name, "slug": cat.slug, "image": cat.image.url if cat.image else ""})

@api_view(["DELETE"])
@permission_classes([IsFirebaseAdmin])
def delete_category(request, category_id):
    try: cat = Category.objects.get(id=category_id)
    except Category.DoesNotExist: return Response({"error": "Category not found."}, status=404)
    cat.delete()
    return Response({"message": "Category deleted."}, status=204)
