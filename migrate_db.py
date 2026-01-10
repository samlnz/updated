#!/usr/bin/env python3
# File: migrate_db.py
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    print("🔧 Creating database tables...")
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
        print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)