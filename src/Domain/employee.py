class EmployeeDomain:
    def __init__(self, id, name, cpf, role, store_id):
        self.id = id
        self.name = name
        self.cpf = cpf
        self.role = role
        self.store_id = store_id

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.name,
            "cpf": self.cpf,
            "role": self.role,
            "store_id": self.store_id
        }