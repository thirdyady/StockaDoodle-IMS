from datetime import datetime

from mongoengine import StringField, DateTimeField, ReferenceField

from .base import BaseDocument
from .user import User


class APIActivityLog(BaseDocument):
    meta = {
        'collection': 'api_activity_logs',
        'ordering': ['-timestamp']
    }

    # http method like POST or GET or DESKTOP
    method = StringField(max_length=10, required=True)

    # the target entity name like product or user
    target_entity = StringField(max_length=50, required=True)

    # optional user responsible for the action
    user = ReferenceField(User, required=False)

    # where the action came from
    source = StringField(max_length=50, default="API")

    # details saved as text for flexible logging
    details = StringField()

    # when the action happened
    timestamp = DateTimeField(default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": str(self.id),
            "method": self.method,
            "target": self.target_entity,
            "target_entity": self.target_entity,  # extra-friendly key
            "source": self.source,
            "user_id": int(self.user.id) if self.user else None,  # may be ObjectId-like in mongoengine; keep safe cast
            "user_name": self.user.full_name if self.user else "System",
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else ""
        }
