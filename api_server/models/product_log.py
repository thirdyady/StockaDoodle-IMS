from extensions import db
from datetime import datetime, timezone

class ProductLog(db.Model):
    __tablename__ = 'product_logs'

    # id of the log entry
    id = db.Column(db.Integer, primary_key=True)

    # product related to the log
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # user who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # type of action performed
    action_type = db.Column(db.String(50), nullable=False)

    # optional notes about the action
    notes = db.Column(db.Text, nullable=True)

    # timestamp when the log was created
    log_time = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'notes': self.notes,
            'log_time': self.log_time.isoformat()
        }
