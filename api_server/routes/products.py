from flask import Blueprint, request, jsonify
from api_server.app import db
from models.product import Product
from models.category import Category
import base64

bp = Blueprint('products', __name__)

def validate_product (data, partial = False):
    errors = []
    
    if not partial or 'name' in data:
        if not data.get('name'): errors.append("Product name is required")
        if data.get('name') and len(data['name']) > 120: errors.append("Product name too long")
    
    if not partial or 'price' in data:
        try:
            float(data.get('price', 0))
        except (ValueError, TypeError):
            errors.append("Price must be a number")
    return errors

# Retrieving all products
@bp.route('', method = ['GET'])
def list_product():
    search = request.args.get('search')
    category_id = request.args.get('category_id')
    include_image = request.args.get('include_image') == 'true'
    
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))     
    if category_id:
        query = query.filter_by(category_id=category_id)    
        
    products = query.all()
    return jsonify([
        p.to_dict(include_image) for p in products
    ])
    
    
# Retrieving a product based on ID 
@bp.route('/int:id', methods=[('GET')])
def get_product(id):
    product = Product.query.get_or_404(id)
    include_image = request.get.args('include_image') == 'true'
    return jsonify(product.to_dict(include_image))

# Create a product
@bp.route('int:id', methods=(['POST']))
def create_product():
    data = request.get_json or {}
    errors = validate_product(data)
    if errors:
        return jsonify ({"Errors": errors}), 400
    
    if data.get('category_id') and not Category.query.get(data['category_id']):
        return jsonify ({"Error": "Invalid Category ID"}), 400
    
    image_blob = None
    if data.get('image_base64'):
        try:
            image_blob = base64.b64decode(data['image_base64'])
        except:
            return jsonify ({"Error": "Invalid Image"}), 400
        
    product = Product(
        name=data['name'],
        brand=data.get('brand'),
        price=data['price'],
        category_id=data.get('category_id'),
        stock_level=data.get('stock_level', 0),
        min_stock_level=data.get('min_stock_level', 10),
        expiration_date=data.get('expiration_date'),
        image_blob=image_blob
    )
    
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


# Replace a product
@bp.route('/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json() or {}
    errors = validate_product(data, partial=True)
    if errors: return jsonify({"errors": errors}), 400
    
    for field in ['name', 'brand', 'price', 'category_id', 'stock_level', 'min_stock_level', 'expiration_date']:
        if field in data:
            setattr(product, field, data[field])
    
    if 'image_base64' in data:
        product.image_blob = base64.b64decode(data['image_base64']) if data['image_base64'] else None
    
    db.session.commit()
    return jsonify(product.to_dict())

    
# Edit product details
@bp.route('/<int:id>', methods=['PATCH'])
def patch_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json() or {}

    # Validate only fields being patched
    errors = validate_product(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    # Update only supplied fields
    for field in ['name', 'brand', 'price', 'category_id', 'stock_level', 'min_stock_level', 'expiration_date']:
        if field in data:
            setattr(product, field, data[field])

    # Handle image
    if "image_base64" in data:
        product.image_blob = base64.b64decode(data['image_base64']) if data['image_base64'] else None

    db.session.commit()
    return jsonify(product.to_dict())
        

# Delete a product
@bp.route('/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"}), 200