import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Web URLs
WEB_URL = os.getenv("WEB_URL", "https://updated-eight-ashy.vercel.app")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://updated-eight-ashy.vercel.app")

# Admin Panel
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# Payment Accounts
CBE_ACCOUNT_NAME = os.getenv("CBE_ACCOUNT_NAME", "SAMSON MESFIN")
CBE_ACCOUNT_NUMBER = os.getenv("CBE_ACCOUNT_NUMBER", "100348220032")
TELEBIRR_NAME = os.getenv("TELEBIRR_NAME", "NITSU")
TELEBIRR_NUMBER = os.getenv("TELEBIRR_NUMBER", "0976233815")
YOUR_PHONE = os.getenv("YOUR_PHONE_NUMBER", "0941043869")

# Game Configuration
MIN_PLAYERS = int(os.getenv("MIN_PLAYERS", 2))
GAME_PRICES = [int(x) for x in os.getenv("ENTRY_PRICES", "10,20,50,100").split(",")]
MIN_WITHDRAWAL = int(os.getenv("MIN_WITHDRAWAL", 100))
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", 20))
MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", 100))
CARTELA_SIZE = 100
BINGO_NUMBERS = 75

# Flask Configuration
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
DEBUG = True