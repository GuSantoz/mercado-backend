from src.config.data_base import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False)
    
    # Mantém o user_id apontando para a loja/dono
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Vincula o operador/funcionário
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=True)
    discount_applied = db.Column(db.Numeric(10, 2), nullable=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey('coupons.id'), nullable=True)
    coupon_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # CORREÇÃO AQUI: Altere backref='sale' para back_populates='sale'
    items = db.relationship('SaleItem', back_populates='sale', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "employee_id": self.employee_id,
            "total_price": float(self.total_price) if self.total_price else 0.0,
            "subtotal": float(self.subtotal) if self.subtotal else 0.0,
            "discount_applied": float(self.discount_applied) if self.discount_applied else 0.0,
            "coupon_id": self.coupon_id,
            "coupon_code": self.coupon_code,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "items": [item.to_dict() for item in self.items]
        }