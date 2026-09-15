from src.config.data_base import db


class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)


    sale = db.relationship("Sale", back_populates="items")
    product = db.relationship("Product", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "product_name": (
                self.product.name
                if self.product
                else None
            ),
            "quantity": self.quantity,
            "unit_price": (
                float(self.unit_price)
                if self.unit_price is not None
                else 0.0
            ),
            "total_price": (
                float(self.total_price)
                if self.total_price is not None
                else 0.0
            )
        }