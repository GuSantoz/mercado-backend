from src.Domain.user import UserDomain
from src.Infrastructure.Model.user import User
from src.Infrastructure.Model.employee import Employee
from src.config.data_base import db 
from datetime import datetime, timedelta
import jwt
import os  
import re
from werkzeug.security import generate_password_hash, check_password_hash

SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-super-secreta")

class UserService:
    @staticmethod
    def get_all_users():
        users = db.session.query(User).all()
        return [UserDomain(user.id, user.name, user.cnpj, user.email, user.celular, user.status, user.code) for user in users]
    
    @staticmethod
    def get_user_by_id(user_id):
        user = db.session.query(User).filter(User.id == user_id).first()
        if user:
            return UserDomain(user.id, user.name, user.cnpj, user.email, user.celular, user.status, user.code)
        return None
    
    @staticmethod
    def create_user(name, cnpj, email, celular, password, code):
        usuario_existente = db.session.query(User).filter(User.cnpj == cnpj).first()
        if usuario_existente:
            return {"success": False, "message": "Este CNPJ já está cadastrado no sistema."}

        password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        user = User(name=name, cnpj=cnpj, email=email, celular=celular, password=password_hash, code=code)
        
        try:
            db.session.add(user)
            db.session.commit()       
            
            user_domain = UserDomain(user.id, user.name, user.cnpj, user.email, user.celular, user.status, user.code)
            
            return {"success": True, "message": "Usuário criado com sucesso.", "user": user_domain}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro interno ao salvar no banco de dados: {str(e)}"}
    

    @staticmethod
    def activate_user(cnpj, activation_code):
        user = db.session.query(User).filter(User.cnpj == cnpj, User.code == activation_code).first()
        if user:
            user.status = "Ativo"
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def authenticate_user(documento, password):
        # Remove pontuações para contar os dígitos (deixa só números)
        doc_limpo = re.sub(r'\D', '', documento)
        
        # 1. TENTA LOGIN COMO DONO (CNPJ - 14 dígitos)
        if len(doc_limpo) == 14:
            user = db.session.query(User).filter(User.cnpj == documento).first()
            if not user or not check_password_hash(user.password, password):
                return {"success": False, "message": "Credenciais inválidas. CNPJ ou senha incorretos."}

            if user.status != "Ativo":
                return {"success": False, "message": "Usuário inativo. Por favor, ative sua conta primeiro."}
            
            token = jwt.encode(
                {
                    "user_id": user.id, 
                    "store_id": user.id, # O dono é a própria loja
                    "documento": user.cnpj, 
                    "role": "DONO", # Papel master
                    "exp": datetime.utcnow() + timedelta(hours=8)
                },
                SECRET_KEY, algorithm="HS256"
            )
            return {"success": True, "token": token, "nome": user.name, "role": "DONO"}

        # 2. TENTA LOGIN COMO FUNCIONÁRIO (CPF - 11 dígitos)
        elif len(doc_limpo) == 11:
            employee = db.session.query(Employee).filter(Employee.cpf == documento).first()
            if not employee or not check_password_hash(employee.password, password):
                return {"success": False, "message": "Credenciais inválidas. CPF ou senha incorretos."}

            token = jwt.encode(
                {
                    "user_id": employee.id, 
                    "store_id": employee.store_id, # Vincula o funcionário à loja do dono
                    "documento": employee.cpf, 
                    "role": employee.role, # GERENTE, OPERADOR ou COMPRADOR
                    "exp": datetime.utcnow() + timedelta(hours=8)
                },
                SECRET_KEY, algorithm="HS256"
            )
            return {"success": True, "token": token, "nome": employee.name, "role": employee.role}

        # 3. DOCUMENTO INVÁLIDO
        else:
            return {"success": False, "message": "Documento inválido. Digite um CPF ou CNPJ válido."}

    @staticmethod
    def validate_token(token):
        if not token or not token.startswith("Bearer "):
            return {"success": False, "message": "Token não fornecido ou mal formatado"}
        
        token = token.split(" ")[1]
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
            return {
                "success": True, 
                "user_id": data.get("user_id"),
                "store_id": data.get("store_id"),
                "role": data.get("role")
            }
        
        except Exception as e:
            return {"success": False, "message": f"Erro: {e}"}

    @staticmethod
    def update_user(user_id, data_to_update):
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "message": "Usuário não encontrado."}
        
        if 'nome' in data_to_update:
            user.name = data_to_update['nome']
        if 'email' in data_to_update:
            user.email = data_to_update['email']
        if 'celular' in data_to_update:
            user.celular = data_to_update['celular']
        
        try:
            db.session.commit()
            return {"success": True, "message": "Informações atualizadas com sucesso."}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao atualizar o banco de dados: {str(e)}"}