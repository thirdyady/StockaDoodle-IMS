from extensions import db
import base64

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(120), nullable = False)
    brand = db.Column(db.String(50))
    price = db.Column(db.Integer, nullable = False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    stock_level = db.Column(db.Integer, default = 0)
    min_stock_level = db.Column (db.Integer, default = 10)
    expiration_date = db.Column(db.Date)
    image_blob = db.Column(db.LargeBinary)
    
    
    def to_dict(self, include_image = False):
        data = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand or "",
            "price": self.price,
            "category_id": self.category_id,
            "stock_level": self.stock_level,
            "min_stock_level": self.min_stock_level,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None
        }
        if include_image and self.image_blob:
            data["image_base64"] = base64.b64encode(self.image_blob).decode('utf-8')
        return data
    
    
    
    