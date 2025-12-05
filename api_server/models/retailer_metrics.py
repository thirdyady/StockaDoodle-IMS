from .base import BaseDocument
from mongoengine import IntField, FloatField, DateField, ReferenceField
from .user import User
from datetime import date, datetime, timezone

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
    daily_quota = FloatField(default=0.0)

    # last date a sale was made
    last_sale_date = DateField()

    # today's total sales
    sales_today = FloatField(default=0.0)

    # lifetime sales total
    total_sales = FloatField(default=0.0)

    # lifetime transaction count
    total_transactions = IntField(default=0)

    def to_dict(self):
        return {
            'retailer_id': self.retailer.id if self.retailer else None,
            'current_streak': self.current_streak,
            'daily_quota': self.daily_quota,
            'last_sale_date': self.last_sale_date.isoformat() if self.last_sale_date else None,
            'sales_today': self.sales_today,
            'total_sales': self.total_sales,
            'total_transactions': self.total_transactions
        }
