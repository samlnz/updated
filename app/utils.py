# File: app/utils.py
import random
import string
import hashlib
import secrets
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

def generate_referral_code(length: int = 8) -> str:
    """
    Generate a random referral code.
    Format: 2 letters + 4 numbers + 2 letters (e.g., AB1234CD)
    """
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    letters2 = ''.join(random.choices(string.ascii_uppercase, k=2))
    return f"{letters}{numbers}{letters2}"

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID.
    Format: TX + timestamp + random string
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TX{timestamp}{random_str}"

def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard format.
    Ethiopian numbers: +251XXXXXXXXX
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle Ethiopian numbers
    if digits.startswith('0') and len(digits) == 10:
        # Convert 09xxxxxxxx to 2519xxxxxxxx
        digits = '251' + digits[1:]
    elif digits.startswith('251') and len(digits) == 12:
        # Already in correct format
        pass
    elif len(digits) == 9:
        # Assume it's without country code
        digits = '251' + digits
    
    return digits if digits else phone

def is_valid_phone_number(phone: str) -> bool:
    """
    Validate Ethiopian phone number.
    Valid formats: 09XXXXXXXX, 2519XXXXXXXX, +2519XXXXXXXX
    """
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check Ethiopian mobile numbers (9XXXXXXXX)
    if len(digits) == 10 and digits.startswith('09'):
        return True
    elif len(digits) == 12 and digits.startswith('2519'):
        return True
    elif len(digits) == 9 and digits.startswith('9'):
        return True
    
    return False

def generate_bingo_numbers():
    """
    Generate random Bingo numbers (5x5 grid with FREE in center).
    Returns a list of 25 numbers (0 represents FREE at index 12).
    """
    board = []
    
    # Bingo columns: B(1-15), I(16-30), N(31-45), G(46-60), O(61-75)
    ranges = [(1, 15), (16, 30), (31, 45), (46, 60), (61, 75)]
    
    for col in range(5):
        start, end = ranges[col]
        numbers = random.sample(range(start, end + 1), 5)
        board.extend(numbers)
    
    # Set center as FREE (0 represents FREE)
    board[12] = 0
    
    return board

def format_currency(amount: float) -> str:
    """
    Format currency with Ethiopian Birr symbol.
    """
    return f"{amount:,.2f} ብር"

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string.
    """
    if not dt:
        return ""
    return dt.strftime(format_str)

def parse_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    """
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None

def calculate_win_probability(players_count: int, games_played: int = 0) -> float:
    """
    Calculate win probability based on number of players and user's experience.
    """
    if players_count < 2:
        return 0.0
    
    base_probability = 1.0 / players_count
    
    # Experience bonus (up to 20% for experienced players)
    experience_bonus = min(games_played * 0.01, 0.2)
    
    return min(base_probability + experience_bonus, 1.0)

def validate_deposit_amount(amount: float) -> tuple[bool, str]:
    """
    Validate deposit amount.
    Returns (is_valid, error_message)
    """
    from config import MIN_DEPOSIT
    
    if amount <= 0:
        return False, "Amount must be positive"
    
    if amount < MIN_DEPOSIT:
        return False, f"Minimum deposit is {MIN_DEPOSIT} birr"
    
    if amount > 10000:  # Max deposit 10,000 birr
        return False, "Maximum deposit is 10,000 birr"
    
    return True, ""

def validate_withdrawal_amount(amount: float, balance: float, games_played: int) -> tuple[bool, str]:
    """
    Validate withdrawal amount.
    Returns (is_valid, error_message)
    """
    from config import MIN_WITHDRAWAL
    
    if amount <= 0:
        return False, "Amount must be positive"
    
    if amount < MIN_WITHDRAWAL:
        return False, f"Minimum withdrawal is {MIN_WITHDRAWAL} birr"
    
    if amount > balance:
        return False, "Insufficient balance"
    
    if games_played < 5:
        return False, "You must play at least 5 games before withdrawing"
    
    return True, ""

def generate_password_hash(password: str) -> str:
    """
    Generate a secure hash for passwords.
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256(f"{password}{salt}".encode())
    return f"{hash_obj.hexdigest()}:{salt}"

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        stored_hash, salt = password_hash.split(':')
        test_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return secrets.compare_digest(test_hash, stored_hash)
    except (ValueError, AttributeError):
        return False

def format_bingo_number(number: int) -> str:
    """
    Format Bingo number with letter prefix.
    """
    if number <= 15:
        return f"B{number}"
    elif number <= 30:
        return f"I{number}"
    elif number <= 45:
        return f"N{number}"
    elif number <= 60:
        return f"G{number}"
    else:
        return f"O{number}"

def parse_bingo_number(bingo_str: str) -> Optional[int]:
    """
    Parse Bingo string to number (e.g., "B12" -> 12).
    """
    if not bingo_str:
        return None
    
    try:
        prefix = bingo_str[0].upper()
        number = int(bingo_str[1:])
        
        # Validate range based on prefix
        if prefix == 'B' and 1 <= number <= 15:
            return number
        elif prefix == 'I' and 16 <= number <= 30:
            return number
        elif prefix == 'N' and 31 <= number <= 45:
            return number
        elif prefix == 'G' and 46 <= number <= 60:
            return number
        elif prefix == 'O' and 61 <= number <= 75:
            return number
    except (ValueError, IndexError):
        pass
    
    return None

def calculate_referral_bonus(level: int = 1) -> float:
    """
    Calculate referral bonus based on level.
    Level 1: Direct referral
    Level 2: Referral of referral, etc.
    """
    from config import REFERRAL_BONUS
    
    if level == 1:
        return REFERRAL_BONUS
    elif level == 2:
        return REFERRAL_BONUS * 0.5
    elif level == 3:
        return REFERRAL_BONUS * 0.25
    else:
        return 0.0

def get_time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference.
    """
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"

def safe_json_loads(json_str: str) -> Any:
    """
    Safely load JSON string, return empty dict on error.
    """
    if not json_str:
        return {}
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return {}

def safe_json_dumps(data: Any) -> str:
    """
    Safely dump data to JSON string.
    """
    try:
        return json.dumps(data, default=str)
    except (TypeError, ValueError):
        return "{}"

def generate_admin_session_token() -> str:
    """
    Generate a secure session token for admin panel.
    """
    return secrets.token_urlsafe(32)

def sanitize_input(text: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent XSS and SQL injection.
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    
    # Truncate to max length
    if len(clean) > max_length:
        clean = clean[:max_length]
    
    # Escape special characters for SQL (basic)
    clean = clean.replace("'", "''").replace('"', '""')
    
    return clean.strip()

def calculate_game_prize(entry_price: float, players_count: int, platform_fee: float = 0.1) -> float:
    """
    Calculate game prize pool after platform fee.
    """
    total_pool = entry_price * players_count
    prize_pool = total_pool * (1 - platform_fee)
    return round(prize_pool, 2)

def get_bank_account_info(bank_name: str) -> Dict[str, str]:
    """
    Get bank account information by bank name.
    """
    from config import BANK_ACCOUNTS
    
    bank_name = bank_name.strip().lower()
    
    for key, info in BANK_ACCOUNTS.items():
        if key.lower() == bank_name:
            return info
    
    return BANK_ACCOUNTS.get("CBE", {})

def format_bank_details(bank_name: str) -> str:
    """
    Format bank details for display.
    """
    info = get_bank_account_info(bank_name)
    
    if not info:
        return "Bank information not available"
    
    return (
        f"🏦 {bank_name.upper()}:\n"
        f"Account: {info.get('account_number', 'N/A')}\n"
        f"Name: {info.get('account_name', 'N/A')}"
    )

def validate_email(email: str) -> bool:
    """
    Validate email address format.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def generate_otp(length: int = 6) -> str:
    """
    Generate a numeric OTP.
    """
    return ''.join(random.choices(string.digits, k=length))

def format_game_id(game_id: int) -> str:
    """
    Format game ID with leading zeros.
    """
    return f"G{game_id:06d}"

def format_user_id(user_id: int) -> str:
    """
    Format user ID with leading zeros.
    """
    return f"U{user_id:06d}"

def get_current_season() -> str:
    """
    Get current game season based on date.
    Format: YYYY-S (e.g., 2024-1 for first half of year)
    """
    now = datetime.now()
    season = 1 if now.month <= 6 else 2
    return f"{now.year}-{season}"

def calculate_user_level(games_won: int, total_deposits: float) -> int:
    """
    Calculate user level based on games won and total deposits.
    """
    level = 1
    
    if games_won >= 50 or total_deposits >= 5000:
        level = 5  # VIP
    elif games_won >= 25 or total_deposits >= 2500:
        level = 4  # Gold
    elif games_won >= 10 or total_deposits >= 1000:
        level = 3  # Silver
    elif games_won >= 5 or total_deposits >= 500:
        level = 2  # Bronze
    
    return level

def get_level_badge(level: int) -> str:
    """
    Get badge for user level.
    """
    badges = {
        1: "🎯",  # Newbie
        2: "🥉",  # Bronze
        3: "🥈",  # Silver
        4: "🥇",  # Gold
        5: "👑",  # VIP
    }
    return badges.get(level, "🎯")

def log_transaction(transaction_type: str, user_id: int, amount: float, details: str = ""):
    """
    Log transaction for auditing.
    """
    logger = logging.getLogger("transactions")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": transaction_type,
        "user_id": user_id,
        "amount": amount,
        "details": details
    }
    logger.info(f"Transaction: {json.dumps(log_entry)}")

def backup_database():
    """
    Create a database backup (for SQLite).
    In production with PostgreSQL, you'd use pg_dump.
    """
    import shutil
    from config import DATABASE_URL
    
    if "sqlite" in DATABASE_URL:
        # Extract database file path
        db_path = DATABASE_URL.replace("sqlite:///", "")
        
        # Create backup with timestamp
        backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            shutil.copy2(db_path, backup_path)
            logging.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Failed to backup database: {e}")
            return None
    
    return None

def parse_ethiopian_bank_sms(sms_text: str) -> dict:
    """
    Parse Ethiopian bank SMS messages to extract transaction details.
    Returns dict with amount, sender_phone, bank_name, and transaction_type.
    """
    result = {
        'amount': 0.0,
        'sender_phone': '',
        'bank_name': 'unknown',
        'transaction_type': 'deposit',
        'is_valid': False
    }
    
    if not sms_text:
        return result
    
    sms_lower = sms_text.lower()
    
    # Common Ethiopian SMS patterns
    patterns = {
        'amount_patterns': [
            r'([\d,]+\.\d{2})\s*(?:etb|ብር|birr)',
            r'(?:etb|ብር|birr)\s*([\d,]+\.\d{2})',
            r'የተቀበሉት\s*([\d,]+\.\d{2})',
            r'ተቀምጧል\s*([\d,]+\.\d{2})',
            r'received\s*([\d,]+\.\d{2})',
            r'credited\s*([\d,]+\.\d{2})'
        ],
        'phone_patterns': [
            r'from\s*(\+\d{12})',
            r'from\s*(\d{10})',
            r'ከ\s*(\+\d{12})',
            r'ከ\s*(\d{10})',
            r'sender\s*(\+\d{12})',
            r'sender\s*(\d{10})'
        ]
    }
    
    # Extract amount
    for pattern in patterns['amount_patterns']:
        match = re.search(pattern, sms_lower, re.IGNORECASE)
        if match:
            try:
                amount_str = match.group(1).replace(',', '')
                result['amount'] = float(amount_str)
                break
            except (ValueError, IndexError):
                continue
    
    # Extract phone number
    for pattern in patterns['phone_patterns']:
        match = re.search(pattern, sms_lower, re.IGNORECASE)
        if match:
            phone = match.group(1)
            if is_valid_phone_number(phone):
                result['sender_phone'] = format_phone_number(phone)
                break
    
    # Identify bank
    bank_keywords = {
        'cbe': ['commercial bank', 'cbe', 'ደሴን'],
        'telebirr': ['telebirr', 'ቴሌብር'],
        'dashen': ['dashen', 'ደሴን'],
        'awash': ['awash', 'አዋሽ'],
        'cbe_birr': ['cbe birr'],
        'hello_cash': ['hello cash', 'ሄሎ ኬሽ'],
        'm_birr': ['m-birr', 'ኤም ብር']
    }
    
    for bank_name, keywords in bank_keywords.items():
        for keyword in keywords:
            if keyword in sms_lower:
                result['bank_name'] = bank_name
                break
    
    # Determine transaction type
    if any(word in sms_lower for word in ['received', 'credited', 'ተቀበለዋል', 'ተቀምጧል']):
        result['transaction_type'] = 'deposit'
    elif any(word in sms_lower for word in ['sent', 'transferred', 'ወስደዋል', 'ተላልፏል']):
        result['transaction_type'] = 'withdrawal'
    
    result['is_valid'] = result['amount'] > 0
    return result

def validate_sms_for_deposit(sms_text: str) -> tuple[bool, str, float]:
    """
    Validate if SMS is a valid deposit notification.
    Returns (is_valid, phone_number, amount)
    """
    parsed = parse_ethiopian_bank_sms(sms_text)
    
    if not parsed['is_valid']:
        return False, "", 0.0
    
    if parsed['transaction_type'] != 'deposit':
        return False, parsed['sender_phone'], parsed['amount']
    
    if not parsed['sender_phone']:
        return True, "", parsed['amount']
    
    return True, parsed['sender_phone'], parsed['amount']

def generate_macrodroid_config() -> dict:
    """
    Generate configuration for Macrodroid automation.
    """
    return {
        "name": "Addis Bingo Deposit Auto-Forward",
        "triggers": [
            {
                "type": "SMS Received",
                "config": {
                    "sender": "ANY",
                    "content_filter": ["ETB", "ብር", "received", "credited", "የተቀበሉት"],
                    "regex_filter": r"(ETB|ብር|birr).*?\d+\.\d{2}"
                }
            }
        ],
        "actions": [
            {
                "type": "HTTP Request",
                "config": {
                    "method": "POST",
                    "url": "{YOUR_SERVER_URL}/webhook/macrodroid",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "sms_text": "{sms_body}",
                        "sender_number": "{sms_sender}",
                        "timestamp": "{datetime}",
                        "device_id": "{device_id}"
                    }
                }
            },
            {
                "type": "Notification",
                "config": {
                    "title": "Deposit Forwarded",
                    "message": "SMS forwarded to Addis Bingo server"
                }
            }
        ],
        "variables": [
            {
                "name": "server_url",
                "value": "https://updated-eight-ashy.vercel.app"
            }
        ]
    }

def get_bank_sms_senders() -> dict:
    """
    Get common SMS sender numbers for Ethiopian banks.
    Useful for filtering SMS in Macrodroid.
    """
    return {
        "cbe": ["9893", "9894", "9895"],
        "telebirr": ["999", "127"],
        "dashen": ["9880", "9881"],
        "awash": ["9860", "9861"],
        "cbe_birr": ["9898"],
        "hello_cash": ["847"],
        "m_birr": ["9899"],
        "amole": ["841"],
        "payday": ["826"]
    }

def create_macrodroid_export_config() -> str:
    """
    Create a Macrodroid configuration export file content.
    Users can import this directly into Macrodroid.
    """
    config = {
        "version": 1,
        "macros": [
            {
                "name": "Addis Bingo Auto-Deposit",
                "enabled": True,
                "trigger": {
                    "type": "SMS_RECEIVED",
                    "constraint": {
                        "sender": "",
                        "content": "",
                        "regex": ".*(ETB|ብር|birr).*\\d+\\.\\d{2}.*"
                    }
                },
                "actions": [
                    {
                        "type": "HTTP_POST",
                        "url": "https://updated-eight-ashy.vercel.app/webhook/macrodroid",
                        "headers": "Content-Type: application/json",
                        "body": '{"sms_text": "{sms_body}", "sender_number": "{sms_sender}", "timestamp": "{datetime}", "device_id": "{device_id}"}'
                    },
                    {
                        "type": "NOTIFICATION",
                        "title": "💰 Deposit Forwarded",
                        "message": "SMS sent to Addis Bingo server for processing"
                    }
                ],
                "variables": [
                    {
                        "name": "server_url",
                        "value": "https://updated-eight-ashy.vercel.app"
                    }
                ]
            }
        ]
    }
    
    return json.dumps(config, indent=2)

# Add a logger for this module
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())