# File: app/macrodroid_webhook.py
import re
import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Transaction
from app.utils import is_valid_phone_number, format_phone_number

bp = Blueprint('macrodroid', __name__, url_prefix='/webhook')
logger = logging.getLogger(__name__)

class SMSForwarder:
    """Handle SMS forwarding from Macrodroid and Tasker"""
    
    # Common SMS patterns for Ethiopian banks and mobile money
    SMS_PATTERNS = {
        'cbe': [
            r'You have received ([\d,]+\.?\d*) ETB from .*?\. New balance is .*?',
            r'Deposit of ([\d,]+\.?\d*) ETB received from .*?\.',
            r'Account \d+ credited with ([\d,]+\.?\d*) ETB\.',
            r'Credit Alert: ([\d,]+\.?\d*) ETB has been credited to your account\.',
            r'በሂሳብዎ \d+ ውስጥ ([\d,]+\.?\d*) ብር ተቀምጧል\.'
        ],
        'telebirr': [
            r'You have received ([\d,]+\.?\d*) ETB from .*?\.',
            r'Tx: ([\d,]+\.?\d*) ETB received from .*?\.',
            r'የተላለፈ: ([\d,]+\.?\d*) ብር ከ.*? ተቀብለዋል\.',
            r'የተቀበሉት: ([\d,]+\.?\d*) ብር ከ.*?\.'
        ],
        'dashen': [
            r'Deposit: ([\d,]+\.?\d*) ETB to account \d+\.',
            r'Credit: ([\d,]+\.?\d*) ETB\. Balance: .*?\.',
            r'ሂሳብዎ በ([\d,]+\.?\d*) ብር ተሞልቷል\.'
        ],
        'cbe_birr': [
            r'CBE Birr: ([\d,]+\.?\d*) ETB received from .*?\.',
            r'CBE Birr Tx: ([\d,]+\.?\d*) ETB\.'
        ],
        'awash': [
            r'A/C \d+ credited with ([\d,]+\.?\d*) ETB\.',
            r'Deposit of ([\d,]+\.?\d*) ETB successful\.'
        ]
    }
    
    @staticmethod
    def extract_amount_from_sms(sms_text: str) -> float:
        """Extract amount from SMS text using regex patterns"""
        if not sms_text:
            return 0.0
        
        # Try each pattern
        for bank_patterns in SMS_PATTERNS.values():
            for pattern in bank_patterns:
                match = re.search(pattern, sms_text, re.IGNORECASE)
                if match:
                    try:
                        # Extract amount and clean it
                        amount_str = match.group(1).replace(',', '')
                        return float(amount_str)
                    except (ValueError, IndexError):
                        continue
        
        # Fallback: Look for any number with decimal
        amount_matches = re.findall(r'([\d,]+\.\d{2})', sms_text)
        if amount_matches:
            try:
                return float(amount_matches[0].replace(',', ''))
            except ValueError:
                pass
        
        # Look for any number with 2 decimal places
        amount_matches = re.findall(r'(\d+\.\d{2})', sms_text)
        if amount_matches:
            try:
                return float(amount_matches[0])
            except ValueError:
                pass
        
        return 0.0
    
    @staticmethod
    def extract_sender_from_sms(sms_text: str) -> str:
        """Extract sender phone number from SMS text"""
        # Look for phone numbers in SMS
        phone_patterns = [
            r'from (\+\d{12})',  # +251912345678
            r'from (\d{10})',    # 0912345678
            r'ከ(\+\d{12})',      # Amharic: from +251...
            r'ከ(\d{10})',        # Amharic: from 09...
            r'by (\+\d{12})',
            r'by (\d{10})',
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                phone = match.group(1)
                if is_valid_phone_number(phone):
                    return format_phone_number(phone)
        
        return ""
    
    @staticmethod
    def identify_bank_from_sms(sms_text: str) -> str:
        """Identify which bank/mobile money sent the SMS"""
        sms_lower = sms_text.lower()
        
        if 'telebirr' in sms_lower:
            return 'telebirr'
        elif 'cbe birr' in sms_lower:
            return 'cbe_birr'
        elif 'cbe' in sms_lower:
            return 'cbe'
        elif 'dashen' in sms_lower:
            return 'dashen'
        elif 'awash' in sms_lower:
            return 'awash'
        elif 'commercial bank' in sms_lower:
            return 'cbe'
        elif 'ደሴን' in sms_lower:
            return 'dashen'
        elif 'አዋሽ' in sms_lower:
            return 'awash'
        elif 'ቴሌብር' in sms_lower:
            return 'telebirr'
        
        return 'unknown'

@bp.route('/macrodroid', methods=['POST'])
def macrodroid_webhook():
    """
    Handle SMS forwarded from Macrodroid
    Expected JSON format from Macrodroid:
    {
        "sms_text": "You have received 100.00 ETB from 0912345678. Your balance is 500.00 ETB.",
        "sender_number": "0941043869",
        "timestamp": "2024-01-01 12:00:00",
        "device_id": "device123"
    }
    """
    try:
        data = request.get_json()
        logger.info(f"Received Macrodroid webhook: {data}")
        
        # Validate required fields
        if not data or 'sms_text' not in data:
            error_msg = 'Invalid webhook data - must include sms_text'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        sms_text = data.get('sms_text', '')
        sender_number = data.get('sender_number', '')  # Phone that received SMS
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Extract amount from SMS
        amount = SMSForwarder.extract_amount_from_sms(sms_text)
        if amount <= 0:
            logger.warning(f"Could not extract valid amount from SMS: {sms_text}")
            return jsonify({
                'status': 'warning',
                'message': 'No valid amount found in SMS',
                'extracted_amount': amount,
                'sms_preview': sms_text[:100] + '...' if len(sms_text) > 100 else sms_text
            })
        
        # Extract sender phone from SMS (who sent the money)
        sender_from_sms = SMSForwarder.extract_sender_from_sms(sms_text)
        if not sender_from_sms:
            sender_from_sms = sender_number  # Fallback to SMS receiver number
        
        # Identify bank
        bank = SMSForwarder.identify_bank_from_sms(sms_text)
        
        logger.info(f"Extracted from SMS: Amount={amount}, Sender={sender_from_sms}, Bank={bank}")
        
        # Find user by phone number
        user = User.query.filter_by(phone=sender_from_sms).first()
        if not user:
            logger.warning(f"No user found with phone: {sender_from_sms}")
            return jsonify({
                'status': 'error',
                'message': f'No user registered with phone: {sender_from_sms}',
                'extracted_amount': amount,
                'extracted_phone': sender_from_sms,
                'suggested_action': 'Ask user to register with this phone number'
            }), 404
        
        # Check for existing pending deposit
        pending_transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='deposit',
            status='pending',
            amount=amount
        ).order_by(Transaction.created_at.desc()).first()
        
        if pending_transaction:
            # Approve the pending deposit
            pending_transaction.status = 'completed'
            pending_transaction.completed_at = datetime.utcnow()
            pending_transaction.sms_text = sms_text
            pending_transaction.transaction_id = f"MACRO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Update user balance
            user.balance += amount
            user.total_deposits += amount
            
            db.session.commit()
            
            logger.info(f"Deposit approved via Macrodroid for user {user.id}: {amount} birr")
            
            return jsonify({
                'status': 'success',
                'message': f'Deposit of {amount} birr processed successfully',
                'user_id': user.id,
                'username': user.username,
                'new_balance': user.balance,
                'transaction_id': pending_transaction.id,
                'bank': bank,
                'processed_at': datetime.utcnow().isoformat()
            })
        else:
            # Create new deposit transaction
            transaction = Transaction(
                user_id=user.id,
                type='deposit',
                amount=amount,
                status='completed',
                completed_at=datetime.utcnow(),
                deposit_phone=sender_from_sms,
                sms_text=sms_text,
                transaction_id=f"MACRO-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            # Update user balance
            user.balance += amount
            user.total_deposits += amount
            
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Auto-deposit created via Macrodroid for user {user.id}: {amount} birr")
            
            return jsonify({
                'status': 'success',
                'message': f'Auto-deposit of {amount} birr created successfully',
                'user_id': user.id,
                'username': user.username,
                'new_balance': user.balance,
                'transaction_id': transaction.id,
                'bank': bank,
                'note': 'No pending deposit found, created automatic deposit',
                'processed_at': datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.exception(f"Error processing Macrodroid webhook: {str(e)}")
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'help': 'Make sure to send JSON with sms_text field'
        }), 500

@bp.route('/macrodroid/test', methods=['POST', 'GET'])
def macrodroid_test():
    """Test endpoint for Macrodroid setup"""
    if request.method == 'GET':
        return jsonify({
            'status': 'ready',
            'message': 'Macrodroid webhook is ready',
            'endpoint': '/webhook/macrodroid',
            'method': 'POST',
            'required_fields': ['sms_text'],
            'optional_fields': ['sender_number', 'timestamp', 'device_id'],
            'example': {
                'sms_text': 'You have received 100.00 ETB from 0912345678. Your balance is 500.00 ETB.',
                'sender_number': '0941043869',
                'timestamp': '2024-01-01 12:00:00'
            }
        })
    
    # POST request - test parsing
    try:
        data = request.get_json() or {}
        sms_text = data.get('sms_text', '')
        
        if not sms_text:
            return jsonify({
                'status': 'error',
                'message': 'Please provide sms_text in the request body'
            }), 400
        
        # Test parsing
        amount = SMSForwarder.extract_amount_from_sms(sms_text)
        sender = SMSForwarder.extract_sender_from_sms(sms_text)
        bank = SMSForwarder.identify_bank_from_sms(sms_text)
        
        return jsonify({
            'status': 'success',
            'parsed_data': {
                'amount': amount,
                'sender_phone': sender,
                'bank': bank,
                'is_valid_amount': amount > 0,
                'is_valid_phone': is_valid_phone_number(sender)
            },
            'sms_analysis': {
                'length': len(sms_text),
                'preview': sms_text[:200] + '...' if len(sms_text) > 200 else sms_text,
                'contains_etb': 'etb' in sms_text.lower() or 'ብር' in sms_text,
                'contains_birr': 'birr' in sms_text.lower()
            },
            'recommendation': 'Amount > 0 and valid phone number required for processing'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'help': 'Send JSON with sms_text field'
        }), 500

@bp.route('/tasker', methods=['POST'])
def tasker_webhook():
    """
    Handle Tasker webhook (alternative to Macrodroid)
    Expected format:
    {
        "amount": 100.00,
        "phone": "0941043869",
        "timestamp": "2024-01-01 12:00:00",
        "reference": "TX123456"
    }
    """
    try:
        data = request.get_json()
        logger.info(f"Received Tasker webhook: {data}")
        
        # Validate required fields
        if not data or 'amount' not in data or 'phone' not in data:
            error_msg = 'Invalid webhook data - must include amount and phone'
            logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
        
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        phone = data['phone']
        if not is_valid_phone_number(phone):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        formatted_phone = format_phone_number(phone)
        
        # Find user by phone number
        user = User.query.filter_by(phone=formatted_phone).first()
        if not user:
            return jsonify({'error': f'No user found with phone: {formatted_phone}'}), 404
        
        # Check for pending deposit
        pending_transaction = Transaction.query.filter_by(
            user_id=user.id,
            type='deposit',
            status='pending',
            amount=amount
        ).order_by(Transaction.created_at.desc()).first()
        
        if pending_transaction:
            # Approve the deposit
            pending_transaction.status = 'completed'
            pending_transaction.completed_at = datetime.utcnow()
            pending_transaction.transaction_id = data.get('reference', f"TASKER-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            # Update user balance
            user.balance += amount
            user.total_deposits += amount
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Deposit of {amount} birr processed successfully',
                'new_balance': user.balance
            })
        else:
            # Create auto-deposit
            transaction = Transaction(
                user_id=user.id,
                type='deposit',
                amount=amount,
                status='completed',
                completed_at=datetime.utcnow(),
                deposit_phone=formatted_phone,
                transaction_id=data.get('reference', f"TASKER-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            )
            
            user.balance += amount
            user.total_deposits += amount
            
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Auto-deposit of {amount} birr created',
                'new_balance': user.balance,
                'note': 'No pending deposit found, created automatic deposit'
            })
            
    except Exception as e:
        logger.exception(f"Error processing Tasker webhook: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500