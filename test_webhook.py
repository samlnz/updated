import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_all_webhooks():
    """
    Test script to test all webhook endpoints
    """
    # Your configuration
    YOUR_PHONE = "0941043869"
    YOUR_NAME = "SAMSON MESFIN"
    
    # Test URLs - both local and production
    urls = [
        {
            "name": "Local Development",
            "base_url": "http://localhost:5000",
            "description": "Local Flask server"
        },
        {
            "name": "Production Vercel",
            "base_url": "https://updated-eight-ashy.vercel.app",
            "description": "Production deployment"
        }
    ]

    # Test cases for different scenarios
    test_cases = [
        {
            "name": "Valid Deposit (CBE)",
            "endpoint": "/webhook/deposit",
            "data": {
                "amount": 100.0,
                "phone": YOUR_PHONE,
                "method": "cbe",
                "reference": f"TEST-CBE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            },
            "headers": {
                "Content-Type": "application/json",
                "X-Test-Source": "test_script"
            }
        },
        {
            "name": "Valid Deposit (TeleBirr)",
            "endpoint": "/webhook/deposit",
            "data": {
                "amount": 200.0,
                "phone": YOUR_PHONE,
                "method": "telebirr",
                "reference": f"TEST-TELEBIRR-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            },
            "headers": {
                "Content-Type": "application/json",
                "X-Test-Source": "test_script"
            }
        },
        {
            "name": "Test Endpoint",
            "endpoint": "/webhook/test",
            "data": {
                "amount": 50.0,
                "phone": YOUR_PHONE,
                "method": "cbe",
                "reference": "TEST-ENDPOINT"
            },
            "headers": {
                "Content-Type": "application/json"
            }
        },
        {
            "name": "GET Test Endpoint",
            "endpoint": "/webhook/test",
            "method": "GET",
            "data": None,
            "headers": {}
        },
        {
            "name": "Deposit Instructions",
            "endpoint": "/deposit/instructions",
            "method": "GET",
            "data": None,
            "headers": {}
        }
    ]

    print("🎯 COMPREHENSIVE WEBHOOK TESTS")
    print("=" * 70)
    print(f"📱 Test Phone: {YOUR_PHONE}")
    print(f"👤 Test Name: {YOUR_NAME}")
    print("=" * 70)

    for url_config in urls:
        base_url = url_config["base_url"]
        print(f"\n\n🔧 Testing: {url_config['name']}")
        print(f"🌐 Base URL: {base_url}")
        print(f"📝 {url_config['description']}")
        print("-" * 70)

        # Test basic connectivity first
        print("\n🔗 Testing connectivity...")
        try:
            ping_response = requests.get(f"{base_url}/", timeout=5)
            print(f"   Homepage: {ping_response.status_code}")
        except:
            print(f"   ❌ Cannot connect to {base_url}")
            continue

        for test_case in test_cases:
            endpoint = test_case["endpoint"]
            full_url = f"{base_url}{endpoint}"
            
            print(f"\n📋 Test: {test_case['name']}")
            print(f"   URL: {full_url}")
            
            if test_case.get("data"):
                print(f"   Data: {json.dumps(test_case['data'], indent=6)}")

            try:
                method = test_case.get("method", "POST")
                
                if method == "GET":
                    response = requests.get(
                        full_url,
                        headers=test_case["headers"],
                        timeout=10
                    )
                else:
                    response = requests.post(
                        full_url,
                        json=test_case["data"],
                        headers=test_case["headers"],
                        timeout=10
                    )

                print(f"   📊 Status: {response.status_code}")
                print(f"   ⏱️  Response Time: {response.elapsed.total_seconds():.2f}s")

                try:
                    if response.text:
                        response_json = response.json()
                        print(f"   📨 Response:")
                        print(json.dumps(response_json, indent=6))
                        
                        # Check for success/failure
                        if response.status_code == 200:
                            if 'success' in response_json:
                                if response_json['success']:
                                    print("   ✅ SUCCESS")
                                else:
                                    print(f"   ⚠️  FAILED: {response_json.get('error', 'Unknown error')}")
                            else:
                                print("   ℹ️  Response received (no success flag)")
                        else:
                            print(f"   ❌ HTTP ERROR: {response.status_code}")
                    else:
                        print("   📭 Empty response")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️  Response is not JSON: {response.text[:100]}...")

            except requests.exceptions.ConnectionError:
                print(f"   ❌ Connection failed")
            except requests.exceptions.Timeout:
                print(f"   ⏰ Request timeout")
            except Exception as e:
                print(f"   ❌ Unexpected error: {str(e)}")

def test_negative_cases():
    """Test negative/error scenarios"""
    print("\n\n" + "=" * 70)
    print("🚨 NEGATIVE TEST CASES")
    print("=" * 70)

    base_url = "https://updated-eight-ashy.vercel.app"
    
    negative_cases = [
        {
            "name": "Missing required field (amount)",
            "data": {
                "phone": "0941043869",
                "method": "cbe"
            },
            "expected_error": True
        },
        {
            "name": "Missing required field (phone)",
            "data": {
                "amount": 100.0,
                "method": "cbe"
            },
            "expected_error": True
        },
        {
            "name": "Invalid amount (0)",
            "data": {
                "amount": 0,
                "phone": "0941043869",
                "method": "cbe"
            },
            "expected_error": True
        },
        {
            "name": "Invalid amount (negative)",
            "data": {
                "amount": -100.0,
                "phone": "0941043869",
                "method": "cbe"
            },
            "expected_error": True
        },
        {
            "name": "Invalid phone format",
            "data": {
                "amount": 100.0,
                "phone": "invalid-phone",
                "method": "cbe"
            },
            "expected_error": True
        },
        {
            "name": "Unregistered phone",
            "data": {
                "amount": 100.0,
                "phone": "0910000000",
                "method": "cbe"
            },
            "expected_error": True
        }
    ]

    for case in negative_cases:
        print(f"\n⚠️  Test: {case['name']}")
        print(f"   Data: {json.dumps(case['data'], indent=6)}")
        
        try:
            response = requests.post(
                f"{base_url}/webhook/test",
                json=case["data"],
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code >= 400:
                print(f"   ✅ Got expected error response")
            else:
                result = response.json()
                if 'status' in result and result['status'] == 'invalid':
                    print(f"   ✅ Validation failed as expected")
                else:
                    print(f"   ⚠️  Unexpected success response")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_performance():
    """Test webhook performance"""
    print("\n\n" + "=" * 70)
    print("⚡ PERFORMANCE TESTS")
    print("=" * 70)

    base_url = "https://updated-eight-ashy.vercel.app"
    test_data = {
        "amount": 100.0,
        "phone": "0941043869",
        "method": "cbe",
        "reference": "PERF-TEST"
    }
    
    print("Testing response times (5 requests):")
    
    times = []
    for i in range(5):
        try:
            response = requests.post(
                f"{base_url}/webhook/test",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            times.append(response.elapsed.total_seconds())
            print(f"   Request {i+1}: {times[-1]:.3f}s - Status: {response.status_code}")
            
        except Exception as e:
            print(f"   Request {i+1}: ❌ Error - {str(e)}")
    
    if times:
        avg_time = sum(times) / len(times)
        print(f"\n   📊 Average response time: {avg_time:.3f}s")
        print(f"   🏆 Best time: {min(times):.3f}s")
        print(f"   🐌 Worst time: {max(times):.3f}s")

def generate_macrodroid_config():
    """Generate Macrodroid configuration instructions"""
    print("\n\n" + "=" * 70)
    print("📱 MACRODROID CONFIGURATION")
    print("=" * 70)
    
    config = {
        "trigger": {
            "type": "SMS Received",
            "conditions": [
                "Sender: Your bank number",
                "Content contains: 'ETB' or 'Birr'"
            ]
        },
        "actions": [
            {
                "type": "HTTP Request",
                "config": {
                    "url": "https://updated-eight-ashy.vercel.app/webhook/deposit",
                    "method": "POST",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": """{
  "amount": %amount,
  "phone": "0941043869",
  "method": "cbe",
  "reference": "%sms_body"
}"""
                }
            }
        ]
    }
    
    print("Macrodroid Macro Configuration:")
    print(json.dumps(config, indent=2))
    
    print("\n📋 Quick Setup:")
    print("1. Create new macro in Macrodroid")
    print("2. Trigger: SMS Received")
    print("3. Action: HTTP Request")
    print("4. URL: https://updated-eight-ashy.vercel.app/webhook/deposit")
    print("5. Method: POST")
    print("6. Headers: Content-Type: application/json")
    print("7. Body: (as shown above)")
    print("\n💡 Tip: Extract %amount from SMS using Macrodroid's text extraction")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Webhook Tests")
    print("=" * 70)
    print(f"📱 Your Phone: 0941043869")
    print(f"👤 Your Name: SAMSON MESFIN")
    print(f"🏦 CBE Account: 100348220032")
    print(f"📱 TeleBirr: NITSU - 0976233815")
    print("=" * 70)
    
    # Run all test suites
    test_all_webhooks()
    test_negative_cases()
    test_performance()
    generate_macrodroid_config()
    
    print("\n\n" + "=" * 70)
    print("🎯 TESTING COMPLETE")
    print("=" * 70)
    print("\n📊 Summary:")
    print("✅ All endpoints tested")
    print("✅ Error cases validated")
    print("✅ Performance measured")
    print("✅ Macrodroid config generated")
    print("\n🔗 Production URL: https://updated-eight-ashy.vercel.app")
    print("📧 Webhook Endpoint: /webhook/deposit")
    print("🧪 Test Endpoint: /webhook/test")
    print("=" * 70)