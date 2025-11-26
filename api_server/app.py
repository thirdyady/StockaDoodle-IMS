import os
from flask import Flask, jsonify
from extensions import db, migrate
from dotenv import load_dotenv

load_dotenv()

# Make DB path absolute inside api_server
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'stockadoodle.db')

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'stockadoodle-dev-2025')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ← CRITICAL: These two lines MUST be here!
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models AFTER init_app
    with app.app_context():
        from models import category, product, api_activity_log, product_log, retailer_metrics, sale, stock_batch, user
        db.create_all()

    # Register blueprint
    from routes.products import bp as products_bp
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    
    # Register blueprint
    from routes.category import bp as category_bp
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
    
    # Register blueprint
    from routes.logs import bp as logs_bp
    app.register_blueprint(logs_bp, url_prefix='/api/v1/logs')
    
    # Register blueprint
    from routes.sales import bp as sales_bp
    app.register_blueprint(sales_bp, url_prefix='/api/v1/sales')
    
    # Register blueprint
    from routes.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')

    @app.route('/api/v1')
    def home():
        return jsonify({
            "message": "StockaDoodle API LIVE!",
            "status": "Production Ready",
            "database": "stockadoodle.db"
        })

    @app.route('/api/v1/health')
    def health():
        return jsonify({"status": "healthy"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)