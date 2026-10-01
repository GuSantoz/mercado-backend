from datetime import datetime
from decimal import Decimal
from src.config.data_base import db
from src.Domain.coupon import CouponDomain
from src.Infrastructure.Model.coupon import Coupon
from src.Infrastructure.Model.sale import Sale

class CouponService:

    @staticmethod
    def _parse_datetime(val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            # Handle ISO formats like 2026-10-01T15:30 or 2026-10-01
            val_str = str(val).strip()
            if len(val_str) == 10:
                return datetime.strptime(val_str, "%Y-%m-%d")
            return datetime.fromisoformat(val_str.replace("Z", ""))
        except Exception:
            return None

    @staticmethod
    def get_all_coupons(user_id):
        coupons = (
            db.session.query(Coupon)
            .filter(Coupon.user_id == user_id)
            .order_by(Coupon.created_at.desc())
            .all()
        )
        return [
            CouponDomain(
                c.id, c.code, c.description, c.discount_type,
                c.discount_value, c.min_purchase_value, c.max_discount_value,
                c.usage_limit, c.usage_count, c.valid_from, c.valid_until,
                c.status, c.user_id, c.created_at
            )
            for c in coupons
        ]

    @staticmethod
    def get_coupon_by_id(user_id, coupon_id):
        coupon = (
            db.session.query(Coupon)
            .filter(Coupon.id == coupon_id, Coupon.user_id == user_id)
            .first()
        )
        if not coupon:
            return None
        return CouponDomain(
            coupon.id, coupon.code, coupon.description, coupon.discount_type,
            coupon.discount_value, coupon.min_purchase_value, coupon.max_discount_value,
            coupon.usage_limit, coupon.usage_count, coupon.valid_from, coupon.valid_until,
            coupon.status, coupon.user_id, coupon.created_at
        )

    @staticmethod
    def create_coupon(user_id, data):
        code = str(data.get("code", "")).strip().upper()
        if not code:
            return {"success": False, "message": "O código do cupom é obrigatório."}

        # Check uniqueness per user/seller
        existing = (
            db.session.query(Coupon)
            .filter(Coupon.user_id == user_id, Coupon.code == code)
            .first()
        )
        if existing:
            return {"success": False, "message": f"Já existe um cupom com o código '{code}'."}

        discount_type = data.get("discount_type", "percentage")
        if discount_type not in ["percentage", "fixed"]:
            return {"success": False, "message": "Tipo de desconto inválido (deve ser 'percentage' ou 'fixed')."}

        try:
            discount_value = Decimal(str(data.get("discount_value", 0)))
            if discount_value <= 0:
                return {"success": False, "message": "O valor do desconto deve ser maior que zero."}
            if discount_type == "percentage" and discount_value > 100:
                return {"success": False, "message": "O desconto em porcentagem não pode ultrapassar 100%."}
        except Exception:
            return {"success": False, "message": "Valor de desconto inválido."}

        min_purchase = Decimal(str(data.get("min_purchase_value", 0) or 0))
        if min_purchase < 0:
            min_purchase = Decimal(0)

        max_discount = None
        if data.get("max_discount_value"):
            try:
                max_discount = Decimal(str(data.get("max_discount_value")))
            except Exception:
                max_discount = None

        usage_limit = None
        if data.get("usage_limit") is not None and str(data.get("usage_limit")).strip() != "":
            try:
                usage_limit = int(data.get("usage_limit"))
                if usage_limit <= 0:
                    return {"success": False, "message": "O limite de usos deve ser maior que zero."}
            except Exception:
                return {"success": False, "message": "Limite de uso inválido."}

        valid_from = CouponService._parse_datetime(data.get("valid_from"))
        valid_until = CouponService._parse_datetime(data.get("valid_until"))

        if valid_from and valid_until and valid_until < valid_from:
            return {"success": False, "message": "A data de expiração deve ser posterior à data de início."}

        coupon = Coupon(
            code=code,
            description=data.get("description", "").strip(),
            discount_type=discount_type,
            discount_value=discount_value,
            min_purchase_value=min_purchase,
            max_discount_value=max_discount,
            usage_limit=usage_limit,
            usage_count=0,
            valid_from=valid_from,
            valid_until=valid_until,
            status=bool(data.get("status", True)),
            user_id=user_id,
            created_at=datetime.now()
        )

        try:
            db.session.add(coupon)
            db.session.commit()
            return {"success": True, "message": f"Cupom '{code}' criado com sucesso!", "cupom": coupon.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao salvar cupom: {str(e)}"}

    @staticmethod
    def update_coupon(user_id, coupon_id, data):
        coupon = (
            db.session.query(Coupon)
            .filter(Coupon.id == coupon_id, Coupon.user_id == user_id)
            .first()
        )
        if not coupon:
            return {"success": False, "message": "Cupom não encontrado."}

        if "code" in data:
            code = str(data["code"]).strip().upper()
            if not code:
                return {"success": False, "message": "O código não pode ser vazio."}
            existing = (
                db.session.query(Coupon)
                .filter(Coupon.user_id == user_id, Coupon.code == code, Coupon.id != coupon_id)
                .first()
            )
            if existing:
                return {"success": False, "message": f"Já existe outro cupom com o código '{code}'."}
            coupon.code = code

        if "description" in data:
            coupon.description = str(data["description"]).strip()

        if "discount_type" in data:
            if data["discount_type"] in ["percentage", "fixed"]:
                coupon.discount_type = data["discount_type"]

        if "discount_value" in data:
            try:
                val = Decimal(str(data["discount_value"]))
                if val <= 0:
                    return {"success": False, "message": "Valor de desconto deve ser positivo."}
                if coupon.discount_type == "percentage" and val > 100:
                    return {"success": False, "message": "Porcentagem não pode exceder 100%."}
                coupon.discount_value = val
            except Exception:
                return {"success": False, "message": "Valor de desconto inválido."}

        if "min_purchase_value" in data:
            try:
                coupon.min_purchase_value = Decimal(str(data["min_purchase_value"] or 0))
            except Exception:
                pass

        if "max_discount_value" in data:
            try:
                val = data["max_discount_value"]
                coupon.max_discount_value = Decimal(str(val)) if val else None
            except Exception:
                pass

        if "usage_limit" in data:
            try:
                val = data["usage_limit"]
                coupon.usage_limit = int(val) if (val is not None and str(val).strip() != "") else None
            except Exception:
                pass

        if "valid_from" in data:
            coupon.valid_from = CouponService._parse_datetime(data["valid_from"])

        if "valid_until" in data:
            coupon.valid_until = CouponService._parse_datetime(data["valid_until"])

        if "status" in data:
            coupon.status = bool(data["status"])

        try:
            db.session.commit()
            return {"success": True, "message": "Cupom atualizado com sucesso!", "cupom": coupon.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao atualizar cupom: {str(e)}"}

    @staticmethod
    def toggle_status(user_id, coupon_id):
        coupon = (
            db.session.query(Coupon)
            .filter(Coupon.id == coupon_id, Coupon.user_id == user_id)
            .first()
        )
        if not coupon:
            return {"success": False, "message": "Cupom não encontrado."}

        coupon.status = not coupon.status
        try:
            db.session.commit()
            status_text = "ativado" if coupon.status else "desativado"
            return {"success": True, "message": f"Cupom '{coupon.code}' {status_text} com sucesso!", "cupom": coupon.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao alterar status: {str(e)}"}

    @staticmethod
    def delete_coupon(user_id, coupon_id):
        coupon = (
            db.session.query(Coupon)
            .filter(Coupon.id == coupon_id, Coupon.user_id == user_id)
            .first()
        )
        if not coupon:
            return {"success": False, "message": "Cupom não encontrado."}

        # Check if used in sales
        used_in_sales = (
            db.session.query(Sale)
            .filter(Sale.coupon_id == coupon_id)
            .first()
        )
        if used_in_sales or coupon.usage_count > 0:
            coupon.status = False
            db.session.commit()
            return {
                "success": True,
                "message": f"O cupom '{coupon.code}' já possui histórico de vendas e foi inativado com sucesso.",
                "soft_deleted": True
            }

        try:
            db.session.delete(coupon)
            db.session.commit()
            return {"success": True, "message": f"Cupom '{coupon.code}' removido com sucesso!"}
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"Erro ao excluir cupom: {str(e)}"}

    @staticmethod
    def validate_coupon(user_id, code, subtotal):
        if not code:
            return {"success": False, "message": "Informe o código do cupom."}

        code_clean = str(code).strip().upper()
        coupon = (
            db.session.query(Coupon)
            .filter(Coupon.user_id == user_id, Coupon.code == code_clean)
            .first()
        )
        if not coupon:
            return {"success": False, "message": f"Cupom '{code_clean}' não encontrado."}

        if not coupon.status:
            return {"success": False, "message": f"O cupom '{code_clean}' está desativado."}

        now = datetime.now()
        if coupon.valid_from and coupon.valid_from > now:
            return {"success": False, "message": f"O cupom '{code_clean}' só será válido a partir de {coupon.valid_from.strftime('%d/%m/%Y %H:%M')}."}

        if coupon.valid_until and coupon.valid_until < now:
            return {"success": False, "message": f"O cupom '{code_clean}' expirou em {coupon.valid_until.strftime('%d/%m/%Y %H:%M')}."}

        if coupon.usage_limit is not None and coupon.usage_count >= coupon.usage_limit:
            return {"success": False, "message": f"O cupom '{code_clean}' atingiu o limite máximo de {coupon.usage_limit} utilizações."}

        try:
            subtotal_dec = Decimal(str(subtotal))
        except Exception:
            return {"success": False, "message": "Subtotal da compra inválido."}

        min_val = Decimal(str(coupon.min_purchase_value or 0))
        if subtotal_dec < min_val:
            return {
                "success": False,
                "message": f"O cupom '{code_clean}' exige uma compra mínima de R$ {min_val:.2f}. Seu subtotal atual é R$ {subtotal_dec:.2f}."
            }

        # Calculate discount
        if coupon.discount_type == "percentage":
            pct = Decimal(str(coupon.discount_value)) / Decimal("100")
            calc_discount = subtotal_dec * pct
            if coupon.max_discount_value is not None:
                max_disc = Decimal(str(coupon.max_discount_value))
                calc_discount = min(calc_discount, max_disc)
        else:
            calc_discount = min(Decimal(str(coupon.discount_value)), subtotal_dec)

        calc_discount = round(calc_discount, 2)
        total_price = max(Decimal("0.00"), subtotal_dec - calc_discount)

        return {
            "success": True,
            "message": f"Cupom '{code_clean}' aplicado com sucesso!",
            "coupon": coupon.to_dict(),
            "coupon_id": coupon.id,
            "coupon_code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
            "discount_applied": float(calc_discount),
            "subtotal": float(subtotal_dec),
            "total_price": float(total_price)
        }
