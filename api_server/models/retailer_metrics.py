from extensions import db
from datetime import date, datetime, timezone

class RetailerMetrics(db.Model):
    __tablename__ = 'retailer_metrics'

    # id of the retailer metrics entry
    id = db.Column(db.Integer, primary_key=True)

    # which retailer this belongs to
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # how many days in a row the retailer has met quota
    current_streak = db.Column(db.Integer, default=0, nullable=False)

    # daily quota
    daily_quota = db.Column(db.Float, default=0.0, nullable=False)

    # last date a sale was made
    last_sale_date = db.Column(db.Date, nullable=True)

    # today's total sales
    sales_today = db.Column(db.Float, default=0.0, nullable=False)

    # lifetime sales total
    total_sales = db.Column(db.Float, default=0.0, nullable=False)

    # lifetime transaction count
    total_transactions = db.Column(db.Integer, default=0, nullable=False)

    def to_dict(self):
        return {
            'retailer_id': self.retailer_id,
            'current_streak': self.current_streak,
            'daily_quota': self.daily_quota,
            'last_sale_date': self.last_sale_date.isoformat() if self.last_sale_date else None,
            'sales_today': self.sales_today,
            'total_sales': self.total_sales,
            'total_transactions': self.total_transactions
        }
