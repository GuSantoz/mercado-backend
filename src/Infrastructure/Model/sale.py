from datetime import datetime

from src.config.data_base import db


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer,primary_key=True)
    order_number = db.Column(db.String(10), nullable=False, unique=True)
    user_id = db.Column( db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    items = db.relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "total_price": (
                float(self.total_price)
                if self.total_price is not None
                else 0.0
            ),
            "status": self.status,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "items": [
                item.to_dict()
                for item in self.items
            ]
        }
