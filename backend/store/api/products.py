# Moved from products/views.py
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from firebase_auth_app.permissions import IsFirebaseAdmin
from store.models import Product, Category

def _validate_product(data):
    errors = {}
    name = str(data.get("name", "")).strip()
    if not name or len(name) > 200:
        errors["name"] = "Required, max 200 characters."
    try:
        if float(data["price"]) <= 0:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        errors["price"] = "Required — must be a positive number."
    try:
        if int(data["stock"]) < 0:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        errors["stock"] = "Required — must be a non-negative integer."
    if not data.get("category"):
        errors["category"] = "Required."
    return errors

@api_view(["GET"])
@permission_classes([AllowAny])
def list_products(request):
    products_qs = Product.objects.filter(in_stock=True)
    category = request.query_params.get("category")
    featured = request.query_params.get("featured")
    if category:
        products_qs = products_qs.filter(category__slug=category)
    if featured and featured.lower() == "true":
        products_qs = products_qs.filter(is_featured=True)
    products_qs = products_qs.order_by('-created_at')
    search = (request.query_params.get("search") or "").lower().strip()
    if search:
        products_qs = products_qs.filter(name__icontains=search)
    products = []
    for product in products_qs:
        data = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category": product.category.slug if product.category else None,
            "images": [product.imageURL] if product.imageURL else [],
            "stock": 1 if product.in_stock else 0,
            "featured": product.is_featured,
            "createdAt": product.created_at.isoformat() if product.created_at else None,
        }
        products.append(data)
    return Response(products)

@api_view(["POST"])
@permission_classes([IsFirebaseAdmin])
def create_product(request):
    errors = _validate_product(request.data)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    category_slug = request.data["category"]
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return Response({"errors": {"category": "Category not found."}}, status=status.HTTP_400_BAD_REQUEST)
    product = Product.objects.create(
        name=request.data["name"].strip(),
        description=(request.data.get("description") or "").strip(),
        price=float(request.data["price"]),
        category=category,
        in_stock=int(request.data["stock"]) > 0,
        is_featured=bool(request.data.get("featured", False)),
    )
    data = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category.slug,
        "images": [product.imageURL] if product.imageURL else [],
        "stock": 1 if product.in_stock else 0,
        "featured": product.is_featured,
        "createdAt": product.created_at.isoformat(),
    }
    return Response(data, status=status.HTTP_201_CREATED)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id, in_stock=True)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)
    data = {"id": product.id, "name": product.name, "description": product.description, "price": product.price, "category": product.category.slug if product.category else None, "images": [product.imageURL] if product.imageURL else [], "stock": 1 if product.in_stock else 0, "featured": product.is_featured, "createdAt": product.created_at.isoformat() if product.created_at else None}
    return Response(data)

@api_view(["PUT"])
@permission_classes([IsFirebaseAdmin])
def update_product(request, product_id):
    errors = _validate_product(request.data)
    if errors: return Response({"errors": errors}, status=400)
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)
    category_slug = request.data["category"]
    try:
        category = Category.objects.get(slug=category_slug)
    except Category.DoesNotExist:
        return Response({"errors": {"category": "Category not found."}}, status=status.HTTP_400_BAD_REQUEST)
    product.name, product.description, product.price, product.category, product.in_stock, product.is_featured = request.data["name"].strip(), (request.data.get("description") or "").strip(), float(request.data["price"]), category, int(request.data["stock"]) > 0, bool(request.data.get("featured", False))
    product.save()
    data = {"id": product.id, "name": product.name, "description": product.description, "price": product.price, "category": product.category.slug, "images": [product.imageURL] if product.imageURL else [], "stock": 1 if product.in_stock else 0, "featured": product.is_featured, "createdAt": product.created_at.isoformat()}
    return Response(data)

@api_view(["PATCH"])
@permission_classes([IsFirebaseAdmin])
def patch_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=404)
    allowed, patch = {"name", "description", "price", "category", "stock", "featured"}, {k: v for k, v in request.data.items() if k in allowed}
    if not patch: return Response({"error": "No valid fields provided."}, status=400)
    if "name" in patch: product.name = patch["name"].strip()
    if "description" in patch: product.description = patch["description"].strip()
    if "price" in patch: product.price = float(patch["price"])
    if "category" in patch:
        try: product.category = Category.objects.get(slug=patch["category"])
        except Category.DoesNotExist: return Response({"error": "Category not found."}, status=400)
    if "stock" in patch: product.in_stock = int(patch["stock"]) > 0
    if "featured" in patch: product.is_featured = bool(patch["featured"])
    product.save()
    return Response({"message": "Product updated.", "updatedFields": list(patch.keys())})

@api_view(["DELETE"])
@permission_classes([IsFirebaseAdmin])
def delete_product(request, product_id):
    try: product = Product.objects.get(id=product_id)
    except Product.DoesNotExist: return Response({"error": "Product not found."}, status=404)
    product.delete()
    return Response({"message": "Product deleted."}, status=status.HTTP_204_NO_CONTENT)
