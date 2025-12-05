from flask import Blueprint, request, jsonify
from models.user import User
from models.retailer_metrics import RetailerMetrics
from core.sales_manager import SalesManager
from core.activity_logger import ActivityLogger

bp = Blueprint('metrics', __name__)


# ----------------------------------------------------------------------
# GET /api/v1/retailer/<user_id> → Get retailer metrics
# Returns: current_streak, daily_quota, sales_today, total_sales
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>', methods=['GET'])
def get_retailer_metrics(user_id):
    """Get retailer's current performance metrics"""
    try:
        user  = User.objects(id=user_id).first()
        
        if not user:
            return jsonify({"errors": ["Retailer metrics not found"]}), 404
        
        if user.role not in ['retailer', 'staff']:
            return jsonify({"errors": ["User is not a retailer"]}), 403
        
        performance = SalesManager.get_retailer_performance(user_id)
        
        return jsonify(performance), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to get metrics: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/retailer/leaderboard → Get top performing retailers
# Query params:
#   limit: Integer (optional, default=10)
# ----------------------------------------------------------------------
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
# Body:
#   daily_quota: Float (required) → New daily quota amount
#   updated_by: Integer (optional) → Admin/manager user ID
# ----------------------------------------------------------------------
@bp.route('/<int:user_id>/quota', methods=['PATCH'])
def update_retailer_quota(user_id):
    """Update retailer's daily quota"""
    data = request.get_json() or {}
    
    daily_quota = data.get('daily_quota')
    if daily_quota is None:
        return jsonify({"errors": ["daily_quota is required"]}), 400
    
    try:
        daily_quota = float(daily_quota)
        if daily_quota < 0:
            return jsonify({"errors": ["daily_quota must be non-negative"]}), 400
    except (TypeError, ValueError):
        return jsonify({"errors": ["daily_quota must be a number"]}), 400
    
    try:
        metrics = SalesManager.update_retailer_quota(user_id, daily_quota)
        
        # Log activity
        updated_by = data.get('updated_by')
        ActivityLogger.log_api_activity(
            method='PATCH',
            target_entity='retailer_metrics',
            user_id=updated_by,
            details=f"Updated quota for retailer {user_id} to ${daily_quota:.2f}"
        )
        
        return jsonify({
            'message': 'Quota updated successfully',
            'metrics': metrics.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [str(e)]}), 400


# ----------------------------------------------------------------------
# POST /api/v1/retailer/reset-daily → Reset daily metrics 
# Body:
#   admin_id: Integer (optional) → Admin performing the reset
# ----------------------------------------------------------------------
@bp.route('/reset-daily', methods=['POST'])
def reset_retailer_streak():
    """Reset daily metrics for all retailers (called at midnight)"""
    data = request.get_json() or {}
    
    admin_id = data.get('admin_id')
    if not admin_id:
        return jsonify({"errors": ["Admin ID required"]}), 400
    
    try:
        updated_count = SalesManager.reset_daily_metrics()

        # Log activity
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