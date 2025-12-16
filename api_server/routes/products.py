from __future__ import annotations

import io
import imghdr
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, send_file
from mongoengine import Q
from mongoengine.errors import DoesNotExist

from models.product import Product
from models.category import Category
from models.stock_batch import StockBatch
from models.user import User

from core.inventory_manager import InventoryManager, InventoryError
from core.activity_logger import ActivityLogger

from utils import get_image_binary, extract_int, parse_date

bp = Blueprint('products', __name__)

API_USER_ID = 1001  # the dedicated API handler user


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _get_actor_id(data: dict | None) -> int:
    data = data or {}
    return extract_int(data.get("added_by")) or extract_int(data.get("user_id")) or API_USER_ID


def _get_actor_user(actor_id: int):
    return User.objects(id=actor_id).first()


def _err(msg: str, code: int = 400):
    return jsonify({"errors": [msg]}), code


def _detect_image_mimetype(blob: bytes) -> tuple[str, str]:
    """
    Returns (mimetype, ext) best-effort.
    """
    kind = imghdr.what(None, h=blob)  # 'png', 'jpeg', etc.
    if kind in ("jpeg", "jpg"):
        return "image/jpeg", "jpg"
    if kind == "png":
        return "image/png", "png"
    if kind == "gif":
        return "image/gif", "gif"
    if kind == "webp":
        return "image/webp", "webp"
    # fallback
    return "application/octet-stream", "bin"


# ----------------------------------------------------------------------
# GET /api/v1/products → list all products
# ----------------------------------------------------------------------
@bp.route('', methods=['GET'])
def list_product():
    args = request.args

    allowed_sort = {"id", "name", "price", "created_at"}
    sort_by = args.get('sort_by', 'id')
    if sort_by not in allowed_sort:
        sort_by = "id"

    sort_dir = (args.get('sort_dir', 'asc') or "asc").lower()
    sort_prefix = "-" if sort_dir == "desc" else ""

    page = extract_int(args.get('page'), 1) or 1
    per_page = extract_int(args.get('per_page'), 10) or 10

    include_image = args.get('include_image') == 'true'
    search_mode = (args.get('search_mode', 'AND') or "AND").upper()

    filters = []

    if name := args.get('name'):
        filters.append(Q(name__icontains=name))

    if brand := args.get('brand'):
        filters.append(Q(brand__icontains=brand))

    if category_id := args.get('category_id'):
        cat_int = extract_int(category_id)
        if cat_int is not None:
            filters.append(Q(category_id=cat_int))

    for op in ['gt', 'gte', 'lt', 'lte']:
        if price := args.get(f'price_{op}'):
            price_int = extract_int(price)
            if price_int is not None:
                filters.append(Q(**{f'price__{op}': price_int}))

    query = Product.objects()
    if filters:
        combined = filters[0]
        for f in filters[1:]:
            combined = (combined | f) if search_mode == "OR" else (combined & f)
        query = query.filter(combined)

    query = query.order_by(f'{sort_prefix}{sort_by}')

    total = query.count()
    skip = (page - 1) * per_page
    products = query.skip(skip).limit(per_page)
    pages = (total + per_page - 1) // per_page

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "products": [p.to_dict(include_image=include_image) for p in products]
    })


# ----------------------------------------------------------------------
# GET /api/v1/products/<id> → retrieve product based on ID
# ----------------------------------------------------------------------
@bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    include_image = request.args.get('include_image') == 'true'
    include_batches = request.args.get('include_batches') == 'true'

    product = Product.objects(id=id).first()
    if not product:
        return _err("Product not found", 404)

    return jsonify(product.to_dict(include_image, include_batches))


# ----------------------------------------------------------------------
# ✅ NEW: GET /api/v1/products/<id>/image → fetch product image bytes
# ----------------------------------------------------------------------
@bp.route('/<int:id>/image', methods=['GET'])
def get_product_image(id: int):
    product = Product.objects(id=id).first()
    if not product:
        return _err("Product not found", 404)

    blob = product.product_image
    if not blob:
        return _err("No product image", 404)

    mimetype, ext = _detect_image_mimetype(blob)

    resp = send_file(
        io.BytesIO(blob),
        mimetype=mimetype,
        as_attachment=False,
        download_name=f"product_{id}.{ext}"
    )
    # light caching
    resp.headers["Cache-Control"] = "public, max-age=3600"
    return resp


# ----------------------------------------------------------------------
# GET /api/v1/products/<product_id>/stock_batches → list all batches
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['GET'])
def list_stock_batches(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    category = Category.objects(id=product.category_id).first() if product.category_id else None
    batches = [batch.to_dict() for batch in StockBatch.objects(product_id=product.id)]

    return jsonify({
        "product_id": product.id,
        "product_name": product.name,
        "product_category": category.name if category else "Uncategorized",
        "stock_batches": batches,
        "total_stock": product.stock_level
    })


# ----------------------------------------------------------------------
# POST /api/v1/products → create new product
# ----------------------------------------------------------------------
@bp.route('', methods=['POST'])
def create_product():
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    if not data.get('name'):
        return _err("Product name is required", 400)

    price = extract_int(data.get('price'))
    if price is None:
        return _err("Price must be a number", 400)

    category_id = None
    if 'category_id' in data and data.get('category_id') not in (None, "", "null"):
        category_id = extract_int(data.get('category_id'))

    if category_id:
        if not Category.objects(id=category_id).first():
            return _err("Invalid category ID", 400)

    if category_id is None:
        has_any_category = Category.objects().first() is not None
        product_category_required = True  # change to False if you want fully optional
        if has_any_category and product_category_required:
            return _err("Category is required", 400)

    image_blob = get_image_binary()
    min_stock = extract_int(data.get('min_stock_level'), 10)

    product = Product(
        name=data['name'],
        brand=data.get('brand'),
        price=price,
        category_id=category_id,
        min_stock_level=min_stock,
        product_image=image_blob,
        details=data.get('details')
    )

    product.save()

    initial_stock = extract_int(data.get('stock_level'), 0) or 0
    include_batches = False

    actor_id = _get_actor_id(data)
    actor_user = _get_actor_user(actor_id)

    if initial_stock > 0:
        batch = StockBatch(
            product_id=product.id,
            quantity=initial_stock,
            expiration_date=parse_date(data.get('expiration_date')),
            added_at=datetime.now(timezone.utc),
            added_by=actor_user,
            reason="Initial stock"
        )
        batch.save()
        include_batches = True

    ActivityLogger.log_api_activity(
        method='POST',
        target_entity='product',
        user_id=actor_id,
        details=f"Created product '{product.name}' (id={product.id})"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Create',
        quantity=initial_stock if initial_stock > 0 else None,
        notes=f"Product created with initial stock: {initial_stock}" if initial_stock > 0 else "Product created"
    )

    return jsonify(product.to_dict(include_image=True, include_batches=include_batches)), 201


# ----------------------------------------------------------------------
# POST /api/v1/products/<product_id>/stock_batches → add stock batch
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['POST'])
def add_stock_batch(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    data = request.get_json() or {}

    quantity = extract_int(data.get('quantity'))
    if not quantity or quantity <= 0:
        return _err("Quantity must be a positive integer", 400)

    expiration_date = parse_date(data.get('expiration_date'))
    if not expiration_date:
        return _err("Expiration date is required (YYYY-MM-DD)", 400)

    actor_id = _get_actor_id(data)
    actor_user = _get_actor_user(actor_id)
    reason = data.get("reason") or "Stock added"

    batch = StockBatch(
        product_id=product.id,
        quantity=quantity,
        expiration_date=expiration_date,
        added_at=datetime.now(timezone.utc),
        added_by=actor_user,
        reason=reason
    )

    batch.save()

    ActivityLogger.log_api_activity(
        method='POST',
        target_entity='stock_batch',
        user_id=actor_id,
        details=f"Added stock batch: product_id={product.id}, qty={quantity}, exp={expiration_date}"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Restock',
        quantity=quantity,
        notes=f"{reason}. Expires: {expiration_date}"
    )

    return jsonify({
        "message": "Stock batch added",
        "product_id": product.id,
        "batch": batch.to_dict(),
        "new_stock_level": product.stock_level
    }), 201


# ----------------------------------------------------------------------
# PUT /api/v1/products/<product_id> → Replace a product
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>', methods=['PUT'])
def replace_product(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    if 'name' not in data or not data.get("name"):
        return _err("Product name is required for PUT", 400)

    price = extract_int(data.get('price'))
    if price is None:
        return _err("Price must be a number", 400)

    category_id = None
    if 'category_id' in data and data.get('category_id') not in (None, "", "null"):
        category_id = extract_int(data.get('category_id'))
        if category_id and not Category.objects(id=category_id).first():
            return _err("Invalid category ID", 400)

    product.name = data['name']
    product.brand = data.get('brand')
    product.price = price
    product.category_id = category_id
    product.min_stock_level = extract_int(data.get('min_stock_level'), product.min_stock_level)
    product.details = data.get('details', product.details)

    StockBatch.objects(product_id=product.id).delete()

    new_stock = extract_int(data.get('stock_level'))
    actor_id = _get_actor_id(data)
    actor_user = _get_actor_user(actor_id)

    if new_stock is not None and new_stock > 0:
        batch = StockBatch(
            product_id=product.id,
            quantity=new_stock,
            expiration_date=parse_date(data.get('expiration_date')),
            added_at=datetime.now(timezone.utc),
            added_by=actor_user,
            reason="Stock replacement"
        )
        batch.save()

    new_image = get_image_binary()
    if new_image is not None:
        product.product_image = new_image

    product.save()

    ActivityLogger.log_api_activity(
        method='PUT',
        target_entity='product',
        user_id=actor_id,
        details=f"Replaced product id={product.id}, name={product.name}"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Edit',
        quantity=new_stock if new_stock else None,
        notes=f"Product replaced. Stock set to {new_stock}" if new_stock else "Product replaced"
    )

    return jsonify(product.to_dict(include_image=True, include_batches=True))


# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id> → edit product details
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>', methods=['PATCH'])
def patch_product(product_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    if 'name' in data and not data['name']:
        return _err("Product name cannot be empty", 400)

    if 'price' in data:
        price = extract_int(data['price'])
        if price is None:
            return _err("Price must be a number", 400)
        product.price = price

    if 'category_id' in data:
        cat_val = data.get('category_id')
        if cat_val in (None, "", "null"):
            product.category_id = None
        else:
            cat_id = extract_int(cat_val)
            if cat_id and not Category.objects(id=cat_id).first():
                return _err("Invalid category ID", 400)
            product.category_id = cat_id

    if 'name' in data:
        product.name = data['name']
    if 'brand' in data:
        product.brand = data['brand']
    if 'min_stock_level' in data:
        product.min_stock_level = extract_int(data['min_stock_level'], product.min_stock_level)
    if 'details' in data:
        product.details = data['details']

    actor_id = _get_actor_id(data)
    actor_user = _get_actor_user(actor_id)

    if 'stock_level' in data:
        qty = extract_int(data.get('stock_level'))
        if qty is not None:
            if qty <= 0:
                return _err("stock_level must be a positive integer", 400)

            batch = StockBatch(
                product_id=product.id,
                quantity=qty,
                expiration_date=parse_date(data.get('expiration_date')),
                added_at=datetime.now(timezone.utc),
                added_by=actor_user,
                reason=data.get("reason") or "Stock added via edit"
            )
            batch.save()

    new_image = get_image_binary()
    if new_image is not None:
        product.product_image = new_image

    product.save()

    changed_fields = [
        k for k in ('name', 'price', 'brand', 'category_id', 'min_stock_level', 'details')
        if k in data
    ]
    if 'stock_level' in data:
        changed_fields.append("stock_level")

    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='product',
        user_id=actor_id,
        details=f"Updated product id={product.id}: {', '.join(changed_fields) if changed_fields else 'no fields'}"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Edit',
        quantity=extract_int(data.get('stock_level')) if 'stock_level' in data else None,
        notes=f"Updated fields: {', '.join(changed_fields)}" if changed_fields else "Updated product"
    )

    return jsonify(product.to_dict(include_image=True, include_batches=True))


# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id> → remove stock
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['PATCH'])
def remove_stock_batch(product_id, batch_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    batch = StockBatch.objects(id=batch_id, product_id=product_id).first()
    if not batch:
        return _err("Stock batch not found", 404)

    data = request.get_json() or {}
    remove_qty = extract_int(data.get('quantity'))
    reason = data.get('reason') or 'No reason provided'

    if not remove_qty or remove_qty <= 0:
        return _err("Quantity to remove must be positive", 400)

    if remove_qty > (batch.quantity or 0):
        return _err("Cannot remove more than batch quantity", 400)

    batch.quantity = (batch.quantity or 0) - remove_qty
    batch.reason = reason
    batch.save()

    actor_id = _get_actor_id(data)

    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='stock_batch',
        user_id=actor_id,
        details=f"Removed {remove_qty} units from batch {batch.id} of product {product.id}. Reason: {reason}"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Remove Stock',
        quantity=remove_qty,
        notes=f"Removed {remove_qty} units from batch {batch.id}. Reason: {reason}"
    )

    return jsonify({
        "message": f"{remove_qty} units removed from batch {batch.id}",
        "reason": reason,
        "batch": batch.to_dict(),
        "new_stock_level": product.stock_level
    })


# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id>/metadata
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>/metadata', methods=['PATCH'])
def update_stock_batch_metadata(product_id, batch_id):
    batch = StockBatch.objects(id=batch_id, product_id=product_id).first()
    if not batch:
        return _err("Stock batch not found", 404)

    data = request.get_json() or {}

    if "expiration_date" in data:
        new_date = parse_date(data.get('expiration_date'))
        if not new_date:
            return _err("Invalid expiration date", 400)
        batch.expiration_date = new_date

    actor_id = _get_actor_id(data)
    actor_user = _get_actor_user(actor_id)

    if "added_by" in data:
        user_id = extract_int(data.get('added_by'))
        if user_id:
            batch.added_by = User.objects(id=user_id).first()

    if "reason" in data:
        batch.reason = data.get('reason') or batch.reason

    changed_fields = [f for f in ['expiration_date', 'added_by', 'reason'] if f in data]

    ActivityLogger.log_product_action(
        product_id=product_id,
        user_id=actor_id,
        action_type='Edit Batch Metadata',
        quantity=None,
        notes=f"Updated batch {batch.id} fields: {', '.join(changed_fields) if changed_fields else 'no fields'}"
    )

    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='stock_batch',
        user_id=actor_id,
        details=f"Updated metadata for batch {batch.id} of product {product_id}: {', '.join(changed_fields) if changed_fields else 'no fields'}"
    )

    batch.save()
    return jsonify(batch.to_dict())


# ----------------------------------------------------------------------
# DELETE /api/v1/products/<id> → delete product
# ----------------------------------------------------------------------
@bp.route('/<int:id>', methods=['DELETE'])
def delete_product(id):
    data = request.get_json(silent=True) or {}
    actor_id = _get_actor_id(data)

    product = Product.objects(id=id).first()
    if not product:
        return _err("Product not found", 404)

    name = product.name

    StockBatch.objects(product_id=product.id).delete()
    product.delete()

    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='product',
        user_id=actor_id,
        details=f"Deleted product id={id}, name={name}"
    )

    ActivityLogger.log_product_action(
        product_id=id,
        user_id=actor_id,
        action_type='Delete',
        quantity=None,
        notes=f"Deleted product '{name}'"
    )

    return jsonify({"message": f"{name} product was deleted successfully from inventory."}), 200


# ----------------------------------------------------------------------
# DELETE /api/v1/products/<product_id>/stock_batches/<batch_id> → delete batch
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['DELETE'])
def delete_stock_batch(product_id, batch_id):
    product = Product.objects(id=product_id).first()
    if not product:
        return _err("Product not found", 404)

    batch = StockBatch.objects(id=batch_id, product_id=product_id).first()
    if not batch:
        return _err("Stock batch not found", 404)

    if (batch.quantity or 0) > 0:
        return _err("Cannot delete a batch with remaining stock. Dispose stock first.", 400)

    data = request.get_json(silent=True) or {}
    actor_id = _get_actor_id(data)

    qty_before = batch.quantity or 0
    batch.delete()

    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='stock_batch',
        user_id=actor_id,
        details=f"Deleted stock batch id={batch_id} for product_id={product_id}"
    )

    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=actor_id,
        action_type='Delete Stock Batch',
        quantity=qty_before,
        notes=f"Deleted batch {batch_id} of {product.name}"
    )

    return jsonify({
        "message": f"Batch {batch_id} of {product.name} deleted successfully",
        "product_id": product_id
    }), 200
