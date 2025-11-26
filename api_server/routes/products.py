from flask import Blueprint, request, jsonify
from extensions import db

from models.product import Product
from models.category import Category
from models.stock_batch import StockBatch
from models.user import User
from core.inventory_manager import InventoryManager, InventoryError
from core.activity_logger import ActivityLogger


from utils import get_image_blob, extract_int, parse_date
from datetime import datetime, timezone

bp = Blueprint('products', __name__)

API_USER_ID = 1  # the dedicated API handler user


# ----------------------------------------------------------------------
# GET /api/v1/products → list all products
#
# Filters:
# name: String (optional, contains)
# brand: String (optional, contains)
# category_id: Integer (optional)
# price_gt: Integer (optional)
# price_gte: Integer (optional)
# price_lt: Integer (optional)
# price_lte: Integer (optional)
#
# Advanced:
# sort_by: String (optional) → name, price, created_at
# sort_dir: String (optional) → asc or desc
#
# Pagination:
# page: Integer (optional, default=1)
# per_page: Integer (optional, default=10)
#
# Logic mode:
# search_mode: "AND" or "OR" (default: AND)
# ----------------------------------------------------------------------
@bp.route('', methods = ['GET'])
def list_product():
    from sqlalchemy import or_, and_
    category_id = request.args.get('category_id')
    
    name = request.args.get('name')
    brand = request.args.get('brand')
    category_id = request.args.get('category_id')
    price_gt = request.args.get('price_gt')
    price_gte = request.args.get('price_gte')
    price_lt = request.args.get('price_lt')
    price_lte = request.args.get('price_lte')
    sort_by = request.args.get('sort_by', 'id')
    sort_dir = request.args.get('sort_dir', 'asc')

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    include_image = request.args.get('include_image') == 'true'
    search_mode = request.args.get('search_mode', 'AND').upper()  # AND or OR
    
    query = Product.query
    filters = []
    
    # Build filters
    if name:
        filters.append(Product.name.ilike(f"%{name}%"))

    if brand:
        filters.append(Product.brand.ilike(f"%{brand}%"))  
        
    if category_id:
        filters.append(Product.category_id == category_id)    
    
    if price_gt and price_gt.isdigit():
        filters.append(Product.price > int(price_gt))

    if price_gte and price_gte.isdigit():
        filters.append(Product.price >= int(price_gte))

    if price_lt and price_lt.isdigit():
        filters.append(Product.price < int(price_lt))

    if price_lte and price_lte.isdigit():
        filters.append(Product.price <= int(price_lte))

    # Apply AND / OR mode
    if filters:
        if search_mode == "OR":
            query = query.filter(or_(*filters))
        else:
            query = query.filter(and_(*filters))

    # Apply sorting
    sort_column = getattr(Product, sort_by, Product.id)
    if sort_dir == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    # Pagination
    page_data = query.paginate(page=page, per_page=per_page, error_out=False)
        
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": page_data.total,
        "pages": page_data.pages,
        "products": [p.to_dict(include_image) for p in page_data.items]
    })
    
    
# ----------------------------------------------------------------------
# GET /api/v1/products/<id> → retrieving a product based on ID 
# ----------------------------------------------------------------------    
@bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    include_image = request.args.get('include_image') == 'true'
    include_batches = request.args.get('include_batches') == 'true'
    
    # return product data with optional image and batch details
    return jsonify(product.to_dict(include_image, include_batches))

# ----------------------------------------------------------------------
# GET /api/v1/products/<product_id>/stock_batches → list all batches
# product_id: Integer (required)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['GET'])
def list_stock_batches(product_id):
    product = Product.query.get_or_404(product_id)
    category = Category.query.get(product.category_id)
    batches = [batch.to_dict() for batch in product.stock_batches]
    
    return jsonify({
        "product_id": product.id,
        "product_name": product.name,
        "product_category": category.name,
        "stock_batches": batches,
        "total_stock": product.stock_level
    })


# ----------------------------------------------------------------------
# POST /api/v1/products → create new product
# name: String (required)
# price: Integer (required)
# brand: String (optional)
# category_id: Integer (optional)
# min_stock_level: Integer (optional)
# details: String (optional)
# product_image: File (optional, multipart/form-data)
# stock_level: Integer (optional, creates initial batch)
# expiration_date: String YYYY-MM-DD (optional)
# added_by: Integer (optional)
# ----------------------------------------------------------------------
@bp.route('', methods=['POST'])
def create_product():

    # Determine if the request is form-data or JSON
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    # Validate required fields
    if not data.get('name'):
        return jsonify({"errors": ["Product name is required"]}), 400

    price = extract_int(data.get('price'))
    if price is None:
        return jsonify({"errors": ["Price must be a number"]}), 400

    category_id = None
    if data.get('category_id'):
        category_id = extract_int(data['category_id'])
        if category_id and not Category.query.get(category_id):
            return jsonify({"errors": ["Invalid category ID"]}), 400

    # Handle product image
    image_blob = get_image_blob()

    # Create product
    product = Product(
        name=data['name'],
        brand=data.get('brand'),
        price=price,
        category_id=category_id,
        min_stock_level=extract_int(data.get('min_stock_level'), 10),
        product_image=image_blob,
        details=data.get('details')
    )

    db.session.add(product)
    db.session.commit()
    
    # Create initial stock batch if stock_level provided
    initial_stock = extract_int(data.get('stock_level'), 0)
    if initial_stock > 0:
        batch = StockBatch (
            product_id = product.id,
            quantity = initial_stock,
            expiration_date = parse_date(data.get('expiration_date')),
            added_at = datetime.now(timezone.utc),
            added_by=extract_int(data.get('added_by')) or API_USER_ID       # default to API user
        )
        db.session.add(batch)
        db.session.commit()
        include_batches=True

    return jsonify(product.to_dict(include_image=True, include_batches=include_batches)), 201


# ----------------------------------------------------------------------
# POST /api/v1/products/<product_id>/stock_batches → add stock batch
# quantity: Integer (required)
# expiration_date: String YYYY-MM-DD (required)
# added_by: Integer (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['POST'])
def add_stock_batch(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    quantity = extract_int(data.get('quantity'))
    if not quantity or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    expiration_date = parse_date(data.get('expiration_date'))
    if not expiration_date:
        return jsonify({"error": "Expiration date is required (YYYY-MM-DD)"}), 400

    added_by = extract_int(data.get('added_by')) or API_USER_ID     # default to API user
    
    batch = StockBatch(
        product_id=product.id,
        quantity=quantity,
        expiration_date=expiration_date,
        added_at=datetime.now(timezone.utc),
        added_by=added_by
    )

    db.session.add(batch)
    db.session.commit()

    return jsonify({
        "message": "Stock batch added",
        "product_id": product.id,
        "batch": batch.to_dict(),
        "new_stock_level": product.stock_level
    }), 201
    
# ----------------------------------------------------------------------
# PUT /api/v1/products/<int:id> → Replace a product
# name: String (required)
# price: Integer (required)
# brand: String (optional)
# category_id: Integer (optional)
# min_stock_level: Integer (optional)
# details: String (optional)
# stock_level: Integer (optional, replaces all batches)
# expiration_date: String YYYY-MM-DD (optional)
# added_by: Integer (optional)
# product_image: File (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>', methods=['PUT'])
def replace_product(product_id):
    product = Product.query.get_or_404(product_id)

    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})
   
    # Product name is required
    if 'name' not in data:
        return jsonify({"errors": ["Product name is required for PUT"]}), 400

    # Price validation
    price = extract_int(data.get('price'))
    if price is None:
        return jsonify({"errors": ["Price must be a number"]}), 400

    # Category validation
    category_id = None
    if 'category_id' in data:
        category_id = extract_int(data['category_id'])
        if category_id and not Category.query.get(category_id):
            return jsonify({"errors": ["Invalid category ID"]}), 400

    # Update product core fields
    product.name = data['name']
    product.brand = data.get('brand')
    product.price = price
    product.category_id = category_id
    product.min_stock_level = extract_int(data.get('min_stock_level'), product.min_stock_level)
    product.details = data.get('details', product.details)

    # Handle stock update via new StockBatch
    for batch in product.stock_batches:
        db.session.delete(batch)
    
    new_stock = extract_int(data.get('stock_level'))
    if new_stock is not None and new_stock > 0:
        batch = StockBatch(
            product_id = product.id,
            quantity = new_stock, 
            expiration_date = parse_date(data.get('expiration_date')),
            added_at = datetime.now(timezone.utc),
            added_by = extract_int(data.get('added_by')) or API_USER_ID
        )
        db.session.add(batch)
        
    # Image handling
    new_image = get_image_blob()
    if new_image is not None:
        product.image_blob = new_image

    db.session.commit()
    
    # Log activity
    ActivityLogger.log_api_activity(
        method='PUT',
        target_entity='product',
        user_id=data.get('added_by') or API_USER_ID,
        details=f"Replaced product id={product.id}, name={product.name}"
    )
    
    return jsonify(product.to_dict(include_image=True, include_batches=True))


# ----------------------------------------------------------------------
# PATCH /api/v1/products/<int:id> → edit product details
# name: String (optional)
# price: Integer (optional)
# category_id: Integer (optional)
# brand: String (optional)
# min_stock_level: Integer (optional)
# details: String (optional)
# stock_level: Integer (optional, adds a new batch)
# expiration_date: String YYYY-MM-DD (optional)
# added_by: Integer (optional)
# product_image: File (optional)
# ----------------------------------------------------------------------   
@bp.route('/<int:id>', methods=['PATCH'])
def patch_product(id):
    product = Product.query.get_or_404(id)
    is_form = request.content_type and 'multipart/form-data' in request.content_type
    data = request.form.to_dict() if is_form else (request.get_json() or {})

    # Update basic fields if provided
    if 'name' in data and not data['name']:
        return jsonify({"errors": ["Product name cannot be empty"]}), 400

    if 'price' in data:
        price = extract_int(data['price'])
        if price is None:
            return jsonify({"errors": ["Price must be a number"]}), 400
        product.price = price

    if 'category_id' in data:
        cat_id = extract_int(data['category_id'])
        if cat_id and not Category.query.get(cat_id):
            return jsonify({"errors": ["Invalid category ID"]}), 400
        product.category_id = cat_id

    # Update optional fields
    for field in ('brand', 'min_stock_level', 'details'):
        if field in data:
            setattr(product, field, data[field])
            
    # Handle stock update via new StockBatch
    if 'stock_level' in data:
        qty = extract_int(data['stock_level'])
        if qty is not None and qty > 0:
            batch = StockBatch(
                product_id = product.id,
                quantity = qty, 
                expiration_date = parse_date(data.get('expiration_date')),
                added_at = datetime.now(timezone.utc),
                added_by = extract_int(data.get('added_by')) or API_USER_ID                  
            )
            db.session.add(batch)


    # Image update (replace only if sent)
    new_image = get_image_blob()
    if new_image is not None:
        product.image_blob = new_image
        
    db.session.commit()
    
    changed_fields = [
        k for k in ('name', 'price', 'brand', 'category_id', 'min_stock_level', 'details')
        if k in data
    ]
    if 'stock_level' in data:
        changed_fields.append("stock_level")

    # SAFE LOGGING
    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='product',
        user_id=data.get('added_by') or API_USER_ID,
        details=f"Updated product id={product.id}: {', '.join(changed_fields)}"
    )
    
    return jsonify(product.to_dict(include_image=True, include_batches=True))
        
# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id> → remove stock
# quantity: Integer (required)
# reason: String (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['PATCH'])
def remove_stock_batch(product_id, batch_id):
    product = Product.query.get_or_404(product_id)
    batch = StockBatch.query.filter_by(id=batch_id, product_id=product_id).first_or_404()

    data = request.get_json() or {}
    remove_qty = extract_int(data.get('quantity'))
    reason = data.get('reason', 'No reason provided')

    if not remove_qty or remove_qty <= 0:
        return jsonify({"error": "Quantity to remove must be positive"}), 400
    if remove_qty > batch.quantity:
        return jsonify({"error": "Cannot remove more than batch quantity"}), 400

    batch.quantity -= remove_qty
    batch.reason = reason
    db.session.commit()

    return jsonify({
        "message": f"{remove_qty} units removed from batch {batch.id}",
        "reason": reason,
        "batch": batch.to_dict(),
        "new_stock_level": product.stock_level
    })

# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id> → edit batch (no quantity change)
# Attributes (all optional):
#   expiration_date: String (YYYY-MM-DD)
#   added_by: Integer (optional)
#   reason: String (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['PATCH'])
def update_stock_batch_metadata(product_id, batch_id):
    batch = StockBatch.query.filter_by(id=batch_id, product_id=product_id).first_or_404()
    data = request.get_json() or {}

    # Update expiration date
    if "expiration_date" in data:
        batch.expiration_date = parse_date(data.get('expiration_date'))

    # Update added_by
    if "added_by" in data:
        batch.added_by = extract_int(data.get('added_by')) or batch.added_by

    # Update reason
    if "reason" in data:
        batch.reason = data.get('reason') or batch.reason

    db.session.commit()
    return jsonify(batch.to_dict())


# ----------------------------------------------------------------------
# DELETE /api/v1/products/<int:id> → delete product
# ----------------------------------------------------------------------
@bp.route('/<int:id>', methods=['DELETE'])
def delete_product(id):
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or API_USER_ID
    
    product = Product.query.get_or_404(id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    
    # Log deletion
    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='product',
        user_id=user_id,
        details=f"Deleted product id={id}, name={name}"
    )
    
    return jsonify({"message": f"{name} product was deleted successfully from inventory."}), 200

# ----------------------------------------------------------------------
# DELETE /api/v1/products/<product_id>/stock_batches/<batch_id> → delete batch
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['DELETE'])
def delete_stock_batch(product_id, batch_id):
    product = Product.query.get_or_404(product_id)
    batch = StockBatch.query.filter_by(id=batch_id, product_id=product_id).first_or_404()

    db.session.delete(batch)
    db.session.commit()

    return jsonify({
        "message": f"Batch {batch_id} of {product.name} deleted successfully",
        "product_id": product_id
    }), 200