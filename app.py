import os
import logging
from flask import Flask, render_template, flash
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from db import init_db, mongo
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize extensions
mail = Mail()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "로그인이 필요한 페이지입니다."
login_manager.login_message_category = "info"

def create_app():
    app = Flask(__name__, static_url_path="/static")
    app.config.from_object(Config)
    
    # Set secret key from environment
    app.secret_key = os.environ.get("SESSION_SECRET", app.config["SECRET_KEY"])
    
    # Initialize extensions
    if not init_db(app):
        logging.error("Failed to initialize database")
    
    mail.init_app(app)
    login_manager.init_app(app)
    
    # Import and register blueprints
    from blueprints.auth import auth_bp
    from blueprints.products import products_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.notifications import notifications_bp
    
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(notifications_bp, url_prefix="/notifications")
    
    # Main routes
    @app.route("/")
    def index():
        return render_template("index.html", now=datetime.utcnow())
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        flash("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", "error")
        return render_template("500.html"), 500
    
    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
