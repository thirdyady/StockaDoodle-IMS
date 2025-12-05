from models.product import Product
from models.category import Category
from models.sale import Sale, SaleItem
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

    @staticmethod
    def sales_performance_report(start_date=None, end_date=None):
        """
        Report 1: Sales Performance Report for a Selected Date Range
        
        Shows: Report ID, Date Range, Product Name, Quantity Sold, 
               Total Price, Retailer Name, Total Income
        
        Args:
            start_date (date): Start of date range
            end_date (date): End of date range
            
        Returns:
            dict: Report data with sales breakdown and summary
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
            start_datetime = datetime.combine(start_date, datetime.min.time())
            sales = sales.filter(created_at__gte=start_datetime) 
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            sales = sales.filter(created_at__lte=end_datetime) 
        
        # Query sales
        sales = sales.order_by('-created_at')

        results = []
        for sale in sales:
            retailer = User.objects(id=sale.retailer_id).first()
            items = sale.items
            
            for item in items:
                product = Product.objects(id=item.product_id).first()
                results.append({
                    'sale_id': sale.id,
                    'date': sale.created_at.isoformat(),
                    'product_name': product.name if product else 'Unknown',
                    'quantity_sold': item.quantity,
                    'total_price': item.line_total,
                    'retailer_name': retailer.full_name if retailer else 'Unknown'
                })

        total_income = sum(r['total_price'] for r in results)
        total_quantity = sum(r['quantity_sold'] for r in results)
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

    @staticmethod
    def category_distribution_report():
        """
        Report 2: Category Distribution Report
        
        Shows: Report ID, Category Name, Number of Products, 
               Total Stock Quantity, Percentage Share
        
        Returns:
            dict: Category-wise stock distribution
        """
        categories = Category.objects()
        
        # Calculate total stock across all products
        all_products = Product.objects()
        total_stock = sum(product.stock_level for product in all_products)

        category_data = []
        for category in categories:
            products = Product.objects(category_id=category.id)
            products_count = products.count()
            category_stock = sum(p.stock_level for p in products)
            percentage = (category_stock / total_stock * 100) if total_stock > 0 else 0

            category_data.append({
                'category_id': category.id,
                'category_name': category.name,
                'number_of_products': products_count,
                'total_stock_quantity': category_stock,
                'percentage_share': round(percentage, 2)
            })

        return {
            'report_id': 2,
            'report_name': 'Category Distribution Report',
            'categories': category_data,
            'summary': {
                'total_categories': categories.count(),
                'total_stock': total_stock
            }
        }

    @staticmethod
    def retailer_performance_report():
        """
        Report 3: Retailer Performance Report
        
        Shows: Retailer Name, User ID, Daily Quota Target, 
               Current Sales, Streak Count
        
        Returns:
            dict: All retailers with performance metrics
        """
        retailers = User.objects(role__in=['retailer', 'staff'])
        
        performance_data = []
        for retailer in retailers:
            metrics = RetailerMetrics.objects(retailer=retailer).first()
            
            if metrics:
                quota_progress = (metrics.sales_today / metrics.daily_quota * 100) if metrics.daily_quota > 0 else 0
                performance_data.append({
                    'retailer_name': retailer.full_name,
                    'user_id': retailer.id,
                    'daily_quota': metrics.daily_quota,
                    'current_sales': metrics.sales_today,
                    'quota_progress': round(quota_progress, 2),
                    'streak_count': metrics.current_streak,
                    'total_sales': metrics.total_sales,
                    'has_profile_pic': retailer.user_image is not None
                })

        # Sort by streak, then sales
        performance_data.sort(key=lambda x: (x['streak_count'], x['total_sales']), reverse=True)

        return {
            'report_id': 3,
            'report_name': 'Retailer Performance Report',
            'retailers': performance_data,
            'summary': {
                'total_retailers': retailers.count(),
                'active_today': len([r for r in performance_data if r['current_sales'] > 0])
            }
        }

    @staticmethod
    def low_stock_and_expiration_alert_report(days_ahead=7):
        """
        Report 4: Low-Stock and Expiration Alert Report
        
        Shows: Product ID, Product Name, Current Stock, 
               Minimum Stock Level, Expiration Date, Alert Status
        
        Args:
            days_ahead (int): Days to look ahead for expirations
            
        Returns:
            dict: Products needing attention
        """
        products = Product.objects()
        alerts = []

        cutoff_date = date.today() + timedelta(days=days_ahead)

        for product in products:
            stock = product.stock_level
            alert_status = []

            # Low stock check
            if stock < product.min_stock_level:
                if stock == 0:
                    alert_status.append("OUT_OF_STOCK")
                else:
                    alert_status.append("LOW_STOCK")

            # Expiration check
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

    @staticmethod
    def managerial_activity_log_report(start_date=None, end_date=None):
        """
        Report 5: Managerial Activity Log Report
        
        Shows: Log ID, Product Name, Action Performed, 
               User ID of Manager, Date and Time of Action
        
        Args:
            start_date (date): Start date filter
            end_date (date): End date filter
            
        Returns:
            dict: Manager actions log
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()
            
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # Get all product logs from managers/admins
        all_logs = ProductLog.objects(
            log_time__gte=start_datetime,
            log_time__lte=end_datetime
        ).order_by('-log_time')

        results = []
        unique_managers = set()
        
        for log in all_logs:
            if hasattr(log.user, 'id'):  
                user_id = log.user.id  
            else:  
                user_id = log.user  
            user = User.objects(id=user_id).first()
            if user and user.role in ['admin', 'manager']:
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

    @staticmethod
    def detailed_sales_transaction_report(start_date=None, end_date=None):
        """
        Report 6: Detailed Sales Transaction Report
        
        Shows: Sale ID, Product Name, Quantity Sold, 
               Total Price, Retailer Name, Sale Time
        
        Args:
            start_date (date): Start date
            end_date (date): End date
            
        Returns:
            dict: Detailed transaction list
        """
        
        sales = Sale.objects()  
      
        sales = Sale.objects()  
      
        if start_date:  
            sales = sales.filter(created_at__gte=start_date)  
        if end_date:  
            sales = sales.filter(created_at__lte=end_date)  
      
        transactions = []  
        total_revenue = 0.0  
        total_items = 0  
        
        for sale in sales:  
            retailer = User.objects(id=sale.retailer_id).first()  
            
            # Process each embedded item as a separate transaction line  
            for item in sale.items:  
                product = Product.objects(id=item.product_id).first()  
                
                # Calculate unit price from line total and quantity  
                unit_price = item.line_total / item.quantity if item.quantity > 0 else 0  
                
                transaction_data = {  
                    'sale_id': sale.id,  
                    'transaction_time': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),  
                    'product_id': item.product_id,  
                    'product_name': product.name if product else 'Unknown Product',  
                    'product_brand': product.brand if product else '',  
                    'quantity_sold': item.quantity,  
                    'unit_price': round(unit_price, 2),  
                    'line_total': item.line_total,  
                    'retailer_id': sale.retailer_id,  
                    'retailer_name': retailer.full_name if retailer else 'Unknown'  
                }  
                
                transactions.append(transaction_data)  
                total_revenue += item.line_total  
                total_items += item.quantity  
      
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

    @staticmethod
    def user_accounts_report():
        """
        Report 7: User Accounts Report
        
        Shows: User ID, Username, Role, Email Address (if available),
               Account Status, Date Created (approximated)
        
        Returns:
            dict: All user accounts with details
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
                    'account_status': 'Active',  # Extend User model if needed
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