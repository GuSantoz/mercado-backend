from flask import request, jsonify, make_response
from src.Application.Service.user_service import UserService
from src.Application.Service.coupon_service import CouponService

class CouponController:

    @staticmethod
    def _authenticate():
        token = request.headers.get("Authorization")
        if not token:
            return None, make_response(jsonify({"erro": "Token não fornecido"}), 401)

        token_validation = UserService.validate_token(token)
        if not token_validation.get("success"):
            return None, make_response(jsonify({"erro": token_validation.get("message", "Token inválido")}), 401)

        return token_validation.get("user_id"), None

    @staticmethod
    def get_all_coupons():
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        coupons = CouponService.get_all_coupons(user_id)
        return make_response(
            jsonify({
                "mensagem": "Cupons listados com sucesso",
                "cupons": [c.to_dict() for c in coupons]
            }),
            200
        )

    @staticmethod
    def get_coupon_by_id(coupon_id):
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        coupon = CouponService.get_coupon_by_id(user_id, coupon_id)
        if not coupon:
            return make_response(jsonify({"erro": "Cupom não encontrado"}), 404)

        return make_response(
            jsonify({
                "mensagem": "Cupom encontrado",
                "cupom": coupon.to_dict()
            }),
            200
        )

    @staticmethod
    def create_coupon():
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        data = request.get_json()
        if not data:
            return make_response(jsonify({"erro": "Dados não fornecidos"}), 400)

        result = CouponService.create_coupon(user_id, data)
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 400)

        return make_response(
            jsonify({
                "mensagem": result["message"],
                "cupom": result["cupom"]
            }),
            201
        )

    @staticmethod
    def update_coupon(coupon_id):
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        data = request.get_json()
        if not data:
            return make_response(jsonify({"erro": "Dados para atualização não fornecidos"}), 400)

        result = CouponService.update_coupon(user_id, coupon_id, data)
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 400)

        return make_response(
            jsonify({
                "mensagem": result["message"],
                "cupom": result["cupom"]
            }),
            200
        )

    @staticmethod
    def toggle_status(coupon_id):
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        result = CouponService.toggle_status(user_id, coupon_id)
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 400)

        return make_response(
            jsonify({
                "mensagem": result["message"],
                "cupom": result["cupom"]
            }),
            200
        )

    @staticmethod
    def delete_coupon(coupon_id):
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        result = CouponService.delete_coupon(user_id, coupon_id)
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 400)

        return make_response(
            jsonify({
                "mensagem": result["message"],
                "soft_deleted": result.get("soft_deleted", False)
            }),
            200
        )

    @staticmethod
    def validate_coupon():
        user_id, err_response = CouponController._authenticate()
        if err_response:
            return err_response

        data = request.get_json()
        if not data:
            return make_response(jsonify({"erro": "Dados para validação não fornecidos"}), 400)

        code = data.get("code")
        subtotal = data.get("subtotal")

        if not code:
            return make_response(jsonify({"erro": "Código do cupom é obrigatório"}), 400)

        if subtotal is None:
            return make_response(jsonify({"erro": "Subtotal da compra é obrigatório"}), 400)

        result = CouponService.validate_coupon(user_id, code, subtotal)
        if not result["success"]:
            return make_response(jsonify({"erro": result["message"]}), 400)

        return make_response(
            jsonify({
                "mensagem": result["message"],
                "dados": result
            }),
            200
        )
