import mongoengine
from utils.counters import get_next_sequence

class BaseDocument(mongoengine.Document):
    meta = {
        'abstract': True,
        'allow_inheritance': True
    }
    
    id = mongoengine.IntField(primary_key=True)
    
    def save(self, *args, **kwargs):
        if self.id is None:
            collection_name = self.__class__.__name__.lower()
            self.id = get_next_sequence(collection_name)
        super().save(*args, **kwargs)