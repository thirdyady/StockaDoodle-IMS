from flask import Blueprint, request, jsonify
from models.sale import Sale
from core.sales_manager import SalesManager, SalesError
from core.inventory_manager import InventoryError
from core.activity_logger import ActivityLogger
from datetime import datetime

bp = Blueprint('sales', __name__)


# ----------------------------------------------------------------------
# POST /api/v1/sales → record atomic sale
# retailer_id: Integer (required)
# items: Array of objects (required)
#   - product_id: Integer
#   - quantity: Integer
#   - line_total: Float
# total_amount: Float (required)
# ----------------------------------------------------------------------
@bp.route('', methods=['POST'])
def record_sale():
    """Record atomic sale with FEFO stock deduction"""
    data = request.get_json() or {}
    
    retailer_id = data.get('retailer_id')
    items = data.get('items')
    total_amount = data.get('total_amount')
    
    if not retailer_id or not items or total_amount is None:
        return jsonify({
            "errors": ["retailer_id, items, and total_amount are required"]
        }), 400
    
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"errors": ["items must be a non-empty array"]}), 400
    
    # Validate items structure
    for idx, item in enumerate(items):
        if 'product_id' not in item or 'quantity' not in item or 'line_total' not in item:
            return jsonify({
                "errors": [f"Item {idx}: product_id, quantity, and line_total are required"]
            }), 400
    
    try:
        sale = SalesManager.record_atomic_sale(retailer_id, items, total_amount)
        
        # Log product actions for each item sold
        from models.product import Product
        for item in items:
            product = Product.objects(id=item['product_id']).first()
            if product:
                ActivityLogger.log_product_action(
                    product_id=product.id,
                    user_id=retailer_id,
                    action_type='Sale',
                    notes=f"Sold via sale #{sale.id}"
                )
        
        return jsonify({
            "message": "Sale recorded successfully",
            "sale": sale.to_dict(include_items=True)
        }), 201
        
    except (InventoryError, SalesError) as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Unexpected error: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/sales/<id> → get single sale
# ----------------------------------------------------------------------
@bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    """Get single sale by ID"""
    sale = SalesManager.get_sale(sale_id)
    if not sale:
        return jsonify({"errors": ["Sale not found"]}), 404
    
    include_items = request.args.get('include_items', 'true') == 'true'
    return jsonify(sale.to_dict(include_items=include_items)), 200


# ----------------------------------------------------------------------
# DELETE /api/v1/sales/<id> → undo sale
# user_id: Integer (required in body) - who is undoing the sale
# ----------------------------------------------------------------------
@bp.route('/<int:sale_id>', methods=['DELETE'])
def undo_sale(sale_id):
    """Undo sale and restore stock"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"errors": ["user_id required in request body"]}), 400
    
    try:
        SalesManager.undo_sale(sale_id, user_id)
        
        ActivityLogger.log_api_activity(
            method='DELETE',
            target_entity='sale',
            user_id=user_id,
            details=f"Undid sale {sale_id}"
        )
        
        return jsonify({
            "message": f"Sale {sale_id} undone successfully, stock restored"
        }), 200
        
    except SalesError as e:
        return jsonify({"errors": [str(e)]}), 400
    
    except Exception as e:
        return jsonify({"errors": [f"Unexpected error: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/sales/reports → sales report
# start: String YYYY-MM-DD (optional)
# end: String YYYY-MM-DD (optional)
# retailer_id: Integer (optional)
# ----------------------------------------------------------------------
@bp.route('/reports', methods=['GET'])
def sales_report():
    """Generate sales report for date range"""
    start = request.args.get('start')
    end = request.args.get('end')
    retailer_id = request.args.get('retailer_id', type=int)
    
    # Parse dates
    start_date = None
    end_date = None
    
    if start:
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
        except ValueError:
            return jsonify({"errors": ["Invalid start date format. Use YYYY-MM-DD"]}), 400
    
    if end:
        try:
            end_date = datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            return jsonify({"errors": ["Invalid end date format. Use YYYY-MM-DD"]}), 400
    
    try:
        report = SalesManager.get_sales_report(start_date, end_date, retailer_id)
        return jsonify(report), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500