from extensions import db
from datetime import datetime

class APIActivityLog(db.Model):
    __tablename__ = "api_activity_logs"

    # id of the api log entry
    id = db.Column(db.Integer, primary_key=True)

    # http method like POST or GET
    method = db.Column(db.String(10), nullable=False)

    # the target entity name like product or user
    target_entity = db.Column(db.String(50), nullable=False)

    # optional user responsible for the action
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # where the action came from
    source = db.Column(db.String(50), default="API")

    # details saved as text for flexible logging
    details = db.Column(db.Text)

    # when the action happened
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "method": self.method,
            "target": self.target_entity,
            "source": self.source,
            "user_id": self.user_id,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }
