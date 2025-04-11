
#!/usr/bin/env python3
"""
اسکریپت برای تنظیم وب‌هوک تلگرام بات
"""
import json
import os
import sys
import requests

def set_webhook(bot_token, webhook_url):
    """
    تنظیم وب‌هوک برای ربات تلگرام
    
    Args:
        bot_token (str): توکن ربات تلگرام
        webhook_url (str): آدرس کامل وب‌هوک
        
    Returns:
        dict: پاسخ دریافتی از API تلگرام
    """
    # ابتدا وب‌هوک موجود را حذف می‌کنیم
    delete_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    print(f"Deleting existing webhook...")
    delete_response = requests.get(delete_url)
    print(f"Delete response: {delete_response.json()}")
    
    # تنظیم وب‌هوک جدید با پارامترهای بهینه
    webhook_params = {
        'url': webhook_url,
        'max_connections': 40,
        'drop_pending_updates': True,
        'allowed_updates': ['message', 'callback_query']
    }
    
    set_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    print(f"Setting webhook to: {webhook_url}")
    set_response = requests.post(set_url, json=webhook_params)
    print(f"Set webhook response: {set_response.json()}")
    
    # بررسی تنظیمات وب‌هوک
    info_url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    info_response = requests.get(info_url)
    print(f"Webhook info: {json.dumps(info_response.json(), indent=2)}")
    
    return set_response.json()

def main():
    """
    تابع اصلی برنامه
    """
    # با توجه به آدرس ری‌پلیت، آدرس وب‌هوک را تنظیم می‌کنیم
    replit_domain = "آدرس_دامنه_ریپلیت_شما.replit.dev"  # آدرس دامنه ریپلیت خود را وارد کنید
    webhook_path = "/webhook/VSimsbot"
    
    # آدرس کامل وب‌هوک
    replit_domain = "نام-ریپلیت-شما.replit.dev"  # نام ریپلیت خود را اینجا وارد کنید
    webhook_url = f"https://{replit_domain}{webhook_path}"
    
    # توکن بات را از آرگومان‌های برنامه یا فایل کانفیگ دریافت می‌کنیم
    bot_token = "توکن_ربات_خود_را_اینجا_وارد_کنید"  # توکن ربات خود را اینجا وارد کنید
    
    if not bot_token:
        print("Error: Bot token is required.")
        sys.exit(1)
    
    try:
        result = set_webhook(bot_token, webhook_url)
        if result.get('ok'):
            print("Webhook set successfully!")
        else:
            print(f"Failed to set webhook: {result.get('description')}")
    except Exception as e:
        print(f"Error setting webhook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
