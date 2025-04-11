
import requests
import config_manager
import json

# توکن جدید ربات
NEW_TOKEN = "توکن_جدید_خود_را_اینجا_قرار_دهید"

# آدرس دامنه ری‌پلیت
REPLIT_DOMAIN = "آدرس_دامنه_ریپلیت_شما.replit.dev"

# مسیر وب‌هوک
WEBHOOK_PATH = "/webhook/VSimsbot"

# آدرس کامل وب‌هوک
webhook_url = f"https://{REPLIT_DOMAIN}{WEBHOOK_PATH}"

print(f"تنظیم توکن ربات به: {NEW_TOKEN}")
print(f"تنظیم آدرس وب‌هوک به: {webhook_url}")

# ذخیره توکن جدید در config_data.json
config_manager.set_config_value("bot_token", NEW_TOKEN)
print("توکن با موفقیت در فایل تنظیمات ذخیره شد.")

# حذف وب‌هوک قبلی
delete_url = f"https://api.telegram.org/bot{NEW_TOKEN}/deleteWebhook"
delete_response = requests.get(delete_url)
print(f"پاسخ حذف وب‌هوک قبلی: {delete_response.json()}")

# تنظیم وب‌هوک جدید
webhook_params = {
    'url': webhook_url,
    'max_connections': 40,
    'drop_pending_updates': True,
    'allowed_updates': ['message', 'callback_query']
}

set_url = f"https://api.telegram.org/bot{NEW_TOKEN}/setWebhook"
set_response = requests.post(set_url, json=webhook_params)
print(f"پاسخ تنظیم وب‌هوک جدید: {set_response.json()}")

# بررسی تنظیمات وب‌هوک
info_url = f"https://api.telegram.org/bot{NEW_TOKEN}/getWebhookInfo"
info_response = requests.get(info_url)
print(f"اطلاعات وب‌هوک: {json.dumps(info_response.json(), indent=2)}")
