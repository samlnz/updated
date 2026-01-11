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

def test_tasker_deposit():
    """
    Test script to simulate Macrodroid deposit confirmation.
    This simulates sending a deposit confirmation to the bot.
    """
    # Test data - adjust as needed
    deposit_data = {
        "amount": 100.0,
        "phone": "0941043869",  # Your phone number
        "method": "cbe",
        "reference": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    }

    # URLs to test
    test_urls = [
        "http://localhost:5000/webhook/deposit",  # Local development
        "https://updated-eight-ashy.vercel.app/webhook/deposit",  # Production
        "http://localhost:5000/webhook/test",  # Local test endpoint
        "https://updated-eight-ashy.vercel.app/webhook/test"  # Production test endpoint
    ]

    print("🎯 Testing Deposit Webhook Endpoints")
    print("=" * 50)

    for url in test_urls:
        print(f"\n🔗 Testing URL: {url}")
        print(f"📊 Test Data: {json.dumps(deposit_data, indent=2)}")

        try:
            # Send the deposit confirmation
            response = requests.post(
                url,
                json=deposit_data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Macrodroid-Tester/1.0"
                },
                timeout=10
            )

            print(f"✅ Response status: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"📨 Response body:")
                print(json.dumps(response_data, indent=2))
                
                if response.status_code == 200:
                    if 'success' in response_data and response_data['success']:
                        print("🎉 Deposit test successful!")
                    else:
                        print("⚠️  Deposit returned error:", response_data.get('error', 'Unknown error'))
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    
            except json.JSONDecodeError:
                print(f"⚠️  Response is not JSON: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed: Cannot connect to {url}")
        except requests.exceptions.Timeout:
            print(f"❌ Request timeout: {url}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")

def test_multiple_amounts():
    """Test different deposit amounts"""
    print("\n" + "=" * 50)
    print("💰 Testing Different Deposit Amounts")
    print("=" * 50)
    
    amounts = [10.0, 50.0, 100.0, 200.0, 500.0]
    base_url = "https://updated-eight-ashy.vercel.app"
    
    for amount in amounts:
        test_data = {
            "amount": amount,
            "phone": "0941043869",
            "method": "telebirr",
            "reference": f"TEST-AMT-{amount}-{datetime.now().strftime('%H%M%S')}"
        }
        
        print(f"\n🔢 Testing amount: {amount} Birr")
        
        try:
            response = requests.post(
                f"{base_url}/webhook/test",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Test passed for {amount} Birr")
            else:
                print(f"❌ Test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_webhook_validation():
    """Test webhook validation and formatting"""
    print("\n" + "=" * 50)
    print("🧪 Testing Webhook Validation")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Valid deposit",
            "data": {
                "amount": 100.0,
                "phone": "0941043869",
                "method": "cbe",
                "reference": "TEST-VALID"
            },
            "expected": "success"
        },
        {
            "name": "Missing amount",
            "data": {
                "phone": "0941043869",
                "method": "cbe"
            },
            "expected": "error"
        },
        {
            "name": "Missing phone",
            "data": {
                "amount": 100.0,
                "method": "cbe"
            },
            "expected": "error"
        },
        {
            "name": "Invalid amount (negative)",
            "data": {
                "amount": -100.0,
                "phone": "0941043869",
                "method": "cbe"
            },
            "expected": "error"
        },
        {
            "name": "Invalid phone format",
            "data": {
                "amount": 100.0,
                "phone": "invalid",
                "method": "cbe"
            },
            "expected": "error"
        }
    ]
    
    base_url = "https://updated-eight-ashy.vercel.app"
    
    for test in test_cases:
        print(f"\n📝 Test: {test['name']}")
        print(f"   Data: {json.dumps(test['data'], indent=4)}")
        
        try:
            response = requests.post(
                f"{base_url}/webhook/test",
                json=test['data'],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'status' in result and result['status'] == test['expected']:
                    print(f"✅ Result matches expected: {test['expected']}")
                else:
                    print(f"⚠️  Result: {result.get('status', 'unknown')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def test_deposit_instructions():
    """Test deposit instructions endpoint"""
    print("\n" + "=" * 50)
    print("📋 Testing Deposit Instructions")
    print("=" * 50)
    
    base_url = "https://updated-eight-ashy.vercel.app"
    
    try:
        response = requests.get(
            f"{base_url}/deposit/instructions",
            timeout=5
        )
        
        print(f"📄 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('success', False)}")
            print(f"📝 Instructions available")
            
            # Show account details
            if 'instructions' in data:
                print("\n🏦 Account Details:")
                print(f"   CBE: {data['instructions']['cbe']['name']} - {data['instructions']['cbe']['account']}")
                print(f"   TeleBirr: {data['instructions']['telebirr']['name']} - {data['instructions']['telebirr']['account']}")
        else:
            print(f"❌ Failed to get instructions")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Deposit Webhook Tests")
    print("=" * 50)
    
    # Run all tests
    test_tasker_deposit()
    test_multiple_amounts()
    test_webhook_validation()
    test_deposit_instructions()
    
    print("\n" + "=" * 50)
    print("🎯 All tests completed!")
    print("=" * 50)
    print("\n📱 Your Phone: 0941043869")
    print("🏦 CBE Account: SAMSON MESFIN - 100348220032")
    print("📱 TeleBirr: NITSU - 0976233815")
    print(f"🌐 Webhook URL: https://updated-eight-ashy.vercel.app/webhook/deposit")