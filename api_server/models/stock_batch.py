from extensions import db
from datetime import datetime

class StockBatch(db.Model):
    __tablename__ = 'stock_batches'

    # id of this batch
    id = db.Column(db.Integer, primary_key=True)

    # product this batch belongs to
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # how many items inside this batch
    quantity = db.Column(db.Integer, nullable=False, default=0)

    # when this batch will expire
    expiration_date = db.Column(db.Date)

    # when this batch was added
    added_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # optional: who added this stock
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "added_at": self.added_at.isoformat(),
            "added_by": self.added_by
        }
