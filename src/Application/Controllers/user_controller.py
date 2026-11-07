from flask import request, jsonify, make_response
from src.Application.Service.user_service import UserService
from src.Infrastructure.http.whats_app import WhatsAppService

class UserController:
    
    @staticmethod
    def register_user():
        data = request.get_json()

        name = data.get('nome')
        cnpj = data.get('cnpj')
        email = data.get('email')
        celular = data.get('celular')
        password = data.get('senha')

        if not name or not email or not password or not celular or not cnpj:
            return make_response(jsonify({"erro": "Missing required fields"}), 400)

        code = WhatsAppService.generate_code()

        result = UserService.create_user(name, cnpj, email, celular, password, code)
        
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 409)

        WhatsAppService().send_activation_message(celular, code)

        return make_response(jsonify({
            "mensagem": result["message"],
            "usuarios": result["user"].to_dict()
        }), 201)

    @staticmethod
    def activate_user():
        data = request.get_json()
        cnpj = data.get('cnpj')
        activation_code = data.get('activation_code')

        if not cnpj or not activation_code:
            return make_response(jsonify({"erro": "CNPJ e código de ativação são obrigatórios"}), 400)

        success = UserService.activate_user(cnpj, activation_code)
        if success:
            return make_response(jsonify({"mensagem": "Conta ativada com sucesso"}), 200)
        else:
            return make_response(jsonify({"erro": "Código de ativação inválido ou vendedor não encontrado"}), 400)

    @staticmethod
    def login():
        data = request.get_json()
        
        documento = data.get('documento') or data.get('cnpj') # Suporte retroativo caso o front ainda mande 'cnpj'
        password = data.get('password') 

        if not documento or not password:
            return make_response(jsonify({"erro": "CPF/CNPJ e senha são obrigatórios"}), 400)

        result = UserService.authenticate_user(documento, password)
        
        if result["success"]:
            return make_response(jsonify({
                "mensagem": "Login realizado com sucesso",
                "token": result["token"],
                "nome": result["nome"],
                "role": result["role"] # Devolve o papel para o React montar o menu lateral
            }), 200)
        else:
            return make_response(jsonify({"erro": result["message"]}), 401)

    @staticmethod
    def get_all_users():
        users = UserService.get_all_users()
        return make_response(jsonify({
            "mensagem": "Usuários encontrados com sucesso",
            "usuarios": [user.to_dict() for user in users]
        }), 200)
    
    @staticmethod
    def get_user():
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)

        user_id = token_validation["user_id"]
        user = UserService.get_user_by_id(user_id)
        if not user:
            return make_response(jsonify({"erro": "Usuário não encontrado"}), 404)

        return make_response(jsonify({
            "mensagem": "Usuário encontrado com sucesso",
            "nome": user.name,
            "email": user.email,
            "celular": user.celular
        }), 200)

    @staticmethod
    def update_user():
        token = request.headers.get('Authorization')
        data = request.get_json()
        
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)
        if not data:
            return make_response(jsonify({"erro": "Dados para atualização não fornecidos"}), 400)
        
        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)
            
        user_id = token_validation["user_id"]
        result = UserService.update_user(user_id, data)
        
        if result["success"]:
            return make_response(jsonify({"mensagem": result["message"]}), 200)
        else:
            return make_response(jsonify({"erro": result["message"]}), 400)