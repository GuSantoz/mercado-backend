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
                novo_funcionario.status, 
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
        # ADICIONE O emp.status AQUI, DEPOIS DO emp.role:
        return [EmployeeDomain(emp.id, emp.name, emp.cpf, emp.role, emp.status, emp.store_id) for emp in employees]

    @staticmethod
    def update_employee(employee_id, role, store_id, update_data):
        try:
            role_upper = str(role).upper().strip() if role else ""

            # Bloqueia se não for o dono
            if role_upper != "DONO":
                return {"success": False, "message": "Apenas o dono da loja pode editar os dados dos funcionários."}

            # Busca o funcionário garantindo que ele pertence à mesma loja do dono
            # IMPORTANTE: Troque 'User' pelo nome do seu model de usuário/funcionário
            employee = db.session.query(Employee).filter(
                Employee.id == employee_id,
                Employee.store_id == int(store_id)
            ).first()

            if not employee:
                return {"success": False, "message": "Funcionário não encontrado ou não pertence a esta loja."}

            # Atualiza os dados permitidos (adicione ou remova os campos conforme sua necessidade)
            if "name" in update_data:
                employee.name = update_data["name"]
                
            if "email" in update_data:
                # (Opcional) Aqui você pode adicionar uma validação para ver se o email já existe
                employee.email = update_data["email"]
                
            if "cargo" in update_data:
                employee.role = update_data["cargo"]
                
            if "status" in update_data:
                employee.status = bool(update_data["status"])

            db.session.commit()

            return {
                "success": True, 
                "message": "Dados do funcionário atualizados com sucesso!",
                "employee": employee.to_dict() # Supondo que você tenha esse método
            }

        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao atualizar funcionário: {str(e)}"}