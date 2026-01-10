# File: wsgi.py
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import and create the Flask app
from app import create_app

app = create_app()

if __name__ == "__main__":
    # This is for local development
    from config import FLASK_HOST, FLASK_PORT
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)