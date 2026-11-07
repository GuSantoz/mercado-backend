from src.config.data_base import db 

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False) # Ex: 'GERENTE', 'OPERADOR', 'COMPRADOR'
    
    store_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.name,
            "cpf": self.cpf,
            "role": self.role,
            "store_id": self.store_id
        }