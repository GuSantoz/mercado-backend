import os
import socket
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def can_connect(host, port):
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.8)
        result = sock.connect_ex((host, int(port)))
        return result == 0
    except Exception:
        return False
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass


def init_db(app):
    mysql_user = os.getenv('MYSQL_ROOT_USER', 'root')
    mysql_password = os.getenv('MYSQL_ROOT_PASSWORD', 'root')
    mysql_host = os.getenv('MYSQL_HOST', 'mysql57')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_db = os.getenv('MYSQL_DATABASE', 'market_management')

    custom_uri = os.getenv('DATABASE_URI') or os.getenv('DATABASE_URL')
    if custom_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = custom_uri
    elif can_connect(mysql_host, mysql_port):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}'
    elif can_connect('127.0.0.1', 3307):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{mysql_user}:{mysql_password}@127.0.0.1:3307/{mysql_db}'
    elif can_connect('127.0.0.1', 3306):
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{mysql_user}:{mysql_password}@127.0.0.1:3306/{mysql_db}'
    else:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sqlite_path = os.path.join(backend_dir, "market_management.db").replace("\\", "/")
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{sqlite_path}"
        print(f"[Banco de Dados] MySQL não detectado. Utilizando SQLite local: {sqlite_path}")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy metadata registers all tables
        from src.Infrastructure.Model.user import User
        from src.Infrastructure.Model.product import Product
        from src.Infrastructure.Model.sale import Sale
        from src.Infrastructure.Model.sale_items import SaleItem
        from src.Infrastructure.Model.coupon import Coupon

        db.create_all()



