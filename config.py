# File: config.py
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Flask Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Database - Use Render's PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///instance/addis_bingo.db')

# Parse database URL for SQLAlchemy
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "connect_args": {
        "sslmode": "require"
    }
}

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8502890042:AAG3OO2L-1g1GFz4MUcENizttUvZC1aHspM')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '340864668').split(',')]
BOT_ADMIN_USERNAME = os.getenv('BOT_ADMIN_USERNAME', 'addis_bingo_admin')

# Admin Panel
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'SecurePass123!')
ADMIN_PORT = int(os.getenv('ADMIN_PORT', '5001'))

# Web URLs
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://updated-eight-ashy.vercel.app/')

# Game Settings
GAME_PRICES = [int(price.strip()) for price in os.getenv('GAME_PRICES', '10,20,50,100').split(',')]
MIN_PLAYERS = int(os.getenv('MIN_PLAYERS', '2'))
MAX_PLAYERS = int(os.getenv('MAX_PLAYERS', '10'))
SELECTION_TIME = int(os.getenv('SELECTION_TIME', '60'))
GAME_TIMEOUT = int(os.getenv('GAME_TIMEOUT', '300'))
REFERRAL_BONUS = float(os.getenv('REFERRAL_BONUS', '100'))
MIN_WITHDRAWAL = float(os.getenv('MIN_WITHDRAWAL', '100'))
MIN_DEPOSIT = float(os.getenv('MIN_DEPOSIT', '10'))

# Bank Accounts (Using YOUR exact values)
BANK_ACCOUNTS = {
    "CBE": {
        "account_number": os.getenv('CBE_ACCOUNT_NUMBER', '100348220032'),
        "account_name": os.getenv('CBE_ACCOUNT_NAME', 'SAMSON MESFIN')
    },
    "Telebirr": {
        "account_number": os.getenv('TELEBIRR_PHONE', '0976233815'),
        "account_name": os.getenv('TELEBIRR_ACCOUNT_NAME', 'NITSU')
    },
    "Dashen": {
        "account_number": os.getenv('DASHEN_ACCOUNT_NUMBER', '1234567890'),
        "account_name": os.getenv('DASHEN_ACCOUNT_NAME', 'addis bingo')
    }
}

# Server Configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Security
SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'your-encryption-key-here')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'addis_bingo.log')