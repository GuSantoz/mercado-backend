from datetime import datetime
from src.config.data_base import db

class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    discount_type = db.Column(db.String(20), nullable=False, default='percentage')  # 'percentage' ou 'fixed'
    discount_value = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    min_purchase_value = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    max_discount_value = db.Column(db.Numeric(10, 2), nullable=True)
    usage_limit = db.Column(db.Integer, nullable=True)
    usage_count = db.Column(db.Integer, nullable=False, default=0)
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def get_computed_status(self):
        now = datetime.now()
        if not self.status:
            return "Inativo"
        if self.valid_until and self.valid_until < now:
            return "Expirado"
        if self.valid_from and self.valid_from > now:
            return "Agendado"
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return "Esgotado"
        return "Ativo"

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value is not None else 0.0,
            "min_purchase_value": float(self.min_purchase_value) if self.min_purchase_value is not None else 0.0,
            "max_discount_value": float(self.max_discount_value) if self.max_discount_value is not None else None,
            "usage_limit": self.usage_limit,
            "usage_count": self.usage_count,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "status": self.status,
            "computed_status": self.get_computed_status(),
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
