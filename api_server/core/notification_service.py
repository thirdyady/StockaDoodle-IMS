# api_server/core/notification_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta, timezone
import os
from dotenv import load_dotenv

from core.inventory_manager import InventoryManager
from models.user import User
from models.product import Product

load_dotenv()


class NotificationService:
    """
    Sends automated alerts to managers for low stock and expiring items.
    Integrates with InventoryManager to monitor stock levels.

    Assumptions aligned with your models:
    - StockBatch has product_id (IntField), not product ReferenceField.
    """

    # Email configuration from environment
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'alerts@stockadoodle.com')

    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> bool:
        """
        Send an email notification.

        Dev-friendly behavior:
        - If SMTP creds not set, prints to console and returns True.
        """
        if not NotificationService.SMTP_USERNAME or not NotificationService.SMTP_PASSWORD:
            print(f"\n{'='*60}")
            print("EMAIL NOTIFICATION (DEV MODE)")
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
    def _get_managers():
        """Fetch all admin/manager users."""
        return User.objects(role__in=['admin', 'manager'])

    # ------------------------------------------------------------------
    # Low stock alerts
    # ------------------------------------------------------------------
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
            return {'status': 'no_alerts', 'alerts_sent': 0, 'products_count': 0, 'recipients': 0}

        managers = NotificationService._get_managers()

        if not managers:
            return {'status': 'no_recipients', 'alerts_sent': 0, 'products_count': len(low_stock_products), 'recipients': 0}

        subject = f"🚨 Low Stock Alert - {len(low_stock_products)} Products Need Attention"

        body = (
            f"Low Stock Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"The following products are running low on stock:\n\n"
        )

        for product in low_stock_products:
            current = int(getattr(product, "stock_level", 0) or 0)
            min_level = int(getattr(product, "min_stock_level", 0) or 0)
            shortage = max(0, min_level - current)

            body += (
                f"• {product.name}\n"
                f"  Current Stock: {current}\n"
                f"  Minimum Level: {min_level}\n"
                f"  Shortage: {shortage}\n\n"
            )

        body += (
            "Please restock these items as soon as possible to avoid stockouts.\n\n"
            "--\nStockaDoodle Alert System\n"
        )

        sent_count = 0
        for manager in managers:
            if getattr(manager, "email", None):
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1

        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'products_count': len(low_stock_products),
            'recipients': len(managers)
        }

    # ------------------------------------------------------------------
    # Expiration alerts
    # ------------------------------------------------------------------
    @staticmethod
    def send_expiration_alerts(days_ahead=7):
        """
        Send alerts for products expiring soon.

        Args:
            days_ahead (int): Number of days to look ahead

        Returns:
            dict: Summary of alerts sent
        """
        try:
            days_ahead = int(days_ahead)
        except Exception:
            days_ahead = 7

        expiring_batches = InventoryManager.get_expiring_batches(days_ahead)

        if not expiring_batches:
            return {'status': 'no_alerts', 'alerts_sent': 0, 'products_count': 0, 'batches_count': 0, 'recipients': 0}

        managers = NotificationService._get_managers()
        if not managers:
            return {
                'status': 'no_recipients',
                'alerts_sent': 0,
                'products_count': 0,
                'batches_count': len(expiring_batches),
                'recipients': 0
            }

        # Group batches by product name
        products_expiring = {}
        for batch in expiring_batches:
            pid = getattr(batch, "product_id", None)
            if pid is None:
                continue

            product = Product.objects(id=int(pid)).first()
            pname = product.name if product else "Unknown"

            products_expiring.setdefault(pname, []).append(batch)

        subject = f"⏰ Expiration Alert - {len(products_expiring)} Products Expiring Soon"

        body = (
            f"Expiration Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"The following products have batches expiring within {days_ahead} days:\n\n"
        )

        for product_name, batches in products_expiring.items():
            body += f"• {product_name}\n"

            # sort by soonest expiry
            def _exp_key(b):
                return getattr(b, "expiration_date", date.max) or date.max

            for batch in sorted(batches, key=_exp_key):
                exp_date = getattr(batch, "expiration_date", None)
                qty = int(getattr(batch, "quantity", 0) or 0)

                if not exp_date:
                    body += f"  - Batch #{batch.id}: {qty} units, expires N/A\n"
                    continue

                # exp_date is DateField in your model
                try:
                    days_until = (exp_date - date.today()).days
                except Exception:
                    days_until = "?"

                body += f"  - Batch #{batch.id}: {qty} units, expires {exp_date} ({days_until} days)\n"

            body += "\n"

        body += (
            "Please prioritize selling or disposing of these items to minimize losses.\n\n"
            "--\nStockaDoodle Alert System\n"
        )

        sent_count = 0
        for manager in managers:
            if getattr(manager, "email", None):
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1

        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'products_count': len(products_expiring),
            'batches_count': len(expiring_batches),
            'recipients': len(managers)
        }

    # ------------------------------------------------------------------
    # Daily summary
    # ------------------------------------------------------------------
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
            return {
                'status': 'no_alerts',
                'alerts_sent': 0,
                'low_stock_count': 0,
                'expiring_count': 0,
                'recipients': 0
            }

        managers = NotificationService._get_managers()
        if not managers:
            return {
                'status': 'no_recipients',
                'alerts_sent': 0,
                'low_stock_count': len(low_stock),
                'expiring_count': len(expiring),
                'recipients': 0
            }

        subject = f"📊 Daily Inventory Summary - {date.today().strftime('%Y-%m-%d')}"

        body = (
            "Daily Inventory Summary\n"
            f"{date.today().strftime('%A, %B %d, %Y')}\n\n"
        )

        if low_stock:
            body += f"🚨 LOW STOCK ALERTS: {len(low_stock)} products\n\n"
            for product in low_stock[:5]:
                current = int(getattr(product, "stock_level", 0) or 0)
                min_level = int(getattr(product, "min_stock_level", 0) or 0)
                body += f"• {product.name}: {current}/{min_level}\n"
            if len(low_stock) > 5:
                body += f"  ... and {len(low_stock) - 5} more\n"
            body += "\n"

        if expiring:
            product_names = set()
            for batch in expiring:
                pid = getattr(batch, "product_id", None)
                if pid is None:
                    continue
                product = Product.objects(id=int(pid)).first()
                if product:
                    product_names.add(product.name)

            body += f"⏰ EXPIRATION ALERTS: {len(product_names)} products with expiring batches\n\n"

            for batch in expiring[:5]:
                pid = getattr(batch, "product_id", None)
                product = Product.objects(id=int(pid)).first() if pid is not None else None

                exp_date = getattr(batch, "expiration_date", None)
                if exp_date:
                    try:
                        days_until = (exp_date - date.today()).days
                    except Exception:
                        days_until = "?"
                    pname = product.name if product else "Unknown"
                    body += f"• {pname}: Batch #{batch.id} expires in {days_until} days\n"

            if len(expiring) > 5:
                body += f"  ... and {len(expiring) - 5} more batches\n"

        body += (
            "\nPlease review the full reports in the StockaDoodle system.\n\n"
            "--\nStockaDoodle Alert System\n"
        )

        sent_count = 0
        for manager in managers:
            if getattr(manager, "email", None):
                if NotificationService.send_email(manager.email, subject, body):
                    sent_count += 1

        return {
            'status': 'sent',
            'alerts_sent': sent_count,
            'low_stock_count': len(low_stock),
            'expiring_count': len(expiring),
            'recipients': len(managers)
        }
