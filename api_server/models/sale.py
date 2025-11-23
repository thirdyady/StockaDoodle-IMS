from extensions import db
from datetime import datetime, timezone

class Sale(db.Model):
    __tablename__ = 'sales'
    
    # id of the sale transaction
    id = db.Column(db.Integer, primary_key=True)
    
    # which retailer made the sale
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # when the sale happened
    created_at = db.Column(db.DateTime(timezone=True), default=lambda:datetime.now(timezone.utcnow), nullable=False)
    
    # full sale amount
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    # list of items inside this sale
    items = db.relationship("SaleItem", backref="sale", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat(),
        }

        if include_items:
            # include every sale item if asked
            data["items"] = [item.to_dict() for item in self.items]

        return data


class SaleItem(db.Model):
    __tablename__ = "sale_items"

    # id of the item inside a sale
    id = db.Column(db.Integer, primary_key=True)

    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"))
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))

    # how many of that item
    quantity = db.Column(db.Integer, default=0)

    # price * qty for that item
    line_total = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "line_total": self.line_total
        }