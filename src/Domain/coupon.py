from datetime import datetime

class CouponDomain:
    def __init__(
        self,
        id,
        code,
        description,
        discount_type,
        discount_value,
        min_purchase_value,
        max_discount_value,
        usage_limit,
        usage_count,
        valid_from,
        valid_until,
        status,
        user_id,
        created_at=None
    ):
        self.id = id
        self.code = code
        self.description = description
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.min_purchase_value = min_purchase_value
        self.max_discount_value = max_discount_value
        self.usage_limit = usage_limit
        self.usage_count = usage_count
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.status = status
        self.user_id = user_id
        self.created_at = created_at

    def get_computed_status(self):
        now = datetime.now()
        if not self.status:
            return "Inativo"
        if self.valid_until and self.valid_until < now:
            return "Expirado"
        if self.valid_from and self.valid_from > now:
            return "Agendado"
        if self.usage_limit is not None and self.usage_count >= self.usage_limit:
            return "Esgotado"
        return "Ativo"

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "description": self.description,
            "discount_type": self.discount_type,
            "discount_value": float(self.discount_value) if self.discount_value is not None else 0.0,
            "min_purchase_value": float(self.min_purchase_value) if self.min_purchase_value is not None else 0.0,
            "max_discount_value": float(self.max_discount_value) if self.max_discount_value is not None else None,
            "usage_limit": self.usage_limit,
            "usage_count": self.usage_count,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "status": self.status,
            "computed_status": self.get_computed_status(),
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
