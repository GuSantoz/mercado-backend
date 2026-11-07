from flask import request, jsonify, make_response
from src.Application.Service.employee_service import EmployeeService
from src.Application.Service.user_service import UserService

class EmployeeController:
    
    @staticmethod
    def register_employee():
        # 1. Valida o Token e verifica permissão
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)
        
        # Apenas o DONO (ou GERENTE, se você quiser) pode criar funcionários
        if token_validation.get("role") != "DONO":
            return make_response(jsonify({"erro": "Acesso negado. Apenas o dono do estabelecimento pode cadastrar funcionários."}), 403)

        # 2. Recebe os dados
        data = request.get_json()
        name = data.get('nome')
        cpf = data.get('cpf')
        password = data.get('senha')
        role = data.get('role') # Esperado: 'GERENTE', 'OPERADOR', 'COMPRADOR'
        store_id = token_validation["store_id"] # Pega o ID da loja direto do token de quem está logado

        if not name or not cpf or not password or not role:
            return make_response(jsonify({"erro": "Todos os campos (nome, cpf, senha, role) são obrigatórios"}), 400)

        # 3. Chama o Service
        result = EmployeeService.create_employee(name, cpf, password, role, store_id)
        
        if result["success"]:
            return make_response(jsonify({
                "mensagem": result["message"],
                "funcionario": result["employee"].to_dict()
            }), 201)
        else:
            return make_response(jsonify({"erro": result["message"]}), 409)

    @staticmethod
    def list_employees():
        # 1. Valida o Token
        token = request.headers.get('Authorization')
        if not token:
            return make_response(jsonify({"erro": "Token não fornecido"}), 401)

        token_validation = UserService.validate_token(token)
        if not token_validation["success"]:
            return make_response(jsonify({"erro": token_validation["message"]}), 401)

        # Apenas DONO pode listar os funcionários
        if token_validation.get("role") != "DONO":
             return make_response(jsonify({"erro": "Acesso negado."}), 403)

        store_id = token_validation["store_id"]

        # 2. Busca e retorna
        employees = EmployeeService.get_employees_by_store(store_id)
        return make_response(jsonify({
            "mensagem": "Funcionários listados com sucesso",
            "funcionarios": [emp.to_dict() for emp in employees]
        }), 200)