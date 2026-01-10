#!/usr/bin/env python3
# File: run_bot.py
import asyncio
import logging
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.bot_handlers import main as bot_main
from config import LOG_LEVEL, LOG_FILE

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the bot"""
    try:
        logger.info("🎯 Starting Addis Bingo Telegram Bot...")
        logger.info("🤖 Bot Token: 8502890042:AAG3OO2L-1g1GFz4MUcENizttUvZC1aHspM")
        logger.info("🌐 WebApp URL: https://updated-eight-ashy.vercel.app/")
        logger.info("💳 CBE Account: 100348220032 (SAMSON MESFIN)")
        logger.info("📱 Telebirr: 0976233815 (NITSU)")
        logger.info("🔄 Bot is now running. Press Ctrl+C to stop.")
        
        # Run the bot
        asyncio.run(bot_main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error in bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()