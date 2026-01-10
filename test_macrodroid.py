#!/usr/bin/env python3
# File: test_macrodroid.py
import requests
import json
import sys

def test_macrodroid_webhook():
    """Test the Macrodroid webhook with sample SMS"""
    
    # Your server URL
    SERVER_URL = "https://updated-eight-ashy.vercel.app"
    
    # Test SMS messages from different banks
    test_cases = [
        {
            "name": "Telebirr English",
            "sms": "You have received 100.00 ETB from 0912345678. Your new balance is 500.00 ETB.",
            "sender": "0941043869"
        },
        {
            "name": "Telebirr Amharic",
            "sms": "100.00 ብር ከ0912345678 ተቀበለዋል። አዲሱ ቀሪ ሂሳብዎ 500.00 ብር ነው።",
            "sender": "0941043869"
        },
        {
            "name": "CBE Bank",
            "sms": "Credit Alert: 250.00 ETB has been credited to your account 100348220032 from 0912345678. Balance: 750.00 ETB.",
            "sender": "0941043869"
        },
        {
            "name": "Dashen Bank",
            "sms": "Deposit: 50.00 ETB to account 1234567890 from 0912345678. Available balance: 300.00 ETB.",
            "sender": "0941043869"
        },
        {
            "name": "CBE Birr",
            "sms": "CBE Birr: You have received 75.00 ETB from 0912345678. Transaction ID: TX123456.",
            "sender": "0941043869"
        }
    ]
    
    print("🔧 Testing Macrodroid Webhook")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"SMS: {test_case['sms'][:60]}...")
        
        # Prepare payload
        payload = {
            "sms_text": test_case["sms"],
            "sender_number": test_case["sender"],
            "timestamp": "2024-01-01 12:00:00",
            "device_id": "test_device"
        }
        
        try:
            # Test the webhook
            response = requests.post(
                f"{SERVER_URL}/webhook/macrodroid",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
    
    # Test the test endpoint
    print("\n" + "=" * 50)
    print("Testing /webhook/macrodroid/test endpoint")
    
    try:
        response = requests.get(f"{SERVER_URL}/webhook/macrodroid/test")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_sms_parsing():
    """Test SMS parsing independently"""
    from app.macrodroid_webhook import SMSForwarder
    
    test_sms = [
        "You have received 100.00 ETB from 0912345678.",
        "100.00 ብር ከ0912345678 ተቀበለዋል።",
        "Credit Alert: 250.00 ETB credited to account.",
        "Deposit of 50.00 ETB received from 0912345678.",
        "የተቀበሉት: 75.00 ብር ከ0912345678።"
    ]
    
    print("\n" + "=" * 50)
    print("Testing SMS Parsing")
    print("=" * 50)
    
    for sms in test_sms:
        amount = SMSForwarder.extract_amount_from_sms(sms)
        sender = SMSForwarder.extract_sender_from_sms(sms)
        bank = SMSForwarder.identify_bank_from_sms(sms)
        
        print(f"\nSMS: {sms[:50]}...")
        print(f"  Amount: {amount}")
        print(f"  Sender: {sender}")
        print(f"  Bank: {bank}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "parse":
        test_sms_parsing()
    else:
        test_macrodroid_webhook()