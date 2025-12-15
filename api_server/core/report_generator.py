# core/report_generator.py

from models.product import Product
from models.category import Category
from models.sale import Sale
from models.user import User
from models.retailer_metrics import RetailerMetrics
from models.product_log import ProductLog
from models.stock_batch import StockBatch
from datetime import datetime, date, timedelta


class ReportGenerator:
    """
    Generates all 7 required system reports for StockaDoodle.
    Provides data for managerial decision-making and system auditing.
    """

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------
    @staticmethod
    def _date_to_start_datetime(d: date):
        return datetime.combine(d, datetime.min.time())

    @staticmethod
    def _date_to_end_datetime(d: date):
        return datetime.combine(d, datetime.max.time())

    # ------------------------------------------------------------
    # REPORT 1
    # ------------------------------------------------------------
    @staticmethod
    def sales_performance_report(start_date=None, end_date=None):
        """
        Report 1: Sales Performance Report for a Selected Date Range

        Shows: Report ID, Date Range, Product Name, Quantity Sold,
               Total Price, Retailer Name, Total Income
        """
        sales = Sale.objects()

        # If no start_date provided, fetch the first sale date
        if not start_date:
            first_sale = sales.order_by('created_at').first()
            start_date = first_sale.created_at.date() if first_sale else None

        # If no end_date provided, fetch the last sale date
        if not end_date:
            last_sale = sales.order_by('-created_at').first()
            end_date = last_sale.created_at.date() if last_sale else None

        if start_date:
            sales = sales.filter(created_at__gte=ReportGenerator._date_to_start_datetime(start_date))
        if end_date:
            sales = sales.filter(created_at__lte=ReportGenerator._date_to_end_datetime(end_date))

        sales = sales.order_by('-created_at')

        results = []
        for sale in sales:
            retailer = User.objects(id=sale.retailer_id).first()

            for item in (sale.items or []):
                product = Product.objects(id=item.product_id).first()

                qty = int(item.quantity or 0)
                line_total = float(item.line_total or 0)

                results.append({
                    'sale_id': sale.id,
                    'date': sale.created_at.isoformat(),
                    'product_name': product.name if product else 'Unknown',
                    'quantity_sold': qty,
                    'total_price': line_total,
                    'retailer_name': retailer.full_name if retailer else 'Unknown'
                })

        total_income = sum(float(r.get('total_price') or 0) for r in results)
        total_quantity = sum(int(r.get('quantity_sold') or 0) for r in results)
        unique_sales = len(set(r['sale_id'] for r in results))

        return {
            'report_id': 1,
            'report_name': 'Sales Performance Report',
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'sales': results,
            'summary': {
                'total_income': round(total_income, 2),
                'total_quantity_sold': total_quantity,
                'total_transactions': unique_sales
            }
        }

    # ------------------------------------------------------------
    # REPORT 2
    # ------------------------------------------------------------
    @staticmethod
    def category_distribution_report():
        """
        Report 2: Category Distribution Report

        Shows: Category Name, Number of Products,
               Total Stock Quantity, Percentage Share
        """
        categories = list(Category.objects())

        all_products = list(Product.objects())
        total_stock = sum(int(p.stock_level or 0) for p in all_products)

        category_data = []
        categorized_product_ids = set()

        for category in categories:
            products = list(Product.objects(category_id=category.id))
            for p in products:
                categorized_product_ids.add(p.id)

            products_count = len(products)
            category_stock = sum(int(p.stock_level or 0) for p in products)
            percentage = (category_stock / total_stock * 100) if total_stock > 0 else 0

            category_data.append({
                'category_id': category.id,
                'category_name': category.name,
                'number_of_products': products_count,
                'total_stock_quantity': category_stock,
                'percentage_share': round(percentage, 2)
            })

        # Optional but useful: include uncategorized bucket
        uncategorized_products = [p for p in all_products if not p.category_id]
        if uncategorized_products:
            uncategorized_stock = sum(int(p.stock_level or 0) for p in uncategorized_products)
            percentage = (uncategorized_stock / total_stock * 100) if total_stock > 0 else 0

            category_data.append({
                'category_id': None,
                'category_name': 'Uncategorized',
                'number_of_products': len(uncategorized_products),
                'total_stock_quantity': uncategorized_stock,
                'percentage_share': round(percentage, 2)
            })

        return {
            'report_id': 2,
            'report_name': 'Category Distribution Report',
            'categories': category_data,
            'summary': {
                'total_categories': len(categories),
                'total_stock': total_stock
            }
        }

    # ------------------------------------------------------------
    # REPORT 3
    # ------------------------------------------------------------
    @staticmethod
    def retailer_performance_report():
        """
        Report 3: Retailer Performance Report

        Shows: Retailer Name, User ID, Daily Quota Target,
               Current Sales, Streak Count
        """
        retailers = list(User.objects(role__in=['retailer', 'staff']))

        performance_data = []
        for retailer in retailers:
            metrics = RetailerMetrics.objects(retailer=retailer).first()

            if not metrics:
                # Provide safe defaults so the report is complete
                metrics_data = {
                    'daily_quota': 1000.0,
                    'sales_today': 0.0,
                    'current_streak': 0,
                    'total_sales': 0.0
                }
            else:
                metrics_data = {
                    'daily_quota': float(metrics.daily_quota or 0),
                    'sales_today': float(metrics.sales_today or 0),
                    'current_streak': int(metrics.current_streak or 0),
                    'total_sales': float(metrics.total_sales or 0)
                }

            daily_quota = metrics_data['daily_quota']
            sales_today = metrics_data['sales_today']
            quota_progress = (sales_today / daily_quota * 100) if daily_quota > 0 else 0

            performance_data.append({
                'retailer_name': retailer.full_name,
                'user_id': retailer.id,
                'daily_quota': daily_quota,
                'current_sales': sales_today,
                'quota_progress': round(quota_progress, 2),
                'streak_count': metrics_data['current_streak'],
                'total_sales': metrics_data['total_sales'],
                'has_profile_pic': retailer.user_image is not None
            })

        performance_data.sort(key=lambda x: (x['streak_count'], x['total_sales']), reverse=True)

        return {
            'report_id': 3,
            'report_name': 'Retailer Performance Report',
            'retailers': performance_data,
            'summary': {
                'total_retailers': len(retailers),
                'active_today': len([r for r in performance_data if (r.get('current_sales') or 0) > 0])
            }
        }

    # ------------------------------------------------------------
    # REPORT 4
    # ------------------------------------------------------------
    @staticmethod
    def low_stock_and_expiration_alert_report(days_ahead=7):
        """
        Report 4: Low-Stock and Expiration Alert Report
        """
        products = Product.objects()
        alerts = []

        cutoff_date = date.today() + timedelta(days=int(days_ahead or 7))

        for product in products:
            stock = int(product.stock_level or 0)
            alert_status = []

            if stock < int(product.min_stock_level or 0):
                alert_status.append("OUT_OF_STOCK" if stock == 0 else "LOW_STOCK")

            expiring_batches = StockBatch.objects(
                product_id=product.id,
                expiration_date__lte=cutoff_date,
                expiration_date__ne=None,
                quantity__gt=0
            )

            if expiring_batches.count() > 0:
                alert_status.append("EXPIRING_SOON")
                earliest_expiry = min(batch.expiration_date for batch in expiring_batches)
            else:
                earliest_expiry = None

            if alert_status:
                alerts.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_stock': stock,
                    'min_stock_level': product.min_stock_level,
                    'expiration_date': earliest_expiry.isoformat() if earliest_expiry else None,
                    'alert_status': ', '.join(alert_status),
                    'severity': 'CRITICAL' if 'OUT_OF_STOCK' in alert_status else 'WARNING'
                })

        return {
            'report_id': 4,
            'report_name': 'Low-Stock and Expiration Alert Report',
            'alerts': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['severity'] == 'CRITICAL']),
                'warning_alerts': len([a for a in alerts if a['severity'] == 'WARNING'])
            }
        }

    # ------------------------------------------------------------
    # REPORT 5
    # ------------------------------------------------------------
    @staticmethod
    def managerial_activity_log_report(start_date=None, end_date=None):
        """
        Report 5: Managerial Activity Log Report
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        start_datetime = ReportGenerator._date_to_start_datetime(start_date)
        end_datetime = ReportGenerator._date_to_end_datetime(end_date)

        all_logs = ProductLog.objects(
            log_time__gte=start_datetime,
            log_time__lte=end_datetime
        ).order_by('-log_time')

        results = []
        unique_managers = set()

        for log in all_logs:
            user = log.user  # ProductLog.user is a ReferenceField(User)

            if not user:
                continue

            if user.role not in ['admin', 'manager']:
                continue

            product = Product.objects(id=log.product_id).first()

            results.append({
                'log_id': log.id,
                'product_name': product.name if product else 'Unknown',
                'action_performed': log.action_type,
                'manager_id': user.id,
                'manager_name': user.full_name,
                'date_time': log.log_time.isoformat(),
                'notes': log.notes
            })
            unique_managers.add(user.id)

        return {
            'report_id': 5,
            'report_name': 'Managerial Activity Log Report',
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'logs': results,
            'summary': {
                'total_actions': len(results),
                'unique_managers': len(unique_managers)
            }
        }

    # ------------------------------------------------------------
    # REPORT 6
    # ------------------------------------------------------------
    @staticmethod
    def detailed_sales_transaction_report(start_date=None, end_date=None):
        """
        Report 6: Detailed Sales Transaction Report
        """
        sales = Sale.objects()

        # Consistent defaulting with Report 1 (optional but helpful)
        if not start_date:
            first_sale = sales.order_by('created_at').first()
            start_date = first_sale.created_at.date() if first_sale else None

        if not end_date:
            last_sale = sales.order_by('-created_at').first()
            end_date = last_sale.created_at.date() if last_sale else None

        if start_date:
            sales = sales.filter(created_at__gte=ReportGenerator._date_to_start_datetime(start_date))
        if end_date:
            sales = sales.filter(created_at__lte=ReportGenerator._date_to_end_datetime(end_date))

        sales = sales.order_by('-created_at')

        transactions = []
        total_revenue = 0.0
        total_items = 0

        for sale in sales:
            retailer = User.objects(id=sale.retailer_id).first()

            for item in (sale.items or []):
                product = Product.objects(id=item.product_id).first()

                qty = int(item.quantity or 0)
                line_total = float(item.line_total or 0)
                unit_price = (line_total / qty) if qty > 0 else 0.0

                transaction_data = {
                    'sale_id': sale.id,
                    'transaction_time': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'product_id': item.product_id,
                    'product_name': product.name if product else 'Unknown Product',
                    'product_brand': product.brand if product else '',
                    'quantity_sold': qty,
                    'unit_price': round(unit_price, 2),
                    'line_total': line_total,
                    'retailer_id': sale.retailer_id,
                    'retailer_name': retailer.full_name if retailer else 'Unknown'
                }

                transactions.append(transaction_data)
                total_revenue += line_total
                total_items += qty

        return {
            'report_id': 6,
            'report_name': 'Detailed Sales Transaction Report',
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_transactions': len(transactions),
                'total_sales_count': len(set(t['sale_id'] for t in transactions)),
                'total_revenue': round(total_revenue, 2),
                'total_items_sold': total_items
            },
            'transactions': transactions
        }

    # ------------------------------------------------------------
    # REPORT 7
    # ------------------------------------------------------------
    @staticmethod
    def user_accounts_report():
        """
        Report 7: User Accounts Report
        """
        users = User.objects().order_by('full_name')

        return {
            'report_id': 7,
            'report_name': 'User Accounts Report',
            'users': [
                {
                    'user_id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role,
                    'email': user.email,
                    'account_status': 'Active' if getattr(user, "is_active", True) else 'Inactive',
                    'created_at': user.created_at.isoformat() if getattr(user, "created_at", None) else None,
                    'has_profile_pic': user.user_image is not None
                }
                for user in users
            ],
            'summary': {
                'total_users': users.count(),
                'admins': User.objects(role='admin').count(),
                'managers': User.objects(role='manager').count(),
                'retailers': User.objects(role__in=['retailer', 'staff']).count()
            }
        }
