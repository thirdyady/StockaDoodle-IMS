# api_server/models/retailer_metrics.py

from .base import BaseDocument
from mongoengine import IntField, FloatField, DateField, ReferenceField
from .user import User


class RetailerMetrics(BaseDocument):
    meta = {
        'collection': 'retailer_metrics',
        'ordering': ['retailer']
    }

    # which retailer this belongs to
    retailer = ReferenceField(User, unique=True, required=True)

    # how many days in a row the retailer has met quota
    current_streak = IntField(default=0)

    # daily quota
    # Align default with SalesManager's "new metrics" default
    daily_quota = FloatField(default=1000.0)

    # last date a sale was made
    last_sale_date = DateField()

    # today's total sales
    sales_today = FloatField(default=0.0)

    # lifetime sales total
    total_sales = FloatField(default=0.0)

    # lifetime transaction count
    total_transactions = IntField(default=0)

    def to_dict(self):
        retailer_obj = self.retailer

        return {
            'retailer_id': retailer_obj.id if retailer_obj else None,

            # helpful non-breaking extras
            'retailer_name': retailer_obj.full_name if retailer_obj else "Unknown",
            'retailer_username': retailer_obj.username if retailer_obj else None,

            'current_streak': self.current_streak,
            'daily_quota': self.daily_quota,
            'last_sale_date': self.last_sale_date.isoformat() if self.last_sale_date else None,
            'sales_today': self.sales_today,
            'total_sales': self.total_sales,
            'total_transactions': self.total_transactions
        }
