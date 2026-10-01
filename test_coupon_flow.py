import unittest
import json
from decimal import Decimal
from datetime import datetime, timedelta
from run import create_app
from src.config.data_base import db
from src.Infrastructure.Model.user import User
from src.Infrastructure.Model.product import Product
from src.Infrastructure.Model.coupon import Coupon
from src.Infrastructure.Model.sale import Sale
from src.Application.Service.user_service import UserService

class CouponFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Clean up test data if any
            db.session.query(Sale).delete()
            db.session.query(Coupon).delete()
            db.session.query(Product).delete()
            db.session.query(User).filter(User.cnpj == "00.000.000/0001-99").delete()
            db.session.commit()

            # Create and activate test user
            res = UserService.create_user(
                name="Mercadinho Teste",
                cnpj="00.000.000/0001-99",
                email="mercadinho@teste.com",
                celular="+5511999999999",
                password="senha1234",
                code="1234"
            )
            UserService.activate_user("00.000.000/0001-99", "1234")
            auth_res = UserService.authenticate_user("00.000.000/0001-99", "senha1234")
            self.token = auth_res["token"]
            self.user_id = db.session.query(User).filter(User.cnpj == "00.000.000/0001-99").first().id

            # Create test product
            self.product = Product(
                name="Arroz 5kg",
                price=Decimal("30.00"),
                quantity=100,
                status=True,
                image="default.png",
                user_id=self.user_id
            )
            db.session.add(self.product)
            db.session.commit()
            self.product_id = self.product.id

    def test_coupon_full_lifecycle(self):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # 1. Create Coupon (10% OFF, min R$ 50)
        coupon_payload = {
            "code": "PROMO10",
            "description": "Desconto de 10% para compras acima de R$ 50",
            "discount_type": "percentage",
            "discount_value": 10.0,
            "min_purchase_value": 50.0,
            "usage_limit": 5,
            "status": True
        }
        res = self.client.post("/coupon", headers=headers, json=coupon_payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["cupom"]["code"], "PROMO10")
        self.assertEqual(data["cupom"]["computed_status"], "Ativo")

        # 2. List Coupons
        res = self.client.get("/coupon", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()["cupons"]), 1)

        # 3. Validate Coupon with subtotal below minimum (R$ 30 < R$ 50)
        val_res = self.client.post("/coupon/validate", headers=headers, json={
            "code": "PROMO10",
            "subtotal": 30.0
        })
        self.assertEqual(val_res.status_code, 400)
        self.assertIn("exige uma compra mínima", val_res.get_json()["erro"])

        # 4. Validate Coupon with subtotal above minimum (R$ 90)
        val_res = self.client.post("/coupon/validate", headers=headers, json={
            "code": "PROMO10",
            "subtotal": 90.0
        })
        self.assertEqual(val_res.status_code, 200)
        val_data = val_res.get_json()["dados"]
        self.assertEqual(val_data["discount_applied"], 9.0)  # 10% of 90 = 9
        self.assertEqual(val_data["total_price"], 81.0)

        # 5. Make a Sale using the coupon (3 items of R$ 30 = R$ 90 -> R$ 81 final)
        sale_payload = {
            "itens": [{"product_id": self.product_id, "quantity": 3}],
            "coupon_code": "PROMO10"
        }
        sale_res = self.client.post("/venda", headers=headers, json=sale_payload)
        self.assertEqual(sale_res.status_code, 201)
        sale_data = sale_res.get_json()["venda"]
        self.assertEqual(sale_data["subtotal"], 90.0)
        self.assertEqual(sale_data["discount_applied"], 9.0)
        self.assertEqual(sale_data["total_price"], 81.0)
        self.assertEqual(sale_data["coupon_code"], "PROMO10")

        # 6. Verify coupon usage count incremented to 1
        with self.app.app_context():
            c = db.session.query(Coupon).filter(Coupon.code == "PROMO10").first()
            self.assertEqual(c.usage_count, 1)

            # Stock should be 100 - 3 = 97
            p = db.session.query(Product).filter(Product.id == self.product_id).first()
            self.assertEqual(p.quantity, 97)

        # 7. Inactivate Sale (Cancel order) -> Should revert stock and usage count
        sale_id = sale_data["id"]
        status_res = self.client.put("/venda/status", headers=headers, json={
            "id": sale_id,
            "status": False
        })
        self.assertEqual(status_res.status_code, 200)

        with self.app.app_context():
            c = db.session.query(Coupon).filter(Coupon.code == "PROMO10").first()
            self.assertEqual(c.usage_count, 0)
            p = db.session.query(Product).filter(Product.id == self.product_id).first()
            self.assertEqual(p.quantity, 100)

        # 8. Reactivate Sale -> Should deduct stock and increment usage count again
        status_res = self.client.put("/venda/status", headers=headers, json={
            "id": sale_id,
            "status": True
        })
        self.assertEqual(status_res.status_code, 200)

        with self.app.app_context():
            c = db.session.query(Coupon).filter(Coupon.code == "PROMO10").first()
            self.assertEqual(c.usage_count, 1)
            p = db.session.query(Product).filter(Product.id == self.product_id).first()
            self.assertEqual(p.quantity, 97)

        print("\nAll coupon backend tests passed with flying colors!")

if __name__ == "__main__":
    unittest.main()
