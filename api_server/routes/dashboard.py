# api_server/routes/dashboard.py

from flask import Blueprint, jsonify
from datetime import datetime, timedelta, timezone

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

        all_sales = Sale.objects()
        total_revenue = sum(float(sale.total_amount or 0) for sale in all_sales)

        return jsonify({
            'total_users': int(total_users),
            'total_products': int(total_products),
            'total_sales_count': int(total_sales),
            'total_revenue': round(float(total_revenue), 2)
        }), 200

    except Exception as e:
        return jsonify({"errors": [f"Failed to load admin dashboard: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/dashboard/manager → Manager dashboard metrics
# Returns:
#   low_stock_count,
#   expiring_items_count,
#   revenue_30d,
#   qty_sold_30d,
#   recent_logs,
#   low_stock_products
# ----------------------------------------------------------------------
@bp.route('/manager', methods=['GET'])
def manager_dashboard():
    """Manager Dashboard Metrics"""
    try:
        # Low stock
        low_stock_products = InventoryManager.get_low_stock_products()
        low_stock_count = len(low_stock_products)

        # Expiring (7 days)
        expiring_batches = InventoryManager.get_expiring_batches(days_ahead=7)
        expiring_count = len(expiring_batches)

        # Revenue + qty sold (last 30 days) — use Sale.created_at (UTC)
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30)

        revenue_30d = 0.0
        qty_sold_30d = 0.0

        sales_30d = Sale.objects(created_at__gte=start, created_at__lte=now)
        for s in sales_30d:
            revenue_30d += float(getattr(s, "total_amount", 0) or 0)
            items = getattr(s, "items", None) or []
            for it in items:
                qty_sold_30d += float(getattr(it, "quantity", 0) or 0)

        # Recent logs (optional, still returned)
        recent_logs = ActivityLogger.get_all_logs(limit=10)

        return jsonify({
            'low_stock_count': int(low_stock_count),
            'expiring_items_count': int(expiring_count),

            # ✅ these 2 keys match your desktop KPI labels
            'revenue_30d': round(float(revenue_30d), 2),
            'qty_sold_30d': int(qty_sold_30d),

            'recent_logs': [log.to_dict() for log in (recent_logs or [])],
            'low_stock_products': [
                {
                    'id': p.id,
                    'name': p.name,
                    'current_stock': p.stock_level,
                    'min_stock_level': p.min_stock_level
                }
                for p in (low_stock_products or [])[:5]
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
        user = User.objects(id=user_id).first()
        if not user:
            return jsonify({"errors": ["User not found"]}), 404

        if user.role not in ['retailer', 'staff']:
            return jsonify({"errors": ["User is not a retailer"]}), 403

        all_products = Product.objects()
        available_products = sum(1 for p in all_products if p.stock_level > 0)

        metrics = RetailerMetrics.objects(retailer=user).first()

        if not metrics:
            return jsonify({
                'available_products_count': int(available_products),
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
            'available_products_count': int(available_products),
            'personal_sales_stats': {
                'sales_today': float(metrics.sales_today),
                'total_sales': float(metrics.total_sales),
                'total_transactions': int(metrics.total_transactions)
            },
            'current_streak': int(metrics.current_streak),
            'daily_quota': float(metrics.daily_quota),
            'quota_progress': round(float(quota_progress), 2),
            'last_sale_date': metrics.last_sale_date.isoformat() if metrics.last_sale_date else None
        }), 200

    except Exception as e:
        return jsonify({"errors": [f"Failed to load retailer dashboard: {str(e)}"]}), 500
