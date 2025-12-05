import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv
from core.inventory_manager import InventoryManager
from models.user import User

load_dotenv()


class NotificationService:
    """
    Sends automated alerts to managers for low stock and expiring items.
    Integrates with InventoryManager to monitor stock levels.
    """
    
    # Email configuration from environment
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'alerts@stockadoodle.com')
    
    @staticmethod
    def send_email(to_email, subject, body):
        """
        Send an email notification.
        
        Args:
            to_email (str): Recipient email
            subject (str): Email subject
            body (str): Email body (plain text)
            
        Returns:
            bool: True if sent successfully
        """
        if not NotificationService.SMTP_USERNAME or not NotificationService.SMTP_PASSWORD:
            # For development: print to console
            print(f"\n{'='*60}")
            print(f"EMAIL NOTIFICATION")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}")
            print(f"{'='*60}\n")
            return True
        
        try:
            msg = MIMEMultipart()
            msg['From'] = NotificationService.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(NotificationService.SMTP_HOST, NotificationService.SMTP_PORT)
            server.starttls()
            server.login(NotificationService.SMTP_USERNAME, NotificationService.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"Alert sent to {to_email}: {subject}")
            return True
        except Exception as e:
            print(f"Failed to send alert email: {e}")
            return False
    
    @staticmethod
    def send_low_stock_alerts():
        """
        Send alerts for products below minimum stock level.
        Emails all managers in the system.
        
        Returns:
            dict: Summary of alerts sent
        """
        low_stock_products = InventoryManager.get_low_stock_products()
        
        if not low_stock_products:
            return {'status': 'no_alerts', 'count': 0}
        
        # Get all managers
        managers = User.objects(role__in=['admin', 'manager'])
        
        if not managers:
            return {'status': 'no_recipients', 'count': 0}
        
        # Build alert message
        subject = f"🚨 Low Stock Alert - {len(low_stock_products)} Products Need Attention"
        
        body = f"""
Low Stock Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}

The following products are running low on stock:

"""
        for product in low_stock_products:
            body += f"• {product.name}\n"
            body += f"  Current Stock: {product.stock_level}\n"
            body += f"  Minimum Level: {product.min_stock_level}\n"
            body += f"  Shortage: {product.min_stock_level - product.stock_level}\n\n"
        
        body += """
Please restock these items as soon as possible to avoid stockouts.

--
StockaDoodle Alert System
"""
        
        # Send to all managers
        sent_count = 0
        for manager in managers:
            # In production, use manager's email address
            if hasattr(manager, 'email') and manager.email:
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1
        
        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'products_count': len(low_stock_products),
            'recipients': len(managers)
        }
    
    @staticmethod
    def send_expiration_alerts(days_ahead=7):
        """
        Send alerts for products expiring soon.
        
        Args:
            days_ahead (int): Number of days to look ahead
            
        Returns:
            dict: Summary of alerts sent
        """
        expiring_batches = InventoryManager.get_expiring_batches(days_ahead)
        
        if not expiring_batches:
            return {'status': 'no_alerts', 'count': 0}
        
        # Get all managers
        managers = User.objects(role__in=['admin', 'manager'])
        
        if not managers:
            return {'status': 'no_recipients', 'count': 0}
        
        # Group batches by product
        from models.product import Product
        products_expiring = {}
        for batch in expiring_batches:
            product = Product.objects(id=batch.product.id).first()
            if product:
                if product.name not in products_expiring:
                    products_expiring[product.name] = []
                products_expiring[product.name].append(batch)
        
        # Build alert message
        subject = f"⏰ Expiration Alert - {len(products_expiring)} Products Expiring Soon"
        
        body = f"""
Expiration Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}

The following products have batches expiring within {days_ahead} days:

"""
        for product_name, batches in products_expiring.items():
            body += f"• {product_name}\n"
            for batch in batches:
                exp_date = batch.expiration_date
                if isinstance(exp_date, datetime):
                    exp_date = exp_date.date()
                days_until = (exp_date - date.today()).days
                body += f"  - Batch #{batch.id}: {batch.quantity} units, expires {batch.expiration_date} ({days_until} days)\n"
            body += "\n"
        
        body += """
Please prioritize selling or disposing of these items to minimize losses.

--
StockaDoodle Alert System
"""
        
        # Send to all managers
        sent_count = 0
        for manager in managers:
            if hasattr(manager, 'email') and manager.email:
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1
        
        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'products_count': len(products_expiring),
            'batches_count': len(expiring_batches),
            'recipients': len(managers)
        }
    
    @staticmethod
    def send_daily_summary():
        """
        Send a daily summary combining low stock and expiration alerts.
        
        Returns:
            dict: Summary of notification sent
        """
        low_stock = InventoryManager.get_low_stock_products()
        expiring = InventoryManager.get_expiring_batches(7)
        
        if not low_stock and not expiring:
            return {'status': 'no_alerts', 'message': 'No alerts to send'}
        
        managers = User.objects(role__in=['admin', 'manager'])
        
        if not managers:
            return {'status': 'no_recipients'}
        
        subject = f"📊 Daily Inventory Summary - {date.today().strftime('%Y-%m-%d')}"
        
        body = f"""
Daily Inventory Summary
{date.today().strftime('%A, %B %d, %Y')}

"""
        if low_stock:
            body += f"🚨 LOW STOCK ALERTS: {len(low_stock)} products\n\n"
            for product in low_stock[:5]:  # Show top 5
                body += f"• {product.name}: {product.stock_level}/{product.min_stock_level}\n"
            if len(low_stock) > 5:
                body += f"  ... and {len(low_stock) - 5} more\n"
            body += "\n"
        
        if expiring:
            from models.product import Product
            products_expiring = set()
            for batch in expiring:
                product = Product.objects(id=batch.product.id if hasattr(batch.product, 'id') else batch.product).first()
                if product:
                    products_expiring.add(product.name)

            body += f"⏰ EXPIRATION ALERTS: {len(products_expiring)} products with expiring batches\n\n"
            for batch in expiring[:5]:  # Show top 5
                product = Product.objects(id=batch.product.id if hasattr(batch.product, 'id') else batch.product).first()
                if product:
                    exp_date = batch.expiration_date
                    if isinstance(exp_date, datetime):
                        exp_date = exp_date.date()
                    days_until = (exp_date - date.today()).days
                    body += f"• {product.name}: Batch #{batch.id} expires in {days_until} days\n"
            if len(expiring) > 5:
                body += f"  ... and {len(expiring) - 5} more batches\n"
        
        body += """

Please review the full reports in the StockaDoodle system.

--
StockaDoodle Alert System
"""
        
        sent_count = 0
        for manager in managers:
            if hasattr(manager, 'email') and manager.email:
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1
        
        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'low_stock_count': len(low_stock),
            'expiring_count': len(expiring)
        }