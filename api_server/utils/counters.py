from pymongo import MongoClient, ReturnDocument
from mongoengine import connect, get_db
from config import Config

connect(db=Config.DATABASE_NAME, host=Config.MONGO_URI, alias='default')
_db = get_db()

def get_next_sequence(collection_name: str) -> int:
    """
    Atomically increment and return the next integer ID for a collection
    """
    key = f"{collection_name}_id"
    updated = _db.counters.find_one_and_update(
        {'_id': key},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document = ReturnDocument.AFTER
    )
    return updated['seq']

