import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_simple_webhook():
    """
    Simple test script that matches Macrodroid HTTP Request format
    """
    # Test data - using your actual phone number
    test_data = {
        "amount": 100.0,
        "phone": "0941043869",  # Your phone number
        "method": "cbe",
        "reference": f"MACRODROID-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }

    # Headers - same as Macrodroid's Content-Type setting
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Macrodroid/1.0"
    }

    # The URL from your Macrodroid setup
    urls = [
        "https://updated-eight-ashy.vercel.app/webhook/deposit",  # Production deposit endpoint
        "https://updated-eight-ashy.vercel.app/webhook/test",     # Production test endpoint
        "http://localhost:5000/webhook/deposit",                  # Local deposit endpoint
        "http://localhost:5000/webhook/test"                      # Local test endpoint
    ]

    for url in urls:
        print(f"\n" + "="*60)
        print(f"🔗 Testing URL: {url}")
        print("="*60)
        
        try:
            logger.info(f"Sending test request to: {url}")
            logger.info(f"Data: {test_data}")
            
            response = requests.post(
                url,
                json=test_data,
                headers=headers,
                timeout=10
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print(f"📨 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📝 Response Body:")
                print(json.dumps(response_json, indent=2))
                
                if response.status_code == 200:
                    if 'success' in response_json and response_json['success']:
                        print("✅ Test successful!")
                        print(f"💡 Message: {response_json.get('message', 'No message')}")
                        
                        # Show user info if available
                        if 'user_id' in response_json:
                            print(f"👤 User ID: {response_json['user_id']}")
                        if 'username' in response_json:
                            print(f"📛 Username: {response_json['username']}")
                        if 'new_balance' in response_json:
                            print(f"💰 New Balance: {response_json['new_balance']} Birr")
                            
                    else:
                        print("❌ Request failed (success: false)")
                        print(f"📛 Error: {response_json.get('error', 'Unknown error')}")
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    
            except json.JSONDecodeError:
                print(f"⚠️ Response is not JSON: {response.text}")
                if response.status_code == 200:
                    print("✅ Test successful (non-JSON response)")
                else:
                    print("❌ Test failed (non-JSON response)")
                    
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ Connection error: {e}")
            print(f"❌ Cannot connect to {url}")
            print(f"💡 Make sure the server is running and accessible")
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ Timeout error: {e}")
            print(f"❌ Request timeout for {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Request error: {e}")
            print(f"❌ Request failed: {e}")

def test_sms_format():
    """Test different SMS formats that Macrodroid might send"""
    print("\n" + "="*60)
    print("📱 Testing Different SMS Formats")
    print("="*60)
    
    # Different SMS formats that banks might use
    sms_formats = [
        {
            "name": "CBE Standard Format",
            "data": {
                "amount": 150.0,
                "phone": "0941043869",
                "method": "cbe",
                "reference": "CBE: You have received 150.00 ETB from 0912345678. Your new balance is 1250.00 ETB."
            }
        },
        {
            "name": "TeleBirr Format",
            "data": {
                "amount": 200.0,
                "phone": "0941043869",
                "method": "telebirr",
                "reference": "TeleBirr: 200.00 ETB received from 0912345678. Balance: 1450.00 ETB."
            }
        },
        {
            "name": "Minimum Required",
            "data": {
                "amount": 50.0,
                "phone": "0941043869"
            }
        },
        {
            "name": "With Extra Fields",
            "data": {
                "amount": 300.0,
                "phone": "0941043869",
                "method": "cbe",
                "reference": "TRX123456789",
                "sender": "0912345678",
                "timestamp": datetime.now().isoformat(),
                "balance": "1750.00"
            }
        }
    ]
    
    base_url = "https://updated-eight-ashy.vercel.app"
    
    for sms_format in sms_formats:
        print(f"\n📄 Testing: {sms_format['name']}")
        print(f"   Data: {json.dumps(sms_format['data'], indent=4)}")
        
        try:
            response = requests.post(
                f"{base_url}/webhook/test",
                json=sms_format['data'],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'status' in result and result['status'] == 'valid':
                    print("   ✅ Format accepted")
                else:
                    print(f"   ⚠️  Format validation: {result.get('status', 'unknown')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_error_cases():
    """Test error cases and edge conditions"""
    print("\n" + "="*60)
    print("🚨 Testing Error Cases")
    print("="*60)
    
    error_cases = [
        {
            "name": "Empty JSON",
            "data": {},
            "expected_code": 400
        },
        {
            "name": "No Content-Type header",
            "data": {"amount": 100, "phone": "0941043869"},
            "headers": {},
            "expected_code": 400
        },
        {
            "name": "Invalid JSON",
            "data": "{invalid json}",
            "expected_code": 400
        },
        {
            "name": "Amount as string",
            "data": {"amount": "100", "phone": "0941043869"},
            "expected_code": 400
        },
        {
            "name": "Phone with spaces",
            "data": {"amount": 100, "phone": "0941 043 869"},
            "expected_code": 400
        }
    ]
    
    base_url = "https://updated-eight-ashy.vercel.app"
    
    for case in error_cases:
        print(f"\n⚠️  Testing: {case['name']}")
        
        headers = case.get('headers', {"Content-Type": "application/json"})
        
        try:
            if isinstance(case['data'], str):
                # Invalid JSON case
                response = requests.post(
                    f"{base_url}/webhook/test",
                    data=case['data'],
                    headers=headers,
                    timeout=5
                )
            else:
                response = requests.post(
                    f"{base_url}/webhook/test",
                    json=case['data'],
                    headers=headers,
                    timeout=5
                )
            
            print(f"   Status: {response.status_code} (expected: {case.get('expected_code', 'any')})")
            
            if response.status_code == case.get('expected_code', 200):
                print("   ✅ Expected response received")
            else:
                print(f"   ⚠️  Unexpected status code")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Macrodroid Webhook Tests")
    print("="*60)
    print(f"📱 Your Phone: 0941043869")
    print(f"🏦 CBE: SAMSON MESFIN - 100348220032")
    print(f"📱 TeleBirr: NITSU - 0976233815")
    print(f"🌐 Base URL: https://updated-eight-ashy.vercel.app")
    print("="*60)
    
    # Run all tests
    test_simple_webhook()
    test_sms_format()
    test_error_cases()
    
    print("\n" + "="*60)
    print("🎯 All tests completed!")
    print("="*60)
    print("\n📋 For Macrodroid setup:")
    print("   URL: https://updated-eight-ashy.vercel.app/webhook/deposit")
    print("   Method: POST")
    print("   Headers: Content-Type: application/json")
    print("   Body: {\"amount\": %amount, \"phone\": \"0941043869\", \"method\": \"cbe\"}")
    print("="*60)