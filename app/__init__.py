# app/__init__.py
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = "winners"

    # Import and register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.api_routes import api_bp
    from .routes.chat_routes import chat_bp  # Updated import

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(chat_bp)  # Register the new chat blueprint

    # Initialize the database
    from .models import init_db
    init_db()

    return app
