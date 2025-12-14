# api_server/routes/metrics.py

from flask import Blueprint, request, jsonify
from models.user import User
from models.retailer_metrics import RetailerMetrics  # kept for compatibility
from core.sales_manager import SalesManager
from core.activity_logger import ActivityLogger

bp = Blueprint('metrics', __name__)


def _normalize_user_id(user_id):
    """
    Supports both:
    - numeric ids (e.g., '1' -> 1)
    - ObjectId-like ids (kept as string)
    """
    if user_id is None:
        return None
    if isinstance(user_id, int):
        return user_id
    s = str(user_id).strip()
    return int(s) if s.isdigit() else s


# ----------------------------------------------------------------------
# GET /api/v1/retailer/<user_id> → Get retailer metrics (DESKTOP EXPECTS THIS)
# ALSO KEEP: /api/v1/<int:user_id> (backward compatible numeric-only)
# ----------------------------------------------------------------------
@bp.route('/retailer/<user_id>', methods=['GET'])
@bp.route('/<int:user_id>', methods=['GET'])  # ✅ prevent hijacking /leaderboard, /health, etc.
def get_retailer_metrics(user_id):
    """Get retailer's current performance metrics"""
    try:
        lookup_id = _normalize_user_id(user_id)

        user = User.objects(id=lookup_id).first()
        if not user:
            return jsonify({"errors": ["Retailer metrics not found"]}), 404

        if (user.role or "").lower() not in ['retailer', 'staff']:
            return jsonify({"errors": ["User is not a retailer"]}), 403

        performance = SalesManager.get_retailer_performance(lookup_id)
        return jsonify(performance), 200

    except Exception as e:
        return jsonify({"errors": [f"Failed to get metrics: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/retailer/leaderboard → Get top performing retailers (DESKTOP USES THIS)
# ALSO KEEP: /api/v1/leaderboard (backward compatible)
# ----------------------------------------------------------------------
@bp.route('/retailer/leaderboard', methods=['GET'])
@bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top performing retailers"""
    try:
        limit = request.args.get('limit', 10, type=int)
        leaderboard = SalesManager.get_leaderboard(limit=limit)

        return jsonify({
            'leaderboard': leaderboard,
            'total_retailers': len(leaderboard)
        }), 200

    except Exception as e:
        return jsonify({"errors": [f"Failed to get leaderboard: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# PATCH /api/v1/retailer/<user_id>/quota → Update retailer daily quota
# ALSO ACCEPT legacy desktop call: /api/v1/metrics/retailer/<user_id>/quota
# ALSO KEEP: /api/v1/<int:user_id>/quota
# Accepts BOTH payload keys:
# - daily_quota (server)
# - new_quota (older desktop client)
# ----------------------------------------------------------------------
@bp.route('/retailer/<user_id>/quota', methods=['PATCH'])
@bp.route('/metrics/retailer/<user_id>/quota', methods=['PATCH'])  # legacy desktop client path
@bp.route('/<int:user_id>/quota', methods=['PATCH'])  # ✅ numeric-only legacy
def update_retailer_quota(user_id):
    """Update retailer's daily quota"""
    data = request.get_json() or {}

    # Accept both keys (prevents breaking either client version)
    daily_quota = data.get('daily_quota', data.get('new_quota'))
    if daily_quota is None:
        return jsonify({"errors": ["daily_quota is required"]}), 400

    try:
        daily_quota = float(daily_quota)
        if daily_quota < 0:
            return jsonify({"errors": ["daily_quota must be non-negative"]}), 400
    except (TypeError, ValueError):
        return jsonify({"errors": ["daily_quota must be a number"]}), 400

    try:
        lookup_id = _normalize_user_id(user_id)

        metrics = SalesManager.update_retailer_quota(lookup_id, daily_quota)

        updated_by = data.get('updated_by')
        ActivityLogger.log_api_activity(
            method='PATCH',
            target_entity='retailer_metrics',
            user_id=updated_by,
            details=f"Updated quota for retailer {lookup_id} to {daily_quota:.2f}"
        )

        metrics_dict = metrics.to_dict() if hasattr(metrics, "to_dict") else metrics

        return jsonify({
            'message': 'Quota updated successfully',
            'metrics': metrics_dict
        }), 200

    except Exception as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# POST /api/v1/retailer/reset-daily → Reset daily metrics
# ALSO KEEP: /api/v1/reset-daily (backward compatible)
# ----------------------------------------------------------------------
@bp.route('/retailer/reset-daily', methods=['POST'])
@bp.route('/reset-daily', methods=['POST'])
def reset_retailer_streak():
    """Reset daily metrics for all retailers (called at midnight)"""
    data = request.get_json() or {}

    admin_id = data.get('admin_id')
    if not admin_id:
        return jsonify({"errors": ["Admin ID required"]}), 400

    try:
        updated_count = SalesManager.reset_daily_metrics()

        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='metrics_reset',
            user_id=admin_id,
            details=f"Reset daily metrics for {updated_count} retailers"
        )

        return jsonify({
            'message': 'Daily metrics was reset successfully',
            'retailers_updated': updated_count
        }), 200

    except Exception as e:
        return jsonify({"errors": [f"Failed to reset streak: {str(e)}"]}), 500


# ======================================================================
# GET /api/v1/metrics/all  (GUI expects this)
# ======================================================================
@bp.route('/metrics/all', methods=['GET'])
def get_all_metrics():
    """
    Returns aggregated global dashboard statistics for ALL users and ALL products.
    """
    try:
        from models.sale import Sale
        from models.user import User
        from models.product import Product
        from models.category import Category
        import datetime

        total_products = Product.objects.count()
        total_categories = Category.objects.count()

        total_sales_amount = 0.0
        today_sales_amount = 0.0
        today = datetime.date.today()

        for sale in Sale.objects():
            amount = float(getattr(sale, "total_amount", 0) or 0)
            total_sales_amount += amount

            try:
                if callable(sale.transaction_date.date) and sale.transaction_date.date() == today:
                    today_sales_amount += amount
            except Exception:
                pass

        retailers_with_sales = User.objects(role__in=["retailer", "staff"]).count()

        return jsonify({
            "total_products": total_products,
            "total_categories": total_categories,
            "total_sales": total_sales_amount,
            "sales_today": today_sales_amount,
            "retailers_with_sales": retailers_with_sales
        }), 200

    except Exception as e:
        return jsonify({"errors": [f"Metrics generation failed: {str(e)}"]}), 500
