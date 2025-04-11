#!/usr/bin/env python3
"""
اسکریپت ساده برای راه‌اندازی ربات تلگرام
"""

import os
import sys
import subprocess
import time
import logging

# تنظیم لاگینگ پایه
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("bot_starter")

def main():
    """تابع اصلی راه‌اندازی ربات"""
    logger.info("در حال راه‌اندازی ربات تلگرام...")

    try:
        # اجرای ربات
        subprocess.run([sys.executable, "run_telegram_bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"خطا در اجرای ربات: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("دریافت سیگنال توقف. در حال خروج...")
    except Exception as e:
        logger.error(f"خطای غیرمنتظره: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())