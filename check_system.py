
#!/usr/bin/env python
"""
اسکریپت بررسی وضعیت سیستم
"""

import os
import sys
import subprocess
import platform

print("=== بررسی وضعیت سیستم ===")
print(f"سیستم عامل: {platform.system()} {platform.release()}")
print(f"نسخه پایتون: {sys.version}")
print(f"مسیر پایتون: {sys.executable}")
print(f"دایرکتوری فعلی: {os.getcwd()}")

print("\n=== بررسی فایل‌های اصلی ===")
critical_files = [
    "app.py", 
    "main.py", 
    "run_telegram_bot.py", 
    "start_system.py",
    ".env.example"
]

for file in critical_files:
    if os.path.exists(file):
        print(f"✓ فایل {file} موجود است")
    else:
        print(f"✗ فایل {file} یافت نشد!")

print("\n=== بررسی ماژول‌های پایتون ===")
required_modules = [
    "flask", "telebot", "sqlalchemy", "requests", "gunicorn"
]

for module in required_modules:
    try:
        __import__(module)
        print(f"✓ ماژول {module} نصب شده است")
    except ImportError:
        print(f"✗ ماژول {module} نصب نشده است")

print("\n=== بررسی تنظیمات محیطی ===")
env_vars = [
    "TELEGRAM_BOT_TOKEN", 
    "DATABASE_URL", 
    "SESSION_SECRET"
]

for var in env_vars:
    if os.getenv(var):
        masked_value = "***" + os.getenv(var)[-4:] if os.getenv(var) else ""
        print(f"✓ متغیر {var} تنظیم شده است: {masked_value}")
    else:
        print(f"✗ متغیر {var} تنظیم نشده است")

print("\n=== پایان بررسی ===")
print("برای راه‌اندازی سیستم، از دکمه Run استفاده کنید")
