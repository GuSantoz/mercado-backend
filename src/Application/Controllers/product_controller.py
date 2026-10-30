from flask import request, jsonify, make_response
from src.Application.Service.product_service import ProductService
from src.Application.Service.user_service import UserService
from src.Infrastructure.storage.image_storage import save_product_image


class ProductController:
    @staticmethod
    def get_all_products():
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)
        
        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401) 
        
        loja_id = token_validation.get("store_id")
        
        # Agora buscamos os produtos passando o ID da loja/dono
        products = ProductService.get_all_products(loja_id)

        return make_response(jsonify({
            "mensagem": "Produtos encontrados com sucesso",
            "usuarios": [product.to_dict() for product in products] # O ideal seria "produtos" aqui em vez de "usuarios", mas mantive seu código!
        }), 200)
    
    @staticmethod
    def create_product():
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)
        
        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)
        
        loja_id = token_validation.get("store_id")

        data = request.get_json()
        
        name = data.get('name')
        price = data.get('price')
        quantity = data.get('quantity')
        image = data.get('image')

        if not name or not price or not quantity or not image:
            return make_response(jsonify({"erro": "Missing required fields"}), 400)
 
        product = ProductService.create_product(name, price, quantity, image, loja_id)
 
        if not product["success"]:
            return make_response(jsonify({"erro": product["message"]}), 400)
 
        productDomain = product["produto"]

        return make_response(
            jsonify({
                "message": "Produto cadastrado com sucesso!",
                "produto": productDomain.to_dict()
            }), 201
        )

    @staticmethod
    def upload_image():
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)

        file = request.files.get('image')
        image_path, error = save_product_image(file)

        if error:
            return make_response(jsonify({"erro": error}), 400)

        return make_response(jsonify({"image": image_path}), 200)
    
    @staticmethod
    def update_product():
        token = request.headers.get('Authorization')
        data = request.get_json()

        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        if not data:
            return make_response(jsonify({"erro": "Dados para atualização não fornecidos"}), 400)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)

        product_id = data.get('id')
        if not product_id:
            return make_response(jsonify({"erro": "ID do produto não fornecido"}), 400)

        result = ProductService.update_product(product_id, data)

        if result["success"]:
                return make_response(jsonify({"mensagem": result["message"]}), 200)
        else:
                return make_response(jsonify({"erro": result["message"]}), 400)


    @staticmethod
    def update_status_product():
        token = request.headers.get('Authorization')
        data = request.get_json()

        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        if not data:
            return make_response(jsonify({"erro": "Dados para atualização não fornecidos"}), 400)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)

        product_id = data.get('id')
        if not product_id:
            return make_response(jsonify({"erro": "ID do produto não fornecido"}), 400)

        if 'status' not in data:
            return make_response(jsonify({"erro": "Status não fornecido"}), 400)

        result = ProductService.update_product(product_id, {"status": data.get('status')})

        if result["success"]:
            return make_response(jsonify({"mensagem": result["message"]}), 200)
        return make_response(jsonify({"erro": result["message"]}), 400)
    