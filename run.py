#!/usr/bin/env python3
# File: run.py
import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from config import FLASK_HOST, FLASK_PORT

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🎯 ADDIS BINGO - Complete Gaming Platform")
    print("=" * 60)
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    print(f"Server: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"Admin Panel: http://{FLASK_HOST}:{FLASK_PORT}/admin")
    print(f"Health Check: http://{FLASK_HOST}:{FLASK_PORT}/api/health")
    print(f"WebApp URL: https://updated-eight-ashy.vercel.app/")
    print("=" * 60)
    print("📱 Telegram Bot: @addis_bingo_admin")
    print("💰 CBE Account: 100348220032 (SAMSON MESFIN)")
    print("📱 Telebirr: 0976233815 (NITSU)")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)