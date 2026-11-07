from src.Infrastructure.Model.sale import Sale
from src.Infrastructure.Model.sale_items import SaleItem
from src.Application.Service.product_service import ProductService
from src.config.data_base import db
from src.Infrastructure.Model.product import Product
from src.Infrastructure.Model.coupon import Coupon

from decimal import Decimal
import random


class SaleService:

    @staticmethod
    def generate_order_code():
        numero = random.randint(1000, 9999)
        return f"P-{numero}"

    @staticmethod
    def create_venda(user_id, store_id, role, itens, coupon_code=None):
        try:
            itens_venda = {}
            for item in itens:
                product_id = item.get("product_id")
                quantidade = item.get("quantity")
                if not product_id or not quantidade or not isinstance(quantidade, int) or quantidade <= 0:
                    return {"success": False, "message": "Dados inválidos nos itens."}
                
                itens_venda[product_id] = itens_venda.get(product_id, 0) + quantidade

            resultado_estoque = ProductService.subtract_stock_batch(store_id, itens_venda)
            if not resultado_estoque["success"]:
                return resultado_estoque

            mapa_produtos = {p.id: p for p in resultado_estoque["products"]}
            codigo_pedido = SaleService.generate_order_code()

            # Normaliza a permissão para maiúsculo para evitar erros de digitação/case
            role_upper = str(role).upper().strip() if role else ""

            # Converte IDs para inteiros para garantir compatibilidade com o MySQL
            if role_upper == "DONO":
                real_user_id = int(user_id)
                real_employee_id = None
            else:
                real_user_id = int(store_id)
                real_employee_id = int(user_id)

            sale = Sale(
                order_number=codigo_pedido,
                user_id=real_user_id,
                employee_id=real_employee_id,
                total_price=Decimal("0.00"),
                status=True
            )

            db.session.add(sale)
            total_venda = Decimal("0.00")

            for product_id, quantidade in itens_venda.items():
                produto = mapa_produtos.get(product_id)
                if not produto:
                    db.session.rollback()
                    return {"success": False, "message": f"Produto {product_id} não encontrado."}

                preco_unitario = Decimal(str(produto.price))
                total_item = preco_unitario * quantidade

                sale_item = SaleItem(
                    sale=sale,
                    product_id=produto.id,
                    quantity=quantidade,
                    unit_price=preco_unitario,
                    total_price=total_item
                )
                db.session.add(sale_item)
                total_venda += total_item

            subtotal = total_venda
            discount_applied = Decimal("0.00")
            coupon_id = None
            applied_coupon_code = None

            if coupon_code:
                from src.Application.Service.coupon_service import CouponService
                validation = CouponService.validate_coupon(store_id, coupon_code, subtotal)
                if not validation["success"]:
                    db.session.rollback()
                    ProductService.add_stock_batch(store_id, itens_venda)
                    return validation

                discount_applied = Decimal(str(validation["discount_applied"]))
                total_venda = Decimal(str(validation["total_price"]))
                coupon_id = validation["coupon_id"]
                applied_coupon_code = validation["coupon_code"]

                coupon_obj = db.session.query(Coupon).filter(Coupon.id == coupon_id).first()
                if coupon_obj:
                    coupon_obj.usage_count += 1

            sale.subtotal = subtotal
            sale.discount_applied = discount_applied
            sale.coupon_id = coupon_id
            sale.coupon_code = applied_coupon_code
            sale.total_price = total_venda

            db.session.commit()
            return {"success": True, "message": f"Pedido {codigo_pedido} realizado!", "venda": sale}

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao registrar pedido: {str(e)}"}

    @staticmethod
    def get_all_vendas(user_id, role, store_id):
        try:
            query = db.session.query(Sale)
            
            role_upper = str(role).upper().strip() if role else ""

            # Se for DONO ou GERENTE, busca todas as vendas da loja
            if role_upper in ["DONO", "GERENTE"]:
                sales = query.filter(Sale.user_id == int(store_id)).order_by(Sale.created_at.desc()).all()
            # Caso contrário (funcionário comum), busca apenas as vendas dele
            else:
                sales = query.filter(Sale.employee_id == int(user_id)).order_by(Sale.created_at.desc()).all()

            return sales
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar vendas: {str(e)}"}

    @staticmethod
    def update_status(sale_id, user_id, role, store_id, new_status):
        try:
            role_upper = str(role).upper().strip() if role else ""

            # Se for DONO ou GERENTE, busca a venda usando o ID da loja
            if role_upper in ["DONO", "GERENTE", "OPERADOR"]:
                sale = db.session.query(Sale).filter(
                    Sale.id == sale_id,
                    Sale.user_id == int(store_id)
                ).first()
            # Se for funcionário, busca garantindo que ele foi o vendedor
            else:
                sale = db.session.query(Sale).filter(
                    Sale.id == sale_id,
                    Sale.employee_id == int(user_id)
                ).first()

            if not sale:
                return {
                    "success": False,
                    "message": "Venda não encontrada"
                }

            if isinstance(new_status, str):
                new_status = new_status.lower() == "true"

            new_status = bool(new_status)

            if sale.status == new_status:
                return {
                    "success": True,
                    "message": "A venda já possui esse status",
                    "venda": sale
                }

            if sale.status is True and new_status is False:

                for item in sale.items:
                    product = (
                        db.session.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )

                    if not product:
                        db.session.rollback()

                        return {
                            "success": False,
                            "message": (
                                f"Produto ID {item.product_id} "
                                "não encontrado."
                            )
                        }

                    product.quantity += item.quantity

                if sale.coupon_id:
                    coupon = db.session.query(Coupon).filter(Coupon.id == sale.coupon_id).first()
                    if coupon and coupon.usage_count > 0:
                        coupon.usage_count -= 1

            elif sale.status is False and new_status is True:

                for item in sale.items:
                    product = (
                        db.session.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )

                    if not product:
                        db.session.rollback()

                        return {
                            "success": False,
                            "message": (
                                f"Produto ID {item.product_id} "
                                "não encontrado."
                            )
                        }

                    if product.quantity < item.quantity:
                        db.session.rollback()

                        return {
                            "success": False,
                            "message": (
                                f"Estoque insuficiente para o produto "
                                f"'{product.name}'. "
                                f"Disponível: {product.quantity}. "
                                f"Necessário: {item.quantity}."
                            )
                        }

                for item in sale.items:
                    product = (
                        db.session.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )

                    product.quantity -= item.quantity

                if sale.coupon_id:
                    coupon = db.session.query(Coupon).filter(Coupon.id == sale.coupon_id).first()
                    if coupon:
                        coupon.usage_count += 1

            sale.status = new_status

            db.session.commit()

            return {
                "success": True,
                "message": "Status da venda atualizado com sucesso",
                "venda": sale
            }

        except Exception as e:
            db.session.rollback()

            return {
                "success": False,
                "message": (
                    f"Erro ao atualizar status da venda: {str(e)}"
                )
            }