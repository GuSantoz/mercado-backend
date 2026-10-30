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

            # Dá baixa no estoque do dono/loja
            resultado_estoque = ProductService.subtract_stock_batch(store_id, itens_venda)
            if not resultado_estoque["success"]:
                return resultado_estoque

            mapa_produtos = {p.id: p for p in resultado_estoque["products"]}
            codigo_pedido = SaleService.generate_order_code()

            # Se for DONO, grava o user_id. Se for OPERADOR/FUNCIONÁRIO, grava o store_id na user_id e o id no employee_id
            if role == "DONO":
                real_user_id = user_id
                real_employee_id = None
            else:
                real_user_id = store_id
                real_employee_id = user_id

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

            sale.subtotal = total_venda
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
            
            # Se for funcionário/operador, filtra apenas pelas vendas onde o employee_id é o dele
            if role != "DONO":
                sales = query.filter(Sale.employee_id == user_id).order_by(Sale.created_at.desc()).all()
            else:
                # Se for dono, busca todas as vendas da sua loja (store_id / user_id)
                sales = query.filter(Sale.user_id == store_id).order_by(Sale.created_at.desc()).all()

            return sales
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar vendas: {str(e)}"}

    @staticmethod
    def update_status(sale_id, user_id, new_status):
        try:
            sale = (
                db.session.query(Sale)
                .filter(
                    Sale.id == sale_id,
                    Sale.user_id == user_id
                )
                .first()
            )

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