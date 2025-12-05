from flask import Blueprint, request, jsonify
from core.notification_service import NotificationService
from core.activity_logger import ActivityLogger

bp = Blueprint('notifications', __name__)


# ----------------------------------------------------------------------
# POST /api/v1/notifications/low-stock → Send low stock alerts
# Body:
#   triggered_by: Integer (optional) → User ID who triggered the alert
# ----------------------------------------------------------------------
@bp.route('/low-stock', methods=['POST'])
def send_low_stock_alerts():
    """Send low stock alerts to managers"""
    data = request.get_json() or {}
    
    try:
        result = NotificationService.send_low_stock_alerts()
        
        # Log activity
        triggered_by = data.get('triggered_by')
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='notification',
            user_id=triggered_by,
            details=f"Low stock alerts sent: {result.get('products_count', 0)} products"
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to send alerts: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# POST /api/v1/notifications/expiring → Send expiration alerts
# Body:
#   days_ahead: Integer (optional, default=7)
#   triggered_by: Integer (optional) → User ID who triggered the alert
# ----------------------------------------------------------------------
@bp.route('/expiring', methods=['POST'])
def send_expiration_alerts():
    """Send expiration alerts to managers"""
    data = request.get_json() or {}
    
    days_ahead = data.get('days_ahead', 7)
    
    try:
        days_ahead = int(days_ahead)
    except (TypeError, ValueError):
        return jsonify({"errors": ["days_ahead must be an integer"]}), 400
    
    try:
        result = NotificationService.send_expiration_alerts(days_ahead)
        
        # Log activity
        triggered_by = data.get('triggered_by')
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='notification',
            user_id=triggered_by,
            details=f"Expiration alerts sent: {result.get('batches_count', 0)} batches"
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to send alerts: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# POST /api/v1/notifications/daily-summary → Send daily summary
# Body:
#   triggered_by: Integer (optional) → User ID who triggered the summary
# ----------------------------------------------------------------------
@bp.route('/daily-summary', methods=['POST'])
def send_daily_summary():
    """Send daily inventory summary to managers"""
    data = request.get_json() or {}
    
    try:
        result = NotificationService.send_daily_summary()
        
        # Log activity
        triggered_by = data.get('triggered_by')
        ActivityLogger.log_api_activity(
            method='POST',
            target_entity='notification',
            user_id=triggered_by,
            details=f"Daily summary sent: {result.get('low_stock_count', 0)} low stock, {result.get('expiring_count', 0)} expiring"
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to send summary: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/notifications/history → Get notification history
# Query params:
#   limit: Integer (optional, default=50)
#   notification_type: String (optional) → 'low_stock', 'expiring', 'daily_summary'
# ----------------------------------------------------------------------
@bp.route('/history', methods=['GET'])
def get_notification_history():
    """Get notification history from activity logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        notification_type = request.args.get('notification_type')
        
        # Get API activity logs filtered by notification target
        logs = ActivityLogger.get_api_logs(
            limit=limit,
            target_entity='notification'
        )
        
        # Filter by notification type if specified
        if notification_type:
            logs = [
                log for log in logs
                if notification_type in log.details.lower()
            ]
        
        return jsonify({
            'total': len(logs),
            'notifications': [log.to_dict() for log in logs]
        }), 200
        
    except Exception as e:
        return jsonify({"errors": [f"Failed to get history: {str(e)}"]}), 500