from flask import Blueprint, request, jsonify

from core.activity_logger import ActivityLogger
from core.inventory_manager import InventoryManager, InventoryError


bp = Blueprint('logs', __name__)


# ----------------------------------------------------------------------
# GET /api/v1/log/product/<id> → logs for specific product
# limit: Integer (optional, default 50)
# ----------------------------------------------------------------------
@bp.route('/product/<int:product_id>', methods=['GET'])
def logs_for_product(product_id):
    """Get all logs for a specific product"""
    limit = request.args.get('limit', 50, type=int)
    logs = ActivityLogger.get_product_logs(product_id, limit=limit)

    return jsonify({
        'product_id': product_id,
        'total': len(logs),
        'logs': [log.to_dict() for log in logs]
    }), 200


# ----------------------------------------------------------------------
# GET /api/v1/log/user/<id> → logs for specific user
# limit: Integer (optional, default 50)
# ----------------------------------------------------------------------
@bp.route('/user/<int:user_id>', methods=['GET'])
def logs_for_user(user_id):
    """Get all logs for a specific user"""
    limit = request.args.get('limit', 50, type=int)
    logs = ActivityLogger.get_user_logs(user_id, limit=limit)

    return jsonify({
        'user_id': user_id,
        'total': len(logs),
        'logs': [log.to_dict() for log in logs]
    }), 200


# ----------------------------------------------------------------------
# GET /api/v1/log → get all product logs with filtering
# action_type: String (optional)
# limit: Integer (optional, default 100)
# ----------------------------------------------------------------------
@bp.route('', methods=['GET'])
def get_all_logs():
    """Get all product logs with optional filtering"""
    action_type = request.args.get('action_type')
    limit = request.args.get('limit', 100, type=int)

    logs = ActivityLogger.get_all_logs(limit=limit, action_type=action_type)

    return jsonify({
        'total': len(logs),
        'action_type_filter': action_type,
        'logs': [log.to_dict() for log in logs]
    }), 200


# ----------------------------------------------------------------------
# GET /api/v1/log/api → get API-wide activity logs
# method: String (optional)
# target_entity: String (optional)
# limit: Integer (optional, default 100)
# ----------------------------------------------------------------------
@bp.route('/api', methods=['GET'])
def get_api_logs():
    """Get API-level activity logs with optional filtering"""
    method = request.args.get('method')
    target_entity = request.args.get('target_entity')
    limit = request.args.get('limit', 100, type=int)

    logs = ActivityLogger.get_api_logs(
        limit=limit,
        method=method,
        target_entity=target_entity
    )

    return jsonify({
        "total": len(logs),
        "method_filter": method,
        "target_entity_filter": target_entity,
        "logs": [log.to_dict() for log in logs]
    }), 200


# ----------------------------------------------------------------------
# POST /api/v1/log/dispose → atomic product disposal
# product_id: Integer (required)
# user_id: Integer (required)
# quantity: Integer (required)
# notes: String (optional)
# ----------------------------------------------------------------------
@bp.route('/dispose', methods=['POST'])
def dispose_product():
    """Dispose product with atomic stock deduction and logging"""
    data = request.get_json() or {}

    product_id = data.get('product_id')
    user_id = data.get('user_id')
    quantity = data.get('quantity')
    notes = data.get('notes', 'Product disposed')

    if not product_id or not user_id or not quantity:
        return jsonify({
            "errors": ["product_id, user_id, and quantity are required"]
        }), 400

    try:
        quantity = int(quantity)
        if quantity <= 0:
            return jsonify({"errors": ["Quantity must be positive"]}), 400
    except (TypeError, ValueError):
        return jsonify({"errors": ["Invalid quantity value"]}), 400

    try:
        # Deduct stock using FEFO
        InventoryManager.deduct_stock_fefo(
            product_id=product_id,
            qty_needed=quantity
        )

        # Log the disposal
        log = ActivityLogger.log_product_action(
            product_id=product_id,
            user_id=user_id,
            action_type='Dispose',
            quantity=quantity,
            notes=notes
        )

        return jsonify({
            "message": "Product disposed successfully",
            "log": log.to_dict()
        }), 201

    except InventoryError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Unexpected error: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# POST /api/v1/log/desktop → log desktop app activity
# user_id: Integer (optional)
# action_type: String (required)
# target_entity: String (optional)
# details: String (optional)
# ----------------------------------------------------------------------
@bp.route('/desktop', methods=['POST'])
def log_desktop_action():
    """Log desktop application activity for centralized audit"""
    data = request.get_json() or {}

    action_type = data.get('action_type')
    if not action_type:
        return jsonify({"errors": ["action_type required"]}), 400

    user_id = data.get('user_id')
    target_entity = data.get('target_entity', 'unknown')
    details = data.get('details')

    try:
        # Log to API activity log
        log = ActivityLogger.log_api_activity(
            method='DESKTOP',
            target_entity=target_entity,
            user_id=user_id,
            source='Desktop App',
            details=details or f"Desktop action: {action_type}"
        )

        return jsonify({
            "message": "Desktop action logged",
            "log": log.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"errors": [f"Failed to log activity: {str(e)}"]}), 500
