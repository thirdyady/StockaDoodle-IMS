import os
from flask import Flask, jsonify
from mongoengine import connect
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'stockadoodle-dev-2025')
    connect (
        db = os.getenv('DATABASE_NAME', 'stockadoodle'),
        host = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
        )
    
    # Import models AFTER init_app
    with app.app_context():
        from models import category, product, api_activity_log, product_log, retailer_metrics, sale, stock_batch, user

    # Register blueprint
    from routes.products import bp as products_bp
    app.register_blueprint(products_bp, url_prefix='/api/v1/products')
    
    # Register blueprint
    from routes.category import bp as category_bp
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
    
    # Register blueprint
    from routes.logs import bp as logs_bp
    app.register_blueprint(logs_bp, url_prefix='/api/v1/log')
    
    # Register blueprint
    from routes.sales import bp as sales_bp
    app.register_blueprint(sales_bp, url_prefix='/api/v1/sales')
    
    # Register blueprint
    from routes.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    
    # Dashboard blueprint
    from routes.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1/dashboard')
    
    # Metrics blueprint
    from routes.metrics import bp as metrics_bp
    app.register_blueprint(metrics_bp, url_prefix='/api/v1/retailer')
    
    # Reports blueprint
    from routes.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    
    # Notifications blueprint
    from routes.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/api/v1/notifications')

    @app.route('/api/v1')
    def home():
        return jsonify({
            "message": "StockaDoodle API LIVE!",
            "status": "Production Ready",
            "database": "MongoDB"
        })

    @app.route('/api/v1/health')
    def health():
        return jsonify({"status": "healthy"}), 200

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=True)