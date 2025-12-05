from mongoengine import StringField, BinaryField
from .base import BaseDocument

class Category(BaseDocument):
    meta = {
        'collection': 'categories',
        'ordering': ['name']
        }
    
    # name of the category, must be unique
    name = StringField(max_length=100, unique=True, required=True)
    
    # optional description of the category
    description = StringField(max_length=255)
    
    # optional image for the category
    category_image = BinaryField()
     
    def to_dict(self, include_image=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
        
        if include_image and self.category_image:
            # return image as binary data
            data['image_data'] = self.category_image
        
        return data
