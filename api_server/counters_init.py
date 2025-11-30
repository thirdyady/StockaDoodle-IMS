""""
One-time script to seed the counters collection.
"""

from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DATABASE_NAME]

initial_counters = [
    {"_id": "user_id", "seq": 1000},
    {"_id": "product_id", "seq": 0},
    {"_id": "category_id", "seq": 0},
    {"_id": "sale_id", "seq": 0},
    {"_id": "stockbatch_id", "seq": 0},
    {"_id": "productlog_id", "seq": 0},
    {"_id": "apiactivitylog_id", "seq": 0},
    {"_id": "retailermetrics_id", "seq": 0},
    {"_id": "saleitem_id", "seq": 0}    
]

for counter in initial_counters:
    db.counters.update_one(
        {"_id": counter["_id"]},
        {"$setOnInsert": counter},
        upsert=True
    )
    
print("All counters initialized successfully")
print("-> Users starts at ID 1001")
print("-> All others starts at 1")
print("\nCounter collection ready for StockaDoodle IMS")