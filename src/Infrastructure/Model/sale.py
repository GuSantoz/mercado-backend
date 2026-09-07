from src.config.data_base import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sales'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Relacionamento: Uma venda tem vários itens (cascade="all, delete-orphan" apaga os itens se a venda for apagada)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "user_id": self.user_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Calculamos o valor total do pedido somando o total_price de todos os itens
            "total_order": sum(float(item.total_price) for item in self.items) if self.items else 0.0,
            "items": [item.to_dict() for item in self.items] # Chama o to_dict dos itens
        }