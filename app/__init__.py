# File: app/__init__.py
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Load configuration
    from config import SECRET_KEY, DATABASE_URL, SQLALCHEMY_TRACK_MODIFICATIONS, SQLALCHEMY_ENGINE_OPTIONS
    
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS
    
    # Configure logging
    configure_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app import routes, admin_routes, macrodroid_webhook
    app.register_blueprint(routes.bp)
    app.register_blueprint(admin_routes.bp, url_prefix='/admin')
    app.register_blueprint(macrodroid_webhook.bp)
    
    # Create database tables
    with app.app_context():
        try:
            from app import models
            db.create_all()
            app.logger.info("✅ Database tables created successfully!")
        except Exception as e:
            app.logger.error(f"❌ Error creating database tables: {e}")
    
    return app

def configure_logging(app):
    """Configure application logging"""
    from config import LOG_LEVEL, LOG_FILE
    
    # Set log level
    numeric_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    app.logger.setLevel(numeric_level)
    
    # Remove default handlers
    app.logger.handlers.clear()
    
    # File handler
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            LOG_FILE, 
            maxBytes=1024 * 1024 * 10,
            backupCount=10
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ Could not set up file logging: {e}")
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    app.logger.addHandler(console_handler)

# Import utility functions
from app import utils

# Make utils available
__all__ = ['create_app', 'db', 'utils']