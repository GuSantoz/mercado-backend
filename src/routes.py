from src.Application.Controllers.sale_controller import SaleController
from src.Application.Controllers.user_controller import UserController
from src.Application.Controllers.product_controller import ProductController
from src.Application.Controllers.coupon_controller import CouponController
from flask import jsonify, make_response, send_from_directory
from src.Infrastructure.storage.image_storage import get_upload_folder

def init_routes(app):    
    @app.route('/api', methods=['GET'])
    def health():
        return make_response(jsonify({
            "mensagem": "API - OK; Docker - Up",
        }), 200)
    
    @app.route('/users', methods=['GET'])
    def get_all_users():
        return UserController.get_all_users()
    
    @app.route('/user', methods=['POST'])
    def register_user():
        return UserController.register_user()

    @app.route('/user/activate', methods=['POST'])
    def activate_user():
        return UserController.activate_user()

    @app.route('/login', methods=["POST"])
    def login():
        return UserController.login()
    
    @app.route('/user', methods=['GET'])
    def get_user():
        return UserController.get_user()
    
    @app.route('/user', methods=['PUT'])
    def update_user():
        return UserController.update_user()
    
    @app.route('/product', methods=['GET'])
    def get_all_products():
        return ProductController.get_all_products()
    
    @app.route('/product', methods=['POST'])
    def create_product():
        return ProductController.create_product()

    @app.route('/product/upload', methods=['POST'])
    def upload_product_image():
        return ProductController.upload_image()

    @app.route('/uploads/<path:filename>')
    def serve_product_image(filename):
        return send_from_directory(get_upload_folder(), filename)
    
    @app.route('/product', methods=['PUT'])
    def update_product():
        return ProductController.update_product()
    
    @app.route('/product/status', methods=['PUT'])
    def update_status_product():
        return ProductController.update_status_product()
        
    @app.route('/venda', methods=['POST'])
    def create_venda():
        return SaleController.create_venda()
    
    @app.route('/venda', methods=['GET'])
    def get_all_vendas():
        return SaleController.get_all_vendas()

    @app.route('/venda/status', methods=['PUT'])
    def update_status_sale():
        return SaleController.update_status_sale()

    # --- ROTAS DE CUPONS DE DESCONTO ---
    @app.route('/coupon', methods=['GET'])
    def get_all_coupons():
        return CouponController.get_all_coupons()

    @app.route('/coupon', methods=['POST'])
    def create_coupon():
        return CouponController.create_coupon()

    @app.route('/coupon/<int:coupon_id>', methods=['GET'])
    def get_coupon_by_id(coupon_id):
        return CouponController.get_coupon_by_id(coupon_id)

    @app.route('/coupon/<int:coupon_id>', methods=['PUT'])
    def update_coupon(coupon_id):
        return CouponController.update_coupon(coupon_id)

    @app.route('/coupon/<int:coupon_id>/status', methods=['PUT'])
    def toggle_coupon_status(coupon_id):
        return CouponController.toggle_status(coupon_id)

    @app.route('/coupon/<int:coupon_id>', methods=['DELETE'])
    def delete_coupon(coupon_id):
        return CouponController.delete_coupon(coupon_id)

    @app.route('/coupon/validate', methods=['POST'])
    def validate_coupon():
        return CouponController.validate_coupon()