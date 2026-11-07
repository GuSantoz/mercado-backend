class EmployeeDomain:
    # 1. Adicione o 'status' aqui nos parâmetros
    def __init__(self, id, name, cpf, role, status, store_id): 
        self.id = id
        self.name = name
        self.cpf = cpf
        self.role = role
        self.status = status # 2. Inicialize o atributo
        self.store_id = store_id

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.name,
            "cpf": self.cpf,
            "role": self.role,
            "status": self.status, # Agora isso vai funcionar!
            "store_id": self.store_id
        }