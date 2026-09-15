from itertools import product

from src.Domain.product import ProductDomain
from src.Domain.sale import SaleDomain
from src.Infrastructure.Model.product import Product
from src.Infrastructure.Model.sale import Sale
from src.Infrastructure.Model.sale_items import SaleItem
from src.config.data_base import db
from datetime import datetime

class ProductService:
    @staticmethod
    def get_all_products(user_id):
        products = db.session.query(Product).filter(Product.user_id == user_id).all()
        return [ProductDomain(product.id, product.name, product.price, product.quantity, product.status, product.image, product.user_id)for product in products]
    
    @staticmethod
    def create_product(name, price, quantity, image, user_id):
        if db.session.query(Product).filter(Product.name == name, Product.user_id == user_id).first():
            return {"success": False, "message": "Já há um produto cadastrado com esse nome!"}
        
        product = Product(name=name, price=price, quantity=quantity, image=image, user_id=user_id)
        db.session.add(product)
        db.session.commit()
 
        product = ProductDomain(
            product.id, product.name, product.price, 
            product.quantity, product.status, product.image, product.user_id
        )

        return {
            "success": True,
            "produto": product
        }
    

    @staticmethod
    def update_product(product_id, data):
        product = db.session.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"success": False, "message": "Produto não encontrado!"}
        
        if 'name' in data:
            product.name = data['name']
        if 'image' in data:
            product.image = data['image']
        if 'price' in data:
            product.price = data['price']


        if 'quantity' in data:
            product.quantity = int(data['quantity'])
            ProductService._recalculate_status(product)   
        # if 'quantity' in data:
        #     nova_quantidade = int(data['quantity'])
        #     product.quantity = nova_quantidade
            
        #     if nova_quantidade <= 0:
        #         product.status = False

        if 'status' in data:
            if product.quantity > 0:
                product.status = data['status']
            else:
                product.status = False

        try:
            db.session.commit()
            return {"success": True, "message": "Informações do produto atualizadas com sucesso."}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao atualizar o banco de dados: {str(e)}"}



    #-----------------------------
    # --- MOTOR INTERNO DE ESTOQUE ---
    @staticmethod
    def _recalculate_status(product):
        # Atualiza o status com base na quantidade atual.
        if product.quantity <= 0:
            product.quantity = 0
            product.status = False
        else:
            product.status = True
        return product

    # --- FUNÇÕES PÚBLICAS DE ESTOQUE (Em Lote) ---
    @staticmethod
    def subtract_stock_batch(user_id, items_to_subtract):
       # Subtrai itens do estoque (Saída/Vendas).
        product_ids = list(items_to_subtract.keys())
        products = db.session.query(Product).filter(
            Product.id.in_(product_ids),
            Product.user_id == user_id
        ).all()

        if len(products) != len(product_ids):
            return {"success": False, "message": "Um ou mais produtos não foram encontrados."}

        for product in products:
            quantidade_saida = items_to_subtract.get(product.id, 0)
            
            # Trava de segurança contra estoque negativo
            if product.quantity < quantidade_saida:
                return {"success": False, "message": f"Estoque insuficiente para '{product.name}'."}
                
            product.quantity -= quantidade_saida
            ProductService._recalculate_status(product)
            
        return {"success": True, "products": products}

    @staticmethod
    def add_stock_batch(user_id, items_to_add):
        # Adiciona itens ao estoque (Entrada/Inativação de Venda).
        product_ids = list(items_to_add.keys())
        products = db.session.query(Product).filter(
            Product.id.in_(product_ids),
            Product.user_id == user_id
        ).all()

        for product in products:
            quantidade_entrada = items_to_add.get(product.id, 0)
            product.quantity += quantidade_entrada
            ProductService._recalculate_status(product)
            
        return {"success": True, "products": products}