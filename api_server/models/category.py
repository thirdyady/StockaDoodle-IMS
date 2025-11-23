from extensions import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    # id of the category
    id = db.Column(db.Integer, primary_key = True)
    
     # name of the category
    name = db.Column(db.String(100), unique = True, nullable = False)
    
    # list of products inside this category
    products = db.relationship('Product', backref='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }