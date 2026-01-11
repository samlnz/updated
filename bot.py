import os
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp

from config import (
    TELEGRAM_BOT_TOKEN, WEBAPP_URL,
    CBE_ACCOUNT_NAME, CBE_ACCOUNT_NUMBER,
    TELEBIRR_NAME, TELEBIRR_NUMBER,
    GAME_PRICES, MIN_WITHDRAWAL, REFERRAL_BONUS,
    YOUR_PHONE
)
from database import db
from models import User, Transaction

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# States
class UserStates(StatesGroup):
    waiting_for_deposit = State()
    waiting_for_withdrawal = State()
    waiting_for_phone = State()

# Keyboard layouts
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Play Bingo"), KeyboardButton(text="💰 Balance")],
            [KeyboardButton(text="➕ Deposit"), KeyboardButton(text="➖ Withdraw")],
            [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="🎁 Referral")],
            [KeyboardButton(text="❓ Help")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an option..."
    )

def get_game_prices_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for price in GAME_PRICES:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{price} Birr Game",
                web_app=WebAppInfo(url=f"{WEBAPP_URL}/lobby?price={price}")
            )
        ])
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        
        # Check for referral code in start parameters
        referral_code = None
        if len(message.text.split()) > 1:
            referral_code = message.text.split()[1]
        
        # Check if user exists
        user = User.query.filter_by(telegram_id=user_id).first()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                referral_code=f"REF{user_id % 10000:04d}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Handle referral
            if referral_code:
                referrer = User.query.filter_by(referral_code=referral_code).first()
                if referrer:
                    user.referrer_id = referrer.id
                    # Give referral bonus
                    referrer.balance += REFERRAL_BONUS
                    transaction = Transaction(
                        user_id=referrer.id,
                        type='referral',
                        amount=REFERRAL_BONUS,
                        status='completed',
                        description=f'Referral bonus from {username}',
                        created_at=datetime.utcnow(),
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(transaction)
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"New user registered: {user_id} ({username})")
            
            # Ask for phone number
            await message.answer(
                "🎉 *Welcome to Addis Bingo Bot!* 🎮\n\n"
                "To process deposits and withdrawals, we need your phone number.\n\n"
                "Please share your phone number by clicking the button below:",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📱 Share Phone", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
        else:
            # Existing user - show main menu
            await show_main_menu(message, user)
            
    except Exception as e:
        logger.error(f"Error in /start command: {str(e)}")
        await message.answer("❌ An error occurred. Please try again.")

@router.message(lambda message: message.contact)
async def handle_contact(message: Message):
    """Handle phone number sharing"""
    try:
        if message.contact.user_id != message.from_user.id:
            await message.answer("Please share your own phone number.")
            return
        
        phone = message.contact.phone_number
        user = User.query.filter_by(telegram_id=message.from_user.id).first()
        
        if user:
            user.phone = phone
            db.session.commit()
            
            # Generate referral message
            bot_info = await bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start={user.referral_code}"
            
            await message.answer(
                f"✅ *Phone number registered:* {phone}\n\n"
                f"🎁 *Referral Program*\n"
                f"Share this link with friends:\n`{referral_link}`\n\n"
                f"*Earn {REFERRAL_BONUS} Birr* when they:\n"
                f"1️⃣ Register with your link\n"
                f"2️⃣ Make first deposit\n"
                f"3️⃣ Play first game\n",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove()
            )
            
            await show_main_menu(message, user)
            
    except Exception as e:
        logger.error(f"Error handling contact: {str(e)}")
        await message.answer("❌ Error saving phone number. Please try again.")

async def show_main_menu(message: Message, user: User = None):
    """Show main menu with user balance"""
    if not user:
        user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    welcome_text = (
        f"🏠 *Main Menu*\n\n"
        f"👤 {user.first_name or user.username}\n"
        f"💰 Balance: *{user.balance:.2f} Birr*\n"
        f"📞 Phone: {user.phone or 'Not set'}\n"
        f"🎮 Games Played: {user.games_played}\n"
        f"🏆 Games Won: {user.games_won}\n\n"
        f"*Choose an option below:*"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@router.message(lambda message: message.text == "🎮 Play Bingo")
async def play_bingo(message: Message):
    """Show game price options"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    if not user.phone:
        await message.answer(
            "Please share your phone number first to play games.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="📱 Share Phone", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return
    
    await message.answer(
        "🎰 *Select Game Price*\n\n"
        "Choose your entry price to join a Bingo game:",
        parse_mode="Markdown",
        reply_markup=get_game_prices_keyboard()
    )

@router.message(lambda message: message.text == "💰 Balance")
async def show_balance(message: Message):
    """Show user balance and transaction history"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    # Get recent transactions
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    balance_text = (
        f"💰 *Your Balance*\n\n"
        f"Current: *{user.balance:.2f} Birr*\n"
        f"Games Played: {user.games_played}\n"
        f"Games Won: {user.games_won}\n\n"
        f"*Recent Transactions:*\n"
    )
    
    if transactions:
        for tx in transactions:
            emoji = "➕" if tx.amount > 0 else "➖"
            status_emoji = "✅" if tx.status == 'completed' else "⏳" if tx.status == 'pending' else "❌"
            balance_text += f"{emoji} {abs(tx.amount):.2f} Birr - {tx.type} {status_emoji}\n"
    else:
        balance_text += "No transactions yet.\n"
    
    balance_text += f"\n*To add funds:* Use ➕ Deposit"
    
    await message.answer(balance_text, parse_mode="Markdown")

@router.message(lambda message: message.text == "➕ Deposit")
async def deposit(message: Message):
    """Show deposit instructions"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    if not user.phone:
        await message.answer("Please share your phone number first to make deposits.")
        return
    
    deposit_instructions = (
        "💳 *Deposit Instructions*\n\n"
        "*Send money to one of these accounts:*\n\n"
        f"🏦 *CBE Bank*\n"
        f"Name: *{CBE_ACCOUNT_NAME}*\n"
        f"Account: `{CBE_ACCOUNT_NUMBER}`\n\n"
        f"📱 *TeleBirr*\n"
        f"Name: *{TELEBIRR_NAME}*\n"
        f"Number: `{TELEBIRR_NUMBER}`\n\n"
        "*Important Notes:*\n"
        "1. Send the exact amount you want to deposit\n"
        "2. Use your registered phone number as reference\n"
        "3. Deposits are processed automatically\n"
        "4. Contact @[AdminUsername] if you have issues\n\n"
        "*Your registered phone:* " + (user.phone or "Not set") + "\n\n"
        "After sending money, your balance will be updated automatically."
    )
    
    await message.answer(deposit_instructions, parse_mode="Markdown")

@router.message(lambda message: message.text == "➖ Withdraw")
async def withdraw(message: Message, state: FSMContext):
    """Handle withdrawal request"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    if not user.phone:
        await message.answer("Please share your phone number first to withdraw.")
        return
    
    if user.balance < MIN_WITHDRAWAL:
        await message.answer(
            f"❌ *Minimum withdrawal is {MIN_WITHDRAWAL} Birr*\n"
            f"Your balance: *{user.balance:.2f} Birr*\n\n"
            "Please deposit more funds to withdraw.",
            parse_mode="Markdown"
        )
        return
    
    # Set state and ask for amount
    await state.set_state(UserStates.waiting_for_withdrawal)
    await state.update_data(user_id=user.id)
    
    await message.answer(
        f"💸 *Withdrawal Request*\n\n"
        f"Your balance: *{user.balance:.2f} Birr*\n"
        f"Minimum withdrawal: *{MIN_WITHDRAWAL} Birr*\n\n"
        "Please enter the amount you want to withdraw:",
        parse_mode="Markdown"
    )

@router.message(UserStates.waiting_for_withdrawal)
async def process_withdrawal(message: Message, state: FSMContext):
    """Process withdrawal amount input"""
    try:
        amount = float(message.text)
        data = await state.get_data()
        user_id = data.get('user_id')
        
        user = User.query.get(user_id)
        
        if not user:
            await message.answer("User not found. Please start again with /start")
            await state.clear()
            return
        
        # Validate amount
        if amount < MIN_WITHDRAWAL:
            await message.answer(f"Minimum withdrawal is {MIN_WITHDRAWAL} Birr")
            return
        
        if amount > user.balance:
            await message.answer(
                f"Insufficient balance. You have {user.balance:.2f} Birr"
            )
            return
        
        # Create withdrawal transaction
        transaction = Transaction(
            user_id=user.id,
            type='withdrawal',
            amount=-amount,
            status='pending',
            description=f'Withdrawal request to {user.phone}',
            payment_method='telebirr',
            created_at=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        await message.answer(
            f"✅ *Withdrawal Request Submitted*\n\n"
            f"Amount: *{amount:.2f} Birr*\n"
            f"To: {user.phone}\n"
            f"Status: ⏳ Pending approval\n\n"
            "Your withdrawal will be processed within 24 hours.\n"
            "You will receive a notification when completed.",
            parse_mode="Markdown"
        )
        
        await state.clear()
        await show_main_menu(message, user)
        
    except ValueError:
        await message.answer("Please enter a valid number (e.g., 100, 200.50)")
    except Exception as e:
        logger.error(f"Error processing withdrawal: {str(e)}")
        await message.answer("❌ An error occurred. Please try again.")
        await state.clear()

@router.message(lambda message: message.text == "📊 My Stats")
async def show_stats(message: Message):
    """Show user statistics"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    # Calculate win rate
    win_rate = (user.games_won / user.games_played * 100) if user.games_played > 0 else 0
    
    stats_text = (
        f"📊 *Your Statistics*\n\n"
        f"👤 Name: {user.first_name or user.username}\n"
        f"📅 Member Since: {user.created_at.strftime('%Y-%m-%d')}\n\n"
        f"💰 Current Balance: *{user.balance:.2f} Birr*\n"
        f"🎮 Games Played: {user.games_played}\n"
        f"🏆 Games Won: {user.games_won}\n"
        f"📈 Win Rate: {win_rate:.1f}%\n\n"
        f"📞 Phone: {user.phone or 'Not set'}\n"
        f"🎁 Referral Code: `{user.referral_code}`"
    )
    
    await message.answer(stats_text, parse_mode="Markdown")

@router.message(lambda message: message.text == "🎁 Referral")
async def show_referral(message: Message):
    """Show referral information"""
    user = User.query.filter_by(telegram_id=message.from_user.id).first()
    
    if not user:
        await message.answer("Please use /start to register first.")
        return
    
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user.referral_code}"
    
    referral_text = (
        f"🎁 *Referral Program*\n\n"
        f"*Your Referral Code:* `{user.referral_code}`\n\n"
        f"*Share this link:*\n"
        f"`{referral_link}`\n\n"
        f"*Earn {REFERRAL_BONUS} Birr for each friend who:*\n"
        f"1️⃣ Registers with your link\n"
        f"2️⃣ Makes first deposit\n"
        f"3️⃣ Plays first game\n\n"
        f"*Your earnings will be added automatically!*"
    )
    
    await message.answer(referral_text, parse_mode="Markdown")

@router.message(lambda message: message.text == "❓ Help")
async def show_help(message: Message):
    """Show help information"""
    help_text = (
        "❓ *Help & Support*\n\n"
        "*Common Questions:*\n\n"
        "*How to deposit?*\n"
        "Use ➕ Deposit button to see account details\n\n"
        "*How to withdraw?*\n"
        f"Minimum withdrawal: {MIN_WITHDRAWAL} Birr\n"
        "Use ➖ Withdraw button\n\n"
        "*How to play?*\n"
        "Use 🎮 Play Bingo to join games\n\n"
        "*Game Rules:*\n"
        "1. Select cartela number (1-100)\n"
        "2. Mark numbers as they're called\n"
        "3. Complete a line/pattern to win\n"
        "4. Center is FREE space\n\n"
        "*Need more help?*\n"
        "Contact: @[AdminUsername]\n"
        "Phone: [Your Support Number]"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    await show_help(message)

async def main():
    """Start the bot"""
    dp.include_router(router)
    
    logger.info("Starting Telegram Bot...")
    
    # Delete webhook (if any) and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Create database tables if they don't exist
    from app import app
    with app.app_context():
        db.create_all()
    
    # Run the bot
    asyncio.run(main())