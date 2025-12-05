from flask import Blueprint, request, jsonify
from models.product import Product
from models.category import Category
from models.stock_batch import StockBatch
from models.user import User
from core.inventory_manager import InventoryManager, InventoryError
from core.activity_logger import ActivityLogger
from mongoengine import Q
from mongoengine.errors import DoesNotExist



from utils import get_image_binary, extract_int, parse_date
from datetime import datetime, timezone

bp = Blueprint('products', __name__)

API_USER_ID = 1001  # the dedicated API handler user


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
    args = request.args
    
    sort_by = args.get('sort_by', 'id')
    sort_dir = args.get('sort_dir', 'asc')
    page = int(args.get('page', 1))
    per_page = int(args.get('per_page', 10))
    include_image = args.get('include_image') == 'true'
    search_mode = args.get('search_mode', 'AND').upper()  # AND or OR
    
    filters = []

    # Build filters
    if name := args.get('name'):
        filters.append(Q(name__icontains=name))
    if brand := args.get('brand'):
        filters.append(Q(brand__icontains=brand))
    if category_id := args.get('category_id'):
        filters.append(Q(category=int(category_id)))
        
    for op in ['gt', 'gte', 'lt', 'lte']:
        if price := args.get(f'price_{op}'):
            if price.isdigit():
                filters.append(Q(**{f'price__{op}': int(price)}))


    # Apply AND / OR mode
    query = Product.objects()
    if filters:
        combined = filters[0]
        for f in filters[1:]:
            combined = combined | f if search_mode == "OR" else combined & f
        query = query.filter(combined)


    # Apply sorting
    sort_column = '-' if sort_dir == 'desc' else ''
    query = query.order_by(f'{sort_column}-{sort_by}')

    # Pagination
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
# GET /api/v1/products/<id> → retrieving a product based on ID 
# ----------------------------------------------------------------------    
@bp.route('/<int:id>', methods=['GET'])
def get_product(id):
    include_image = request.args.get('include_image') == 'true'
    include_batches = request.args.get('include_batches') == 'true'
    
    try:
        product = Product.objects.get(id=id).first()
        # return product data with optional image and batch details
        return jsonify(product.to_dict(include_image, include_batches))
    
    except DoesNotExist:
        return jsonify({"errors": ["Product not found"]}), 404



# ----------------------------------------------------------------------
# GET /api/v1/products/<product_id>/stock_batches → list all batches
# product_id: Integer (required)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['GET'])
def list_stock_batches(product_id):
    try:
        product = Product.objects.get(id=product_id)
    except DoesNotExist:
        return jsonify({"errors": ["Product not found"]}), 404
    
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
        if category_id and not Category.objects(id=category_id).first():
            return jsonify({"errors": ["Invalid category ID"]}), 400

    # Handle product image
    image_blob = get_image_binary()

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
    
    product.save()
    
    # Create initial stock batch if stock_level provided
    initial_stock = extract_int(data.get('stock_level'), 0)
    include_batches = False
    if initial_stock > 0:
        batch = StockBatch (
            product_id = product.id,
            quantity = initial_stock,
            expiration_date = parse_date(data.get('expiration_date')),
            added_at = datetime.now(timezone.utc),
            added_by=User.objects(id=extract_int(data.get('added_by')) or API_USER_ID).first(),   # default to API user
            reason="Initial stock"
        )
        batch.save()
        include_batches=True

    user_id = User.objects(id=extract_int(data.get('added_by')) or API_USER_ID).first()
    
    ActivityLogger.log_api_activity(
        method='POST',
        target_entity='product',
        user_id=user_id,
        details=f"Created product '{product.name}' (id={product.id})"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=user_id,
        action_type='Create',
        quantity=initial_stock if initial_stock > 0 else None,
        notes=f"Product created with initial stock: {initial_stock}" if initial_stock > 0 else "Product created"
    )
    
    return jsonify(product.to_dict(include_image=True, include_batches=include_batches)), 201


# ----------------------------------------------------------------------
# POST /api/v1/products/<product_id>/stock_batches → add stock batch
# quantity: Integer (required)
# expiration_date: String YYYY-MM-DD (required)
# added_by: Integer (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches', methods=['POST'])
def add_stock_batch(product_id):
    try:
        product = Product.objects.get(id=product_id).first()
    except DoesNotExist:
        return jsonify({"errors": ["Product not found"]}), 404
    
    data = request.get_json() or {}

    quantity = extract_int(data.get('quantity'))
    if not quantity or quantity <= 0:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    expiration_date = parse_date(data.get('expiration_date'))
    if not expiration_date:
        return jsonify({"error": "Expiration date is required (YYYY-MM-DD)"}), 400

    added_by = User.objects(id=extract_int(data.get('added_by')) or API_USER_ID).first()
    reason = data.get("reason") or "Stock added"
    
    batch = StockBatch(
        product_id=product.id,
        quantity=quantity,
        expiration_date=expiration_date,
        added_at=datetime.now(timezone.utc),
        added_by= User.objects(id=added_by).first(),
        reason=reason
    )

    batch.save()

    ActivityLogger.log_api_activity(
        method='POST',
        target_entity='stock_batch',
        user_id=added_by,
        details=f"Added stock batch: product_id={product.id}, qty={quantity}, exp={expiration_date}"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=added_by,
        action_type='Restock',
        notes=f"{reason}. Expires: {expiration_date}"
    )
    
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

    try:
        product = Product.objects.get(id=product_id).first()
    except DoesNotExist:
        return jsonify ({"errors": ["Product not found"]}), 404
    
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
        if category_id and not Category.objects(id=category_id).first():
            return jsonify({"errors": ["Invalid category ID"]}), 400

    # Update product core fields
    product.name = data['name']
    product.brand = data.get('brand')
    product.price = price
    product.category = category_id
    product.min_stock_level = extract_int(data.get('min_stock_level'), product.min_stock_level)
    product.details = data.get('details', product.details)

    # Handle stock update via new StockBatch
    StockBatch.objects(product=product.id).delete()

    new_stock = extract_int(data.get('stock_level'))
    if new_stock is not None and new_stock > 0:
        batch = StockBatch(
            product_id = product.id,
            quantity = new_stock, 
            expiration_date = parse_date(data.get('expiration_date')),
            added_at = datetime.now(timezone.utc),
            added_by = User.objects(id=extract_int(data.get('added_by')) or API_USER_ID).first(),
            reason="Stock replacement"
            )
        
        batch.save()
        
    # Image handling
    new_image = get_image_binary()
    if new_image is not None:
        product.product_image = new_image

    product.save()
    
    # Log activity
    ActivityLogger.log_api_activity(
        method='PUT',
        target_entity='product',
        user_id=data.get('added_by') or API_USER_ID,
        details=f"Replaced product id={product.id}, name={product.name}"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=data.get('added_by') or API_USER_ID,
        action_type='Edit',
        quantity=new_stock if new_stock else None,
        notes=f"Product replaced. Stock set to {new_stock}" if new_stock else "Product replaced"
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
def patch_product(product_id):
    try: 
        product = Product.objects.get(id=product_id).first()
    except DoesNotExist:
        return jsonify({"errors": ["Product not found"]}), 404
    
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
        if cat_id and not Category.objects(id=cat_id).first():
            return jsonify({"errors": ["Invalid category ID"]}), 400
        product.category_id = cat_id

    # Update optional fields
    if 'name' in data:
        product.name = data['name']
    if 'brand' in data:
        product.brand = data['brand']
    if 'min_stock_level' in data:
        product.min_stock_level = extract_int(data['min_stock_level'], product.min_stock_level)
    if 'details' in data:
        product.details = data['details']
            
    # Handle stock update via new StockBatch
    if 'stock_level' in data:
        qty = extract_int(data['stock_level'])
        if qty is not None and qty > 0:
            batch = StockBatch(
                product_id = product.id,
                quantity = qty, 
                expiration_date = parse_date(data.get('expiration_date')),
                added_at = datetime.now(timezone.utc),
                added_by = User.objects(id=extract_int(data.get('added_by')) or API_USER_ID).first()               
            )
            batch.save()


    # Image update (replace only if sent)
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

    # Log Activity
    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='product',
        user_id=data.get('added_by') or API_USER_ID,
        details=f"Updated product id={product.id}: {', '.join(changed_fields)}"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=data.get('added_by') or API_USER_ID,
        action_type='Edit',
        quantity=extract_int(data.get('stock_level')) if 'stock_level' in data else None,
        notes=f"Updated fields: {', '.join(changed_fields)}"
    )
    
    return jsonify(product.to_dict(include_image=True, include_batches=True))
        
# ----------------------------------------------------------------------
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id> → remove stock
# quantity: Integer (required)
# reason: String (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>', methods=['PATCH'])
def remove_stock_batch(product_id, batch_id):
    try:
        product = Product.objects.get(id=product_id)
    except DoesNotExist:
        return jsonify({"errors": "Product not found"}), 404
    
    try:
        batch = StockBatch.objects.get(id=batch_id, product_id=product_id)
    except DoesNotExist:
        return jsonify({"errors": "Stock Batches not found"}), 404

    data = request.get_json() or {}
    remove_qty = extract_int(data.get('quantity'))
    reason = data.get('reason', 'No reason provided')

    if not remove_qty or remove_qty <= 0:
        return jsonify({"error": "Quantity to remove must be positive"}), 400
    if remove_qty > batch.quantity:
        return jsonify({"error": "Cannot remove more than batch quantity"}), 400

    batch.quantity -= remove_qty
    batch.reason = reason
    batch.save()
    
    # Log activity
    ActivityLogger.log_api_activity(
        method='PATCH',
        target_entity='stock_batch',  # We're modifying a stock batch
        user_id=data.get('added_by') or API_USER_ID,
        details=f"Removed {remove_qty} units from batch {batch.id} of product {product.id}. Reason: {reason}"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=extract_int(data.get('user_id')) or API_USER_ID,
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
# PATCH /api/v1/products/<product_id>/stock_batches/<batch_id> → edit batch (no quantity change)
# Attributes (all optional):
#   expiration_date: String (YYYY-MM-DD)
#   added_by: Integer (optional)
#   reason: String (optional)
# ----------------------------------------------------------------------
@bp.route('/<int:product_id>/stock_batches/<int:batch_id>/metadata', methods=['PATCH'])
def update_stock_batch_metadata(product_id, batch_id):
    try:
        batch = StockBatch.objects.get(id=batch_id, product=product_id)
    except DoesNotExist:
        return jsonify({"errors": ["Stock Batches not found"]}), 404
    
    data = request.get_json() or {}

    # Update expiration date
    if "expiration_date" in data:
        new_date = parse_date(data.get('expiration_date'))
        if not new_date:
            return jsonify({"errors": ["Invalid expiration date"]}), 400
        batch.expiration_date = new_date

    # Update added_by
    if "added_by" in data:
        user_id = extract_int(data.get('added_by'))
        if user_id:
            batch.added_by = User.objects(id=user_id).first()

    # Update reason
    if "reason" in data:
        batch.reason = data.get('reason') or batch.reason
        
    changed_fields = []
    for field in ['expiration_date', 'added_by', 'reason']:
        if field in data:
            changed_fields.append(field)
    
    ActivityLogger.log_product_action(
        product_id=product_id,
        user_id=extract_int(data.get('user_id')) or API_USER_ID,
        action_type='Edit Batch Metadata',
        quantity=None,
        notes=f"Updated batch {batch.id} fields: {', '.join(changed_fields)}"
    )

    batch.save()
    return jsonify(batch.to_dict())


# ----------------------------------------------------------------------
# DELETE /api/v1/products/<int:id> → delete product
# ----------------------------------------------------------------------
@bp.route('/<int:id>', methods=['DELETE'])
def delete_product(id):
    
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id') or API_USER_ID
    try:
        product = Product.objects.get(id=id)
        
    except DoesNotExist:
        return jsonify({"errors":["Product not found"]}), 404
        
    name = product.name
    product.delete()
    
    # Log activity
    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='product',
        user_id=user_id,
        details=f"Deleted product id={id}, name={name}"
    )
    
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
   
    try:
        product = Product.objects.get(id=product_id)
    except DoesNotExist:
        return jsonify({"errors":["Product not found"]}), 404
    
    try:
        batch = StockBatch.objects.get(id=batch_id, product_id=product_id)
    except DoesNotExist:
        return jsonify({"errors": ["Stock Batches not found"]}), 404

    batch.delete()
    
    data = request.get_json(silent=True) or {}
    user_id = extract_int(data.get('user_id')) or API_USER_ID

    ActivityLogger.log_api_activity(
        method='DELETE',
        target_entity='stock_batch',
        user_id=user_id,
        details=f"Deleted stock batch id={batch_id} for product_id={product_id}"
    )
    
    ActivityLogger.log_product_action(
        product_id=product.id,
        user_id=user_id,
        action_type='Delete Stock Batch',
        quantity=batch.quantity,
        notes=f"Deleted batch {batch.id} of {product.name}"
    )

    return jsonify({
        "message": f"Batch {batch_id} of {product.name} deleted successfully",
        "product_id": product_id
    }), 200