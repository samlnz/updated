import asyncio
import threading
from multiprocessing import Process
import signal
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask():
    """Run Flask web application"""
    from app import app
    logger.info("Starting Flask web application...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    """Run Telegram bot"""
    import asyncio
    from bot import main as bot_main
    logger.info("Starting Telegram bot...")
    asyncio.run(bot_main())

def run_admin():
    """Run admin panel"""
    from admin_panel import app as admin_app
    logger.info("Starting admin panel...")
    admin_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    print("\n" + "="*50)
    print("Shutting down Bingo Bot System...")
    print("="*50)
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("="*50)
    print("🚀 STARTING ADDIS BINGO BOT SYSTEM")
    print("="*50)
    
    # Initialize database
    from app import app as flask_app
    from database import db
    with flask_app.app_context():
        db.create_all()
        logger.info("Database initialized")
    
    # Run services in separate threads
    services = []
    
    # Flask web app
    flask_thread = threading.Thread(target=run_flask, daemon=True, name="Flask-Web")
    services.append(flask_thread)
    
    # Admin panel
    admin_thread = threading.Thread(target=run_admin, daemon=True, name="Admin-Panel")
    services.append(admin_thread)
    
    # Start all services
    for service in services:
        service.start()
        logger.info(f"Started {service.name}")
    
    # Start bot in main thread
    try:
        print("\n" + "="*50)
        print("✅ ALL SERVICES STARTED SUCCESSFULLY")
        print("="*50)
        print(f"\n🌐 Web Application: http://localhost:5000")
        print(f"🤖 Telegram Bot: Running...")
        print(f"👑 Admin Panel: http://localhost:5001/admin/login")
        print(f"\n📱 Your Phone: 0941043869")
        print(f"🏦 CBE Account: SAMSON MESFIN - 100348220032")
        print(f"📱 TeleBirr: NITSU - 0976233815")
        print("\n" + "="*50)
        print("Press Ctrl+C to stop all services")
        print("="*50 + "\n")
        
        # Run bot in main thread
        run_bot()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down... Goodbye!")
    except Exception as e:
        logger.error(f"Error running bot: {str(e)}")
    finally:
        sys.exit(0)