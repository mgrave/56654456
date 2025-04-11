#!/usr/bin/env python3
"""
اسکریپت تست سیستم لاگینگ
این اسکریپت همه لاگرهای سیستم را تست می‌کند و به شما نشان می‌دهد آیا آنها به درستی کار می‌کنند یا خیر
"""

import os
import sys
import logging
import logging_config
import time
from datetime import datetime

def main():
    print("شروع تست سیستم لاگینگ...")

    # اطمینان از وجود پوشه لاگ
    if not os.path.exists(logging_config.LOG_DIR):
        try:
            os.makedirs(logging_config.LOG_DIR)
            print(f"پوشه لاگ ایجاد شد: {logging_config.LOG_DIR}")
        except Exception as e:
            print(f"خطا در ایجاد پوشه لاگ: {str(e)}")
            sys.exit(1)

    # باز تنظیم لاگرها
    loggers = logging_config.setup_all_loggers()

    print(f"مسیر پوشه لاگ: {os.path.abspath(logging_config.LOG_DIR)}")

    # تست لاگ در همه لاگرها
    for logger_name, logger in loggers.items():
        # تست سطوح مختلف لاگ
        logger.debug(f"پیام تست DEBUG در لاگر {logger_name}")
        logger.info(f"پیام تست INFO در لاگر {logger_name}")
        logger.warning(f"پیام تست WARNING در لاگر {logger_name}")
        logger.error(f"پیام تست ERROR در لاگر {logger_name}")

        print(f"✅ لاگر '{logger_name}' تست شد")


    print("\nوضعیت کلی لاگ‌ها:")

    # نمایش همه فایل‌های لاگ و اندازه آنها
    log_files = [f for f in os.listdir(logging_config.LOG_DIR) if f.endswith('.log')]
    for log_file in log_files:
        full_path = os.path.join(logging_config.LOG_DIR, log_file)
        file_size = os.path.getsize(full_path)
        last_modified = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {log_file}: {file_size} بایت (آخرین بروزرسانی: {last_modified})")

    print("\nتست لاگینگ به پایان رسید. لطفاً فایل‌های لاگ را در پوشه logs بررسی کنید.")

if __name__ == "__main__":
    main()