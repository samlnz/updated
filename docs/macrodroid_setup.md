# 📱 Macrodroid Setup Guide for Addis Bingo

## What is Macrodroid?
Macrodroid is an automation app for Android that can automatically forward SMS messages to our server when you receive money.

## Step-by-Step Setup

### Step 1: Install Macrodroid
1. Download Macrodroid from Google Play Store
2. Open the app and grant necessary permissions:
   - SMS permission
   - Internet permission
   - Notification access

### Step 2: Create New Macro

1. Tap the **+** button to create new macro
2. **Trigger**: Select "SMS Received"
3. **Trigger Configuration**:
   - Sender: Leave empty (to catch all banks)
   - Content Contains: `ETB` OR `ብር` OR `birr`
   - Enable Regex: `.*(ETB|ብር|birr).*\d+\.\d{2}.*`

### Step 3: Add Actions

**Action 1: HTTP Post**
- Action Type: "HTTP Request"
- Method: POST
- URL: `https://updated-eight-ashy.vercel.app/webhook/macrodroid`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "sms_text": "{sms_body}",
  "sender_number": "{sms_sender}",
  "timestamp": "{datetime}",
  "device_id": "{device_id}"
}