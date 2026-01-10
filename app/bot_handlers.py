# File: app/bot_handlers.py
import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    CallbackQuery
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from app import db, create_app
from app.models import User, Transaction
from config import TELEGRAM_BOT_TOKEN, WEBAPP_URL, GAME_PRICES, ADMIN_IDS, REFERRAL_BONUS, BANK_ACCOUNTS

logger = logging.getLogger(__name__)

# Create Flask app for context
flask_app = create_app()

# Bot setup
bot = Bot(
    token=TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# States
class UserState(StatesGroup):
    waiting_for_deposit_amount = State()
    waiting_for_withdrawal = State()

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command and registration"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        # Check for referral
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        referrer_id = int(args[0]) if args and args[0].isdigit() else None
        
        with flask_app.app_context():
            # Check if user exists
            user = User.query.filter_by(telegram_id=user_id).first()
            
            if not user:
                # Generate referral code
                import random
                import string
                referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                # New user registration
                user = User(
                    telegram_id=user_id,
                    username=username,
                    referral_code=referral_code,
                    referrer_id=referrer_id
                )
                db.session.add(user)
                db.session.commit()
                logger.info(f"New user registered: {user_id} ({username})")
                
                # Send welcome message
                await message.answer(
                    "🎯 Welcome to Addis Bingo!\n\n"
                    "Complete your registration by sharing your phone number."
                )
                
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                
                await message.answer(
                    "Please share your phone number to continue:",
                    reply_markup=keyboard
                )
            else:
                # Returning user - show main menu
                await show_main_menu(message)
                
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

async def show_main_menu(message: Message):
    """Show main menu with balance and options"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🎮 Play Bingo")],
                    [KeyboardButton(text="💰 Deposit"), KeyboardButton(text="💳 Withdraw")],
                    [KeyboardButton(text="📊 My Stats"), KeyboardButton(text="📞 Support")],
                    [KeyboardButton(text="👥 Refer Friends")]
                ],
                resize_keyboard=True
            )
            
            await message.answer(
                f"🎯 <b>Main Menu</b>\n\n"
                f"💰 Balance: <b>{user.balance:.2f} birr</b>\n"
                f"🎮 Games played: {user.games_played}\n"
                f"🏆 Games won: {user.games_won}\n\n"
                f"Choose an option:",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error showing main menu: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(F.contact)
async def process_phone_number(message: Message):
    """Handle shared contact information"""
    if not message.contact or message.contact.user_id != message.from_user.id:
        await message.answer("Please share your own contact information.")
        return
    
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please use /start first!")
                return
            
            user.phone = message.contact.phone_number
            db.session.commit()
            logger.info(f"Phone number registered for user: {message.from_user.id}")
            
            # Get bot info for referral link
            bot_info = await bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start={user.id}"
            
            await message.answer(
                f"✅ <b>Registration Complete!</b>\n\n"
                f"📱 Phone: {message.contact.phone_number}\n"
                f"🔗 Referral Code: <code>{user.referral_code}</code>\n\n"
                f"<b>Your Referral Link:</b>\n"
                f"{referral_link}\n\n"
                f"Share with friends and earn <b>{REFERRAL_BONUS} birr</b> when they:\n"
                f"1. Register using your link\n"
                f"2. Verify phone number\n"
                f"3. Make first deposit",
                reply_markup=ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML
            )
            
            # Show main menu
            await show_main_menu(message)
    except Exception as e:
        logger.error(f"Error processing phone number: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(F.text == "🎮 Play Bingo")
async def process_play_command(message: Message):
    """Handle play command - show game price options"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            
            if not user:
                await message.answer("Please register first using /start")
                return
            
            if not user.phone:
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                await message.answer("Please share your phone number first to play games.", reply_markup=keyboard)
                return
            
            if user.balance < min(GAME_PRICES):
                await message.answer(
                    f"⚠️ Insufficient balance. Minimum game entry is {min(GAME_PRICES)} birr.\n"
                    f"Please deposit first using the Deposit option."
                )
                return
            
            # Create buttons for each price option
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"{price} Birr",
                    callback_data=f"price_{price}"
                )] for price in GAME_PRICES
            ])
            
            await message.answer(
                "🎮 <b>Choose your game entry price:</b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error processing play command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.callback_query(lambda c: c.data.startswith('price_'))
async def process_price_selection(callback_query: CallbackQuery):
    """Handle price selection and create game"""
    try:
        # Extract price from callback data
        price = int(callback_query.data.split('_')[1])
        
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=callback_query.from_user.id).first()
            if not user:
                await callback_query.answer("User not found", show_alert=True)
                return
            
            if user.balance < price:
                await callback_query.answer("❌ Insufficient balance. Please deposit first.", show_alert=True)
                return
            
            # Create game URL
            game_url = f"{WEBAPP_URL}/game.html?user_id={user.id}&price={price}"
            
            # Create WebApp button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🎮 Play Now",
                    web_app=WebAppInfo(url=game_url)
                )
            ]])
            
            await callback_query.message.edit_text(
                f"🎯 <b>Ready to Play!</b>\n\n"
                f"Entry price: {price} Birr\n"
                f"Your balance: {user.balance:.2f} Birr\n\n"
                f"Click below to start playing:",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        logger.error(f"Error processing price selection: {e}")
        await callback_query.answer("❌ Sorry, there was an error. Please try again.", show_alert=True)

@router.message(F.text == "💰 Deposit")
async def process_deposit_command(message: Message, state: FSMContext):
    """Handle deposit command"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            if not user.phone:
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
                await message.answer("Please share your phone number first.", reply_markup=keyboard)
                return
            
            from config import MIN_DEPOSIT
            await state.set_state(UserState.waiting_for_deposit_amount)
            await message.answer(
                "💰 <b>Deposit Instructions</b>\n\n"
                f"Enter the amount you want to deposit (in birr):\n\n"
                f"Minimum: {MIN_DEPOSIT} birr\n"
                f"Maximum: 10,000 birr\n\n"
                f"Example: <code>100</code>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error processing deposit command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(UserState.waiting_for_deposit_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """Handle deposit amount input"""
    try:
        amount = float(message.text)
        
        from config import MIN_DEPOSIT
        if amount < MIN_DEPOSIT:
            await message.answer(f"⚠️ Minimum deposit amount is {MIN_DEPOSIT} birr")
            return
        if amount > 10000:
            await message.answer("⚠️ Maximum deposit amount is 10,000 birr")
            return
        
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            
            # Create pending transaction
            transaction = Transaction(
                user_id=user.id,
                type='deposit',
                amount=amount,
                status='pending',
                deposit_phone=user.phone
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Get bank account details (using YOUR values)
            await message.answer(
                f"✅ <b>Deposit Request Received</b>\n\n"
                f"Amount: {amount} birr\n"
                f"Status: Pending\n"
                f"Reference: TX{transaction.id:06d}\n\n"
                f"<b>Send money to one of these accounts:</b>\n\n"
                f"🏦 <b>CBE Account:</b>\n"
                f"Account: {BANK_ACCOUNTS['CBE']['account_number']}\n"
                f"Name: {BANK_ACCOUNTS['CBE']['account_name']}\n\n"
                f"📱 <b>Telebirr:</b>\n"
                f"Phone: {BANK_ACCOUNTS['Telebirr']['account_number']}\n"
                f"Name: {BANK_ACCOUNTS['Telebirr']['account_name']}\n\n"
                f"📝 <b>Important:</b>\n"
                f"• Include your phone number ({user.phone}) in transaction note\n"
                f"• Your deposit will be processed within 24 hours\n"
                f"• Contact support if you have issues\n\n"
                f"<b>After sending money:</b>\n"
                f"1. Keep the transaction receipt\n"
                f"2. Contact support if not credited within 24 hours",
                parse_mode=ParseMode.HTML
            )
            
            # Clear state
            await state.clear()
            await show_main_menu(message)
            
    except ValueError:
        await message.answer("⚠️ Please enter a valid number (e.g., 100)")
    except Exception as e:
        logger.error(f"Error processing deposit amount: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(F.text == "💳 Withdraw")
async def process_withdraw_command(message: Message, state: FSMContext):
    """Handle withdraw command"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            from config import MIN_WITHDRAWAL
            if user.balance < MIN_WITHDRAWAL:
                await message.answer(f"⚠️ Minimum withdrawal amount is {MIN_WITHDRAWAL} birr")
                return
            
            if user.games_played < 5:
                await message.answer("⚠️ You must play at least 5 games before withdrawing")
                return
            
            await state.set_state(UserState.waiting_for_withdrawal)
            await message.answer(
                f"💳 <b>Withdrawal Rules</b>\n\n"
                f"1. Minimum: {MIN_WITHDRAWAL} birr\n"
                f"2. Must have played at least 5 games\n"
                f"3. Processing time: 24 hours\n"
                f"4. Funds sent to: {user.phone}\n\n"
                f"Your current balance: {user.balance:.2f} birr\n\n"
                f"Reply with the amount you want to withdraw:",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error processing withdraw command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(UserState.waiting_for_withdrawal)
async def process_withdrawal_request(message: Message, state: FSMContext):
    """Handle withdrawal amount input"""
    try:
        amount = float(message.text)
        
        from config import MIN_WITHDRAWAL
        if amount < MIN_WITHDRAWAL:
            await message.answer(f"⚠️ Minimum withdrawal amount is {MIN_WITHDRAWAL} birr")
            return
        
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if amount > user.balance:
                await message.answer("⚠️ Insufficient balance")
                return
            
            # Create withdrawal transaction
            transaction = Transaction(
                user_id=user.id,
                type='withdraw',
                amount=-amount,
                status='pending',
                withdrawal_phone=user.phone
            )
            db.session.add(transaction)
            db.session.commit()
            
            await message.answer(
                f"✅ <b>Withdrawal Request Received!</b>\n\n"
                f"Amount: {amount} birr\n"
                f"Destination: {user.phone}\n"
                f"Status: Pending admin approval\n"
                f"Reference: W{transaction.id:06d}\n\n"
                f"You'll receive a notification once it's processed.",
                parse_mode=ParseMode.HTML
            )
            
    except ValueError:
        await message.answer("⚠️ Please enter a valid amount")
        return
    except Exception as e:
        logger.error(f"Error processing withdrawal request: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")
    
    await state.clear()
    await show_main_menu(message)

@router.message(F.text == "👥 Refer Friends")
async def process_refer_command(message: Message):
    """Handle refer friends command"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            # Get bot info for referral link
            bot_info = await bot.get_me()
            referral_link = f"https://t.me/{bot_info.username}?start={user.id}"
            
            # Count referrals
            referral_count = User.query.filter_by(referrer_id=user.id).count()
            
            await message.answer(
                f"👥 <b>Refer & Earn</b>\n\n"
                f"Your Referral Code: <code>{user.referral_code}</code>\n\n"
                f"<b>Your Referral Link:</b>\n"
                f"{referral_link}\n\n"
                f"📊 <b>Your Stats:</b>\n"
                f"Referrals: {referral_count}\n"
                f"Earned: {referral_count * REFERRAL_BONUS} birr\n\n"
                f"💰 <b>How it works:</b>\n"
                f"1. Share your link with friends\n"
                f"2. They register and verify phone\n"
                f"3. They make first deposit\n"
                f"4. You earn <b>{REFERRAL_BONUS} birr</b> per referral!\n\n"
                f"💡 <b>Tip:</b> Share on social media for more referrals!",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error processing refer command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(F.text == "📊 My Stats")
async def process_stats_command(message: Message):
    """Handle stats command"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            # Get transaction history
            transactions = Transaction.query.filter_by(user_id=user.id)\
                .order_by(Transaction.created_at.desc())\
                .limit(5)\
                .all()
            
            # Calculate win rate
            win_rate = (user.games_won / user.games_played * 100) if user.games_played > 0 else 0
            
            stats = (
                f"📊 <b>Your Stats</b>\n\n"
                f"💰 Current Balance: {user.balance:.2f} birr\n"
                f"🎮 Games Played: {user.games_played}\n"
                f"🏆 Games Won: {user.games_won}\n"
                f"📈 Win Rate: {win_rate:.1f}%\n\n"
                f"<b>Recent Transactions:</b>\n"
            )
            
            for tx in transactions:
                emoji = "➕" if tx.amount > 0 else "➖"
                sign = "+" if tx.amount > 0 else ""
                stats += f"{emoji} {sign}{tx.amount:.2f} birr - {tx.type} ({tx.status})\n"
            
            if not transactions:
                stats += "No transactions yet.\n"
            
            stats += f"\n📱 Phone: {user.phone}\n"
            stats += f"🔗 Referral Code: {user.referral_code}"
            
            await message.answer(stats, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Error processing stats command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(F.text == "📞 Support")
async def process_support_command(message: Message):
    """Handle support command"""
    support_message = (
        "📞 <b>Support & Contact</b>\n\n"
        "For any issues, questions, or assistance:\n\n"
        "📧 Email: support@addisbingo.com\n"
        "📱 Telegram: @addisbingo_support\n\n"
        "<b>Operating Hours:</b>\n"
        "24/7 Support Available\n\n"
        "Please provide your User ID when contacting support:\n"
        f"<code>{message.from_user.id}</code>"
    )
    
    await message.answer(support_message, parse_mode=ParseMode.HTML)

@router.message(Command("macrodroid"))
async def cmd_macrodroid(message: Message):
    """Send Macrodroid setup instructions"""
    try:
        with flask_app.app_context():
            user = User.query.filter_by(telegram_id=message.from_user.id).first()
            if not user:
                await message.answer("Please register first using /start")
                return
            
            instructions = (
                "📱 <b>Macrodroid Auto-Deposit Setup</b>\n\n"
                "Automatically forward deposit SMS to instantly update your balance!\n\n"
                "<b>Step 1:</b> Install Macrodroid from Play Store\n"
                "<b>Step 2:</b> Create new macro with:\n"
                "   • Trigger: SMS Received\n"
                "   • Sender: (leave empty)\n"
                "   • Content: Contains 'ETB' or 'ብር'\n\n"
                "<b>Step 3:</b> Add HTTP Post action:\n"
                f"   • URL: <code>{WEBAPP_URL}/webhook/macrodroid</code>\n"
                "   • Method: POST\n"
                "   • Headers: Content-Type: application/json\n"
                "   • Body:\n"
                "<code>{\n"
                '  "sms_text": "{sms_body}",\n'
                '  "sender_number": "{sms_sender}",\n'
                '  "timestamp": "{datetime}",\n'
                '  "device_id": "{device_id}"\n'
                "}</code>\n\n"
                "<b>Step 4:</b> Test with small deposit\n\n"
                "<b>Need help?</b> Send /support\n"
                "<b>Test webhook:</b> /testwebhook"
            )
            
            await message.answer(instructions, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Error in macrodroid command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

@router.message(Command("testwebhook"))
async def cmd_test_webhook(message: Message):
    """Test Macrodroid webhook"""
    try:
        test_sms = "You have received 10.00 ETB from 0912345678. Your new balance is 100.00 ETB."
        
        test_instructions = (
            "🔧 <b>Webhook Testing</b>\n\n"
            f"<b>Test URL:</b> <code>{WEBAPP_URL}/webhook/macrodroid/test</code>\n\n"
            "<b>Test with this SMS:</b>\n"
            f"<code>{test_sms}</code>\n\n"
            "<b>How to test:</b>\n"
            "1. Use Postman or curl\n"
            "2. Send POST request to test URL\n"
            "3. Body: {\"sms_text\": \"[SMS_CONTENT]\"}\n\n"
            "<b>Example curl:</b>\n"
            f"<code>curl -X POST {WEBAPP_URL}/webhook/macrodroid/test \\\n"
            "  -H 'Content-Type: application/json' \\\n"
            "  -d '{{\"sms_text\": \"{test_sms}\"}}'</code>"
        )
        
        await message.answer(test_instructions, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logger.error(f"Error in testwebhook command: {e}")
        await message.answer("❌ Sorry, there was an error. Please try again later.")

async def main():
    """Main entry point for the bot"""
    try:
        logger.info("Starting bot...")
        
        # Include router
        dp.include_router(router)
        
        # Start polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise