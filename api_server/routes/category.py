from __future__ import annotations

import io
import imghdr

from flask import Blueprint, request, jsonify, send_file
from mongoengine.errors import DoesNotExist

from models.category import Category
from core.activity_logger import ActivityLogger
from utils import get_image_binary

bp = Blueprint('categories', __name__)


def _detect_image_mimetype(blob: bytes) -> tuple[str, str]:
    kind = imghdr.what(None, h=blob)
    if kind in ("jpeg", "jpg"):
        return "image/jpeg", "jpg"
    if kind == "png":
        return "image/png", "png"
    if kind == "gif":
        return "image/gif", "gif"
    if kind == "webp":
        return "image/webp", "webp"
    return "application/octet-stream", "bin"


# ----------------------------------------------------------------------
# GET /api/v1/categories → list all categories
# ----------------------------------------------------------------------
@bp.route('', methods=['GET'])
def list_categories():
    include_image = request.args.get('include_image', 'false').lower() == 'true'
    categories = Category.objects().order_by('name')

    return jsonify({
        'total': len(categories),
        'categories': [c.to_dict(include_image) for c in categories]
    }), 200


# ----------------------------------------------------------------------
# GET /api/v1/categories/<id> → get single category
# ----------------------------------------------------------------------
@bp.route('/<int:cat_id>', methods=['GET'])
def get_category(cat_id):
    include_image = request.args.get('include_image', 'false').lower() == 'true'

    try:
        category = Category.objects.get(id=cat_id)
    except DoesNotExist:
        return jsonify({"errors": ["Category not found"]}), 404

    return jsonify(category.to_dict(include_image=include_image)), 200


# ----------------------------------------------------------------------
# ✅ NEW: GET /api/v1/categories/<id>/image → fetch category image bytes
# ----------------------------------------------------------------------
@bp.route('/<int:cat_id>/image', methods=['GET'])
def get_category_image(cat_id: int):
    try:
        category = Category.objects.get(id=cat_id)
    except DoesNotExist:
        return jsonify({"errors": ["Category not found"]}), 404

    blob = category.category_image
    if not blob:
        return jsonify({"errors": ["No category image"]}), 404

    mimetype, ext = _detect_image_mimetype(blob)

    resp = send_file(
        io.BytesIO(blob),
        mimetype=mimetype,
        as_attachment=False,
        download_name=f"category_{cat_id}.{ext}"
    )
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


# ----------------------------------------------------------------------
# POST /api/v1/categories → create new category
# ----------------------------------------------------------------------
@bp.route('', methods=['POST'])
def create_category():
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    name = data.get('name')
    if not name:
        return jsonify({"errors": ["Category name is required"]}), 400

    if Category.objects(name__iexact=name.strip()).first():
        return jsonify({"errors": ["Category name already exists"]}), 400

    image_blob = get_image_binary()

    try:
        category = Category(
            name=name.strip(),
            description=data.get('description'),
            category_image=image_blob
        )
        category.save()

        user_id = data.get('user_id')
        if user_id:
            ActivityLogger.log_api_activity(
                method='POST',
                target_entity='category',
                user_id=user_id,
                details=f"Created category: {name}"
            )

        return jsonify(category.to_dict(include_image=True)), 201

    except Exception as e:
        return jsonify({"errors": [f"Server error: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# PUT /api/v1/categories/<id> → replace category
# ----------------------------------------------------------------------
@bp.route('/<int:cat_id>', methods=['PUT'])
def replace_category(cat_id):
    try:
        category = Category.objects.get(id=cat_id)
    except DoesNotExist:
        return jsonify({"errors": ["Category not found"]}), 404

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    name = data.get('name')
    if not name:
        return jsonify({"errors": ["Category name is required for PUT"]}), 400

    existing = Category.objects(
        name__iexact=name.strip(),
        id__ne=cat_id
    ).first()
    if existing:
        return jsonify({"errors": ["Category name already exists"]}), 400

    old_name = category.name
    category.name = name.strip()
    category.description = data.get('description')

    new_image = get_image_binary()

    try:
        if new_image is not None:
            category.category_image = new_image

        category.save()

        ActivityLogger.log_api_activity(
            method='PUT',
            target_entity='category',
            user_id=data.get('user_id'),
            details=f"Replaced category: {old_name} → {name}"
        )
        return jsonify(category.to_dict(include_image=True)), 200

    except Exception as e:
        return jsonify({"errors": [str(e)]}), 500


# ----------------------------------------------------------------------
# PATCH /api/v1/categories/<id> → update category
# ----------------------------------------------------------------------
@bp.route('/<int:cat_id>', methods=['PATCH'])
def update_category(cat_id):
    try:
        category = Category.objects.get(id=cat_id)
    except DoesNotExist:
        return jsonify({"errors": ["Category not found"]}), 404

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    changes = []
    user_id = data.get('user_id')

    if 'name' in data:
        if not data['name']:
            return jsonify({"errors": ["Category name cannot be empty"]}), 400

        existing = Category.objects(
            name__iexact=data['name'].strip(),
            id__ne=cat_id
        ).first()
        if existing:
            return jsonify({"errors": ["Category name already exists"]}), 400

        changes.append(f"name: {category.name} → {data['name']}")
        category.name = data['name'].strip()

    if 'description' in data:
        changes.append("description updated")
        category.description = data['description']

    new_image = get_image_binary()
    if new_image is not None:
        category.category_image = new_image
        changes.append("image updated")

    if not changes:
        return jsonify({"message": "No changes provided"}), 200

    try:
        category.save()

        ActivityLogger.log_api_activity(
            method='PATCH',
            target_entity='category',
            user_id=user_id,
            details=f"Updated category {category.name}: {', '.join(changes)}"
        )

        return jsonify(category.to_dict(include_image=True)), 200

    except Exception as e:
        return jsonify({"errors": [str(e)]}), 500


# ----------------------------------------------------------------------
# DELETE /api/v1/categories/<id> → delete category
# ----------------------------------------------------------------------
@bp.route('/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    data = request.get_json(silent=True) or {}

    try:
        category = Category.objects.get(id=cat_id)
    except DoesNotExist:
        return jsonify({"errors": ["Category not found"]}), 404

    user_id = data.get("user_id")

    from models.product import Product
    if Product.objects(category_id=cat_id).first():
        count = Product.objects(category_id=cat_id).count()
        return jsonify({
            "errors": [f"Cannot delete category while it has {count} linked products"]
        }), 400

    category_name = category.name
    category.delete()

    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='category',
        user_id=user_id,
        details=f"Deleted category '{category_name}'"
    )

    return jsonify({
        "message": f"Category '{category_name}' deleted successfully"
    }), 200
