from extensions import db
import base64

class Product(db.Model):
    __tablename__ = 'products'

    # this is the id of the product
    id = db.Column(db.Integer, primary_key=True)

    # name of the product, must be unique
    name = db.Column(db.String(120), unique=True, nullable=False)

    # simple brand text
    brand = db.Column(db.String(50))

    # price as whole number
    price = db.Column(db.Integer, nullable=False)

    # link to a category
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))

    # lowest allowed stock before warning
    min_stock_level = db.Column(db.Integer, default=10)

    # this stores the product picture in bytes
    product_image = db.Column(db.LargeBinary)

    # longer description of the product, optional
    details = db.Column(db.String(250), nullable=True)

    # connection to all stock batches
    stock_batches = db.relationship(
        'StockBatch',
        backref='product',
        lazy=True,
        cascade='all, delete-orphan'
    )

    @property
    def stock_level(self):
        # this adds all batch quantities together
        return sum(batch.quantity for batch in self.stock_batches)

    def to_dict(self, include_image=False, include_batches=False):
        data = {
            "id": self.id,
            "name": self.name,
            "brand": self.brand or "",
            "price": self.price,
            "category_id": self.category_id,
            "stock_level": self.stock_level,
            "min_stock_level": self.min_stock_level,
            "details": self.details or "",
            "has_image": self.product_image is not None,
        }

        if include_image and self.product_image:
            # send image as base64 string if needed
            data["image_base64"] = base64.b64encode(self.product_image).decode("utf-8")

        if include_batches:
            # include the list of all stock batches
            data["batches"] = [b.to_dict() for b in self.stock_batches]

        return data
