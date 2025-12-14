# utils/counters.py

import os
from pymongo import ReturnDocument
from mongoengine import connect, get_db
from mongoengine.connection import ConnectionFailure


def _ensure_connection():
    """
    Use existing mongoengine connection if already established by app.py.
    If not, connect using the SAME env logic as app.py (safe fallback).
    """
    try:
        # If already connected, this works
        get_db()
        return
    except Exception:
        pass

    mongo_uri = os.getenv('MONGO_URI') or os.getenv('MONGODB_URI') or 'mongodb://localhost:27017/'
    db_name = os.getenv('DATABASE_NAME', 'stockadoodle')

    # Fallback connect (only if app.py hasn't connected yet)
    connect(db=db_name, host=mongo_uri, alias='default')


def get_next_sequence(collection_name: str) -> int:
    """
    Atomically increment and return the next integer ID for a collection.
    Uses the SAME MongoDB connection as the rest of the app.
    """
    _ensure_connection()
    db = get_db()

    key = f"{collection_name}_id"
    updated = db.counters.find_one_and_update(
        {'_id': key},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return int(updated['seq'])
