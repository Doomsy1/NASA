# app/__init__.py
from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.secret_key = "winners"

    # Initialize SocketIO
    socketio.init_app(app)

    # Import and register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.main_routes import main_bp
    from .routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Import SocketIO events to ensure they're registered
    from .routes import socketio_events

    # Initialize the database
    from .models import init_db
    init_db()

    return app
