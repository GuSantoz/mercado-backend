from src.Domain.employee import EmployeeDomain
from src.Infrastructure.Model.employee import Employee
from src.config.data_base import db 
from werkzeug.security import generate_password_hash

class EmployeeService:
    
    @staticmethod
    def create_employee(name, cpf, password, role, store_id):
        # Verifica se o CPF já está cadastrado em algum lugar do sistema
        funcionario_existente = db.session.query(Employee).filter(Employee.cpf == cpf).first()
        if funcionario_existente:
            return {"success": False, "message": "Este CPF já está cadastrado no sistema."}

        # Criptografa a senha
        password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
        
        novo_funcionario = Employee(
            name=name, 
            cpf=cpf, 
            password=password_hash, 
            role=role, 
            store_id=store_id
        )
        
        try:
            db.session.add(novo_funcionario)
            db.session.commit()       
            
            employee_domain = EmployeeDomain(
                novo_funcionario.id, 
                novo_funcionario.name, 
                novo_funcionario.cpf, 
                novo_funcionario.role, 
                novo_funcionario.store_id
            )
            
            return {"success": True, "message": "Funcionário criado com sucesso.", "employee": employee_domain}
            
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro interno ao salvar no banco de dados: {str(e)}"}

    @staticmethod
    def get_employees_by_store(store_id):
        # Busca apenas os funcionários da loja específica (store_id)
        employees = db.session.query(Employee).filter(Employee.store_id == store_id).all()
        return [EmployeeDomain(emp.id, emp.name, emp.cpf, emp.role, emp.store_id) for emp in employees]