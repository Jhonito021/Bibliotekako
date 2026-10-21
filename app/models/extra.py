from datetime import datetime
from app.extensions import db


def utcnow():
    return datetime.utcnow()


class BookCopy(db.Model):
    __tablename__ = "book_copies"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    inventory_code = db.Column(db.String(100), nullable=False, unique=True, index=True)
    status = db.Column(db.String(24), nullable=False, default="available", index=True)
    condition_note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    book = db.relationship("Book")

    def to_dict(self):
        return {"id": self.id, "book_id": self.book_id,
                "book_title": self.book.title if self.book else None,
                "inventory_code": self.inventory_code, "status": self.status,
                "condition_note": self.condition_note,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class Loan(db.Model):
    __tablename__ = "loans"
    id = db.Column(db.Integer, primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    copy_id = db.Column(db.Integer, db.ForeignKey("book_copies.id"), nullable=False, index=True)
    borrowed_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)
    status = db.Column(db.String(24), nullable=False, default="active", index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    reader = db.relationship("User", foreign_keys=[reader_id])
    copy = db.relationship("BookCopy")

    def to_dict(self):
        now = self.returned_at or utcnow()
        overdue_days = max(0, (now - self.due_at).days) if self.due_at else 0
        return {"id": self.id, "reader_id": self.reader_id,
                "reader_name": self.reader.full_name if self.reader else None,
                "copy_id": self.copy_id,
                "book_title": self.copy.book.title if self.copy and self.copy.book else None,
                "inventory_code": self.copy.inventory_code if self.copy else None,
                "borrowed_at": self.borrowed_at.isoformat() if self.borrowed_at else None,
                "due_at": self.due_at.isoformat() if self.due_at else None,
                "returned_at": self.returned_at.isoformat() if self.returned_at else None,
                "status": self.status, "overdue_days": overdue_days}


class Reservation(db.Model):
    __tablename__ = "reservations"
    id = db.Column(db.Integer, primary_key=True)
    reader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False, index=True)
    status = db.Column(db.String(24), nullable=False, default="waiting", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    expires_at = db.Column(db.DateTime)
    reader = db.relationship("User")
    book = db.relationship("Book")

    def to_dict(self):
        return {"id": self.id, "reader_id": self.reader_id,
                "reader_name": self.reader.full_name if self.reader else None,
                "book_id": self.book_id, "book_title": self.book.title if self.book else None,
                "status": self.status,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None}


class Fine(db.Model):
    __tablename__ = "fines"
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loans.id"), nullable=False, unique=True)
    reader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(24), nullable=False, default="unpaid", index=True)
    reason = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    paid_at = db.Column(db.DateTime)
    waived_at = db.Column(db.DateTime)
    reader = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "loan_id": self.loan_id, "reader_id": self.reader_id,
                "reader_name": self.reader.full_name if self.reader else None,
                "amount": self.amount, "status": self.status, "reason": self.reason,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "paid_at": self.paid_at.isoformat() if self.paid_at else None,
                "waived_at": self.waived_at.isoformat() if self.waived_at else None}


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    kind = db.Column(db.String(40), nullable=False, default="info")
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    user = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "title": self.title, "message": self.message,
                "kind": self.kind, "is_read": self.is_read,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    actor = db.relationship("User")

    def to_dict(self):
        return {"id": self.id, "actor_id": self.actor_id,
                "actor_name": self.actor.full_name if self.actor else None,
                "action": self.action, "entity_type": self.entity_type,
                "entity_id": self.entity_id, "details": self.details,
                "created_at": self.created_at.isoformat() if self.created_at else None}


class AppSetting(db.Model):
    __tablename__ = "app_settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {"key": self.key, "value": self.value,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None}
