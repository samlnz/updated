"""
Railway entry point for the Bingo Bot web app.
This file is required by Railway's deployment system.
"""

import os
import logging
from app import app as flask_app

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# This creates the 'app' object that Railway expects
app = flask_app

if __name__ == "__main__":
    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get("PORT", 5000))
    
    logger.info(f"🚀 Starting Bingo Bot on port {port}")
    
    # Start the Flask app
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False  # Set to False in production
    )