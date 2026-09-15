from src.Infrastructure.Model.sale import Sale
from src.Infrastructure.Model.sale_items import SaleItem
from src.Application.Service.product_service import ProductService
from src.config.data_base import db
from src.Infrastructure.Model.product import Product

from decimal import Decimal
import random


class SaleService:

    @staticmethod
    def generate_order_code():
        numero = random.randint(1000, 9999)
        return f"P-{numero}"

    @staticmethod
    def create_venda(user_id, itens):
        try:
            itens_venda = {}

            for item in itens:
                product_id = item.get("product_id")
                quantidade = item.get("quantity")

                if not product_id or not quantidade:
                    return {
                        "success": False,
                        "message": (
                            "Dados incompletos nos itens da venda "
                            "(necessário product_id e quantity)."
                        )
                    }

                if not isinstance(quantidade, int) or quantidade <= 0:
                    return {
                        "success": False,
                        "message": (
                            "A quantidade deve ser um número inteiro "
                            "maior que zero."
                        )
                    }

                if product_id in itens_venda:
                    itens_venda[product_id] += quantidade
                else:
                    itens_venda[product_id] = quantidade

            resultado_estoque = ProductService.subtract_stock_batch(
                user_id,
                itens_venda
            )

            if not resultado_estoque["success"]:
                return resultado_estoque

            produtos_atualizados = resultado_estoque["products"]

            mapa_produtos = {
                produto.id: produto
                for produto in produtos_atualizados
            }

            codigo_pedido = SaleService.generate_order_code()

            sale = Sale(
                order_number=codigo_pedido,
                user_id=user_id,
                total_price=Decimal("0.00"),
                status=True
            )

            db.session.add(sale)

            total_venda = Decimal("0.00")

            for product_id, quantidade in itens_venda.items():
                produto = mapa_produtos.get(product_id)

                if not produto:
                    db.session.rollback()

                    return {
                        "success": False,
                        "message": (
                            f"Produto {product_id} não encontrado "
                            "após atualização do estoque."
                        )
                    }

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

            sale.total_price = total_venda

            db.session.commit()

            return {
                "success": True,
                "message": (
                    f"Pedido {codigo_pedido} realizado com sucesso "
                    f"com {len(itens_venda)} produto(s)!"
                ),
                "venda": sale
            }

        except Exception as e:
            db.session.rollback()

            return {
                "success": False,
                "message": f"Erro ao registrar pedido: {str(e)}"
            }

    @staticmethod
    def get_all_vendas(user_id):
        try:
            sales = (
                db.session.query(Sale)
                .filter(Sale.user_id == user_id)
                .order_by(Sale.created_at.desc())
                .all()
            )

            return sales

        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao buscar vendas: {str(e)}"
            }

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

            # Converte o status recebido para boolean
            if isinstance(new_status, str):
                new_status = new_status.lower() == "true"

            new_status = bool(new_status)

            # Se o status não mudou, não altera o estoque novamente
            if sale.status == new_status:
                return {
                    "success": True,
                    "message": "A venda já possui esse status",
                    "venda": sale
                }

            # =====================================================
            # INATIVAR VENDA
            # Devolve os produtos para o estoque
            # =====================================================
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

            # =====================================================
            # REATIVAR VENDA
            # Retira novamente os produtos do estoque
            # =====================================================
            elif sale.status is False and new_status is True:

                # Primeiro verifica se todos os produtos possuem estoque
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

                # Somente depois da validação decrementa os estoques
                for item in sale.items:
                    product = (
                        db.session.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )

                    product.quantity -= item.quantity

            # Atualiza o status da venda
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