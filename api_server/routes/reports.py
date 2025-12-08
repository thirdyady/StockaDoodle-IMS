# api_server/routes/reports.py

from flask import Blueprint, request, jsonify, send_file
from core.report_generator import ReportGenerator
from core.pdf_report_generator import PDFReportGenerator
from datetime import datetime

# Initialize PDF generator
pdf_generator = PDFReportGenerator()

bp = Blueprint('reports', __name__)


# -------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------
def _parse_date_param(value: str | None, label: str):
    """
    Parse YYYY-MM-DD string into date.
    Returns None if value is falsy.
    Raises ValueError with a clean message if format is invalid.
    """
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid {label} format. Use YYYY-MM-DD")


def _get_date_range_from_args():
    start = request.args.get('start_date')
    end = request.args.get('end_date')
    start_date = _parse_date_param(start, "start_date")
    end_date = _parse_date_param(end, "end_date")
    return start_date, end_date


# ----------------------------------------------------------------------
# GET /api/v1/reports/sales-performance → Report 1: Sales Performance
# Query params:
#   start_date: String (optional) YYYY-MM-DD
#   end_date: String (optional) YYYY-MM-DD
# ----------------------------------------------------------------------
@bp.route('/sales-performance', methods=['GET'])
def sales_performance_report():
    """Report 1: Sales Performance Report for Selected Date Range"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report = ReportGenerator.sales_performance_report(start_date, end_date)
        return jsonify(report), 200

    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/category-distribution → Report 2: Category Distribution
# ----------------------------------------------------------------------
@bp.route('/category-distribution', methods=['GET'])
def category_distribution_report():
    """Report 2: Category Distribution Report"""
    try:
        report = ReportGenerator.category_distribution_report()
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/retailer-performance → Report 3: Retailer Performance
# ----------------------------------------------------------------------
@bp.route('/retailer-performance', methods=['GET'])
def retailer_performance_report():
    """Report 3: Retailer Performance Report"""
    try:
        report = ReportGenerator.retailer_performance_report()
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/alerts → Report 4: Low-Stock and Expiration Alerts
# Query params:
#   days_ahead: Integer (optional, default=7)
# ----------------------------------------------------------------------
@bp.route('/alerts', methods=['GET'])
def alerts_report():
    """Report 4: Low-Stock and Expiration Alert Report"""
    try:
        days_ahead = request.args.get('days_ahead', 7, type=int)
        report = ReportGenerator.low_stock_and_expiration_alert_report(days_ahead)
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/managerial-activity → Report 5: Managerial Activity Log
# Query params:
#   start_date: String (optional) YYYY-MM-DD
#   end_date: String (optional) YYYY-MM-DD
# ----------------------------------------------------------------------
@bp.route('/managerial-activity', methods=['GET'])
def managerial_activity_report():
    """Report 5: Managerial Activity Log Report"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report = ReportGenerator.managerial_activity_log_report(start_date, end_date)
        return jsonify(report), 200

    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/transactions → Report 6: Detailed Sales Transactions
# Query params:
#   start_date: String (optional) YYYY-MM-DD
#   end_date: String (optional) YYYY-MM-DD
# ----------------------------------------------------------------------
@bp.route('/transactions', methods=['GET'])
def transactions_report():
    """Report 6: Detailed Sales Transaction Report"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report = ReportGenerator.detailed_sales_transaction_report(start_date, end_date)
        return jsonify(report), 200

    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/user-accounts → Report 7: User Accounts Report
# ----------------------------------------------------------------------
@bp.route('/user-accounts', methods=['GET'])
def user_accounts_report():
    """Report 7: User Accounts Report"""
    try:
        report = ReportGenerator.user_accounts_report()
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate report: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/sales-performance/pdf → Download Report 1 as PDF
# ----------------------------------------------------------------------
@bp.route('/sales-performance/pdf', methods=['GET'])
def download_sales_performance_pdf():
    """Download Sales Performance Report as PDF"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report_data = ReportGenerator.sales_performance_report(start_date, end_date)

        pdf_buffer = pdf_generator.generate_sales_performance_report(report_data)
        filename = f"Sales_Performance_Report_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/category-distribution/pdf → Download Report 2 as PDF
# ----------------------------------------------------------------------
@bp.route('/category-distribution/pdf', methods=['GET'])
def download_category_distribution_pdf():
    """Download Category Distribution Report as PDF"""
    try:
        report_data = ReportGenerator.category_distribution_report()
        pdf_buffer = pdf_generator.generate_category_distribution_report(report_data)

        filename = f"Category_Distribution_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/retailer-performance/pdf → Download Report 3 as PDF
# ----------------------------------------------------------------------
@bp.route('/retailer-performance/pdf', methods=['GET'])
def download_retailer_performance_pdf():
    """Download Retailer Performance Report as PDF"""
    try:
        report_data = ReportGenerator.retailer_performance_report()
        pdf_buffer = pdf_generator.generate_retailer_performance_report(report_data)

        filename = f"Retailer_Performance_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/alerts/pdf → Download Report 4 as PDF
# ----------------------------------------------------------------------
@bp.route('/alerts/pdf', methods=['GET'])
def download_alerts_pdf():
    """Download Low-Stock and Expiration Alert Report as PDF"""
    try:
        days_ahead = request.args.get('days_ahead', 7, type=int)
        report_data = ReportGenerator.low_stock_and_expiration_alert_report(days_ahead)
        pdf_buffer = pdf_generator.generate_alerts_report(report_data)

        filename = f"Alerts_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/managerial-activity/pdf → Download Report 5 as PDF
# ----------------------------------------------------------------------
@bp.route('/managerial-activity/pdf', methods=['GET'])
def download_managerial_activity_pdf():
    """Download Managerial Activity Log Report as PDF"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report_data = ReportGenerator.managerial_activity_log_report(start_date, end_date)
        pdf_buffer = pdf_generator.generate_managerial_activity_report(report_data)

        filename = f"Managerial_Activity_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/transactions/pdf → Download Report 6 as PDF
# ----------------------------------------------------------------------
@bp.route('/transactions/pdf', methods=['GET'])
def download_transactions_pdf():
    """Download Detailed Sales Transaction Report as PDF"""
    try:
        start_date, end_date = _get_date_range_from_args()
        report_data = ReportGenerator.detailed_sales_transaction_report(start_date, end_date)
        pdf_buffer = pdf_generator.generate_transactions_report(report_data)

        filename = f"Sales_Transactions_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({"errors": [str(e)]}), 400
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500


# ----------------------------------------------------------------------
# GET /api/v1/reports/user-accounts/pdf → Download Report 7 as PDF
# ----------------------------------------------------------------------
@bp.route('/user-accounts/pdf', methods=['GET'])
def download_user_accounts_pdf():
    """Download User Accounts Report as PDF"""
    try:
        report_data = ReportGenerator.user_accounts_report()
        pdf_buffer = pdf_generator.generate_user_accounts_report(report_data)

        filename = f"User_Accounts_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"errors": [f"Failed to generate PDF: {str(e)}"]}), 500
