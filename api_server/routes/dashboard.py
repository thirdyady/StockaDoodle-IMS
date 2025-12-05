from flask import Blueprint, request, jsonify
from models.product import Product
from models.user import User
from models.sale import Sale
from models.retailer_metrics import RetailerMetrics
from core.inventory_manager import InventoryManager
from core.activity_logger import ActivityLogger

bp = Blueprint('dashboard', __name__)


# ----------------------------------------------------------------------
# GET /api/v1/dashboard/admin → Admin dashboard metrics
# Returns: total_users, total_products, total_sales_count, total_revenue
# ----------------------------------------------------------------------
@bp.route('/admin', methods=['GET'])
def admin_dashboard():
    """Admin Dashboard Metrics"""
    try:
        total_users = User.objects.count()
        total_products = Product.objects.count()
        total_sales = Sale.objects.count()
        
        # Calculate total revenue
        all_sales = Sale.objects()
        total_revenue = sum(sale.total_amount for sale in all_sales)
        
        return jsonify({
            'total_users': total_users,
            'total_products': total_products,
            'total_sales_count': total_sales,
            'total_revenue': round(total_revenue, 2)
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to load admin dashboard: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/dashboard/manager → Manager dashboard metrics
# Returns: low_stock_count, expiring_items_count, recent_logs
# ----------------------------------------------------------------------
@bp.route('/manager', methods=['GET'])
def manager_dashboard():
    """Manager Dashboard Metrics"""
    try:
        # Get low stock count
        low_stock_products = InventoryManager.get_low_stock_products()
        low_stock_count = len(low_stock_products)
        
        # Get expiring items count
        expiring_batches = InventoryManager.get_expiring_batches(days_ahead=7)
        expiring_count = len(expiring_batches)
        
        # Get recent logs (last 10)
        recent_logs = ActivityLogger.get_all_logs(limit=10)
        
        return jsonify({
            'low_stock_count': low_stock_count,
            'expiring_items_count': expiring_count,
            'recent_logs': [log.to_dict() for log in recent_logs],
            'low_stock_products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'current_stock': p.stock_level,
                    'min_stock_level': p.min_stock_level
                }
                for p in low_stock_products[:5]
            ]
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to load manager dashboard: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/dashboard/retailer/<user_id> → Retailer dashboard metrics
# Returns: available_products_count, personal_sales_stats, current_streak
# ----------------------------------------------------------------------
@bp.route('/retailer/<int:user_id>', methods=['GET'])
def retailer_dashboard(user_id):
    """Retailer Dashboard Metrics"""
    try:
        # Verify user exists and is a retailer
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"errors": ["User not found"]}), 404
        
        if user.role not in ['retailer', 'staff']:
            return jsonify({"errors": ["User is not a retailer"]}), 403
        
        # Get available products count
        all_products = Product.objects()
        available_products = sum(1 for p in all_products if p.stock_level > 0)
        
        # Get retailer metrics
        metrics = RetailerMetrics.objects(retailer=user).first()
        
        if not metrics:
            return jsonify({
                'available_products_count': available_products,
                'personal_sales_stats': {
                    'sales_today': 0.0,
                    'total_sales': 0.0,
                    'total_transactions': 0
                },
                'current_streak': 0,
                'daily_quota': 500.0,
                'quota_progress': 0.0
            }), 200
        
        quota_progress = (metrics.sales_today / metrics.daily_quota * 100) if metrics.daily_quota > 0 else 0
        
        return jsonify({
            'available_products_count': available_products,
            'personal_sales_stats': {
                'sales_today': metrics.sales_today,
                'total_sales': metrics.total_sales,
                'total_transactions': metrics.total_transactions
            },
            'current_streak': metrics.current_streak,
            'daily_quota': metrics.daily_quota,
            'quota_progress': round(quota_progress, 2),
            'last_sale_date': metrics.last_sale_date.isoformat() if metrics.last_sale_date else None
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to load retailer dashboard: {str(e)}"]}), 500