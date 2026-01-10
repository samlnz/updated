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
    app = Flask(__name__)
    
    # Load configuration
    from config import SECRET_KEY, DATABASE_URL, SQLALCHEMY_TRACK_MODIFICATIONS
    
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from app import routes, admin_routes
    app.register_blueprint(routes.bp)
    app.register_blueprint(admin_routes.bp, url_prefix='/admin')
    
    # Create database tables
    with app.app_context():
        try:
            from app import models
            db.create_all()
            logging.info("Database tables created successfully!")
        except Exception as e:
            logging.error(f"Error creating database tables: {e}")
    
    return app