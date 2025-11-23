from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
import base64

class User(db.Model):
    __tablename__ = 'users'

    # id of the user
    id = db.Column(db.Integer, primary_key=True)

    # full name for display
    full_name = db.Column(db.String(120), nullable=False)

    # used for login
    username = db.Column(db.String(120), unique=True, nullable=False)

    # staff/admin/etc
    role = db.Column(db.String(50), default="staff")

    # hashed password only
    password_hash = db.Column(db.String(255), nullable=False)

    # optional profile picture
    user_image = db.Column(db.LargeBinary)

    # batches added by this user
    stock_batches = db.relationship('StockBatch', backref='added_by_user', lazy=True)

    def set_password(self, password):
        # turn plain password into hashed password
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # check if password is correct
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_image=False):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "role": self.role,
            "has_image": self.user_image is not None
        }

        if include_image and self.user_image:
            # return user image as base64 string
            data["image_base64"] = base64.b64encode(self.user_image).decode("utf-8")

        return data
