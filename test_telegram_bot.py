import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_telegram_bot_api():
    """Test Telegram Bot API endpoints"""
    print("🤖 Testing Telegram Bot Integration")
    print("=" * 50)
    
    # Your bot token (be careful with this)
    BOT_TOKEN = "8502890042:AAG3OO2L-1g1GFz4MUcENizttUvZC1aHspM"
    
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        print("❌ Please set your Telegram Bot Token in the code")
        return
    
    # Test bot info
    try:
        print("\n🔍 Testing bot info...")
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe")
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print("✅ Bot is active!")
                print(f"   🤖 Bot: @{bot_info['result']['username']}")
                print(f"   📛 Name: {bot_info['result']['first_name']}")
                print(f"   🆔 ID: {bot_info['result']['id']}")
            else:
                print("❌ Bot response not OK")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_web_app():
    """Test Telegram Web App integration"""
    print("\n🌐 Testing Web App Integration")
    print("=" * 50)
    
    webapp_url = "https://updated-eight-ashy.vercel.app"
    
    endpoints = [
        "/",
        "/lobby",
        "/deposit/instructions",
        "/webhook/test"
    ]
    
    for endpoint in endpoints:
        url = f"{webapp_url}{endpoint}"
        print(f"\n🔗 Testing: {endpoint}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Accessible")
                
                # Check if it's HTML
                if 'text/html' in response.headers.get('content-type', ''):
                    print("   📄 HTML page")
                elif 'application/json' in response.headers.get('content-type', ''):
                    print("   📊 JSON API")
            elif response.status_code == 302:
                print("   🔀 Redirecting")
            else:
                print("   ⚠️  Unexpected status")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_game_endpoints():
    """Test game-related endpoints"""
    print("\n🎮 Testing Game Endpoints")
    print("=" * 50)
    
    base_url = "https://updated-eight-ashy.vercel.app"
    
    # Test creating a game
    print("\n🎰 Testing game creation...")
    try:
        response = requests.post(
            f"{base_url}/game/create",
            json={"entry_price": 10},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Game created: {data}")
            
            if data.get('success'):
                game_id = data.get('game_id')
                print(f"   🆔 Game ID: {game_id}")
                
                # Test game endpoints
                endpoints = [
                    f"/game/{game_id}/select",
                    f"/game/{game_id}"
                ]
                
                for endpoint in endpoints:
                    url = f"{base_url}{endpoint}"
                    print(f"\n   🔗 Testing: {endpoint}")
                    try:
                        page_response = requests.get(url, timeout=5)
                        print(f"      Status: {page_response.status_code}")
                        print(f"      Type: {page_response.headers.get('content-type', 'unknown')}")
                    except Exception as e:
                        print(f"      ❌ Error: {str(e)}")
        else:
            print(f"   ❌ Failed to create game")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

def generate_qr_code():
    """Generate QR code for easy access"""
    print("\n📱 Generating Quick Access Links")
    print("=" * 50)
    
    webapp_url = "https://updated-eight-ashy.vercel.app"
    bot_username = "your_bot_username"  # Replace with actual bot username
    
    links = {
        "Web App": webapp_url,
        "Game Lobby": f"{webapp_url}/lobby",
        "Deposit Instructions": f"{webapp_url}/deposit/instructions",
        "Webhook Test": f"{webapp_url}/webhook/test",
        "Telegram Bot": f"https://t.me/{bot_username}",
        "Bot with Start": f"https://t.me/{bot_username}?start=test"
    }
    
    print("🔗 Quick Links:")
    for name, url in links.items():
        print(f"   {name}: {url}")
    
    # Generate QR code URLs
    print("\n📷 QR Code URLs:")
    for name, url in links.items():
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}"
        print(f"   {name}: {qr_url}")

if __name__ == "__main__":
    print("🚀 Telegram Bot & Web App Test Suite")
    print("=" * 50)
    
    # Uncomment to test bot API (requires valid token)
    # test_telegram_bot_api()
    
    test_web_app()
    test_game_endpoints()
    generate_qr_code()
    
    print("\n" + "=" * 50)
    print("🎯 Testing Complete!")
    print("=" * 50)
    print("\n📋 Next Steps:")
    print("1. Start the bot: python bot.py")
    print("2. Start web app: python app.py")
    print("3. Test with: python test_deposit.py")
    print("4. Configure Macrodroid with generated config")
    print("=" * 50)