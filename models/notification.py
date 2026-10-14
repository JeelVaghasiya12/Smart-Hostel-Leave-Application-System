from datetime import datetime
from models.user import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    message = db.Column(db.String(500), nullable=False)

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __init__(self, student_id, message):
        self.student_id = student_id
        self.message = message
        self.is_read = False

    def mark_as_read(self):
        self.is_read = True