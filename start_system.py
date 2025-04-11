
#!/usr/bin/env python3
"""
اسکریپت راه‌اندازی کامل سیستم
این اسکریپت هم ربات تلگرام و هم وب اپلیکیشن را به طور همزمان اجرا می‌کند
"""

import os
import sys
import time
import subprocess
import signal
import logging

# تنظیم لاگینگ پایه
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("system_starter")

# فرآیندهای در حال اجرا
processes = []

def signal_handler(sig, frame):
    """مدیریت سیگنال‌های سیستمی برای خروج تمیز"""
    logger.info("دریافت سیگنال خروج. در حال توقف فرآیندها...")
    for process in processes:
        try:
            process.terminate()
            logger.info(f"فرآیند {process.pid} متوقف شد")
        except Exception as e:
            logger.error(f"خطا در توقف فرآیند: {str(e)}")
    
    logger.info("همه فرآیندها متوقف شدند. در حال خروج...")
    sys.exit(0)

def start_bot():
    """راه‌اندازی ربات تلگرام"""
    logger.info("در حال راه‌اندازی ربات تلگرام...")
    bot_process = subprocess.Popen(
        [sys.executable, "run_telegram_bot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(bot_process)
    logger.info(f"ربات تلگرام با PID {bot_process.pid} راه‌اندازی شد")
    return bot_process

def start_web_app():
    """راه‌اندازی وب اپلیکیشن"""
    logger.info("در حال راه‌اندازی وب اپلیکیشن...")
    web_process = subprocess.Popen(
        ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "main:app"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    processes.append(web_process)
    logger.info(f"وب اپلیکیشن با PID {web_process.pid} راه‌اندازی شد")
    return web_process

def monitor_output(process, name):
    """نمایش خروجی فرآیند در کنسول"""
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            print(f"[{name}] {line.strip()}")

def main():
    """تابع اصلی برای راه‌اندازی و مدیریت فرآیندها"""
    # ثبت هندلر برای سیگنال‌های خروج
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("شروع راه‌اندازی کامل سیستم...")
    
    # راه‌اندازی ربات تلگرام
    bot_process = start_bot()
    
    # صبر کوتاه برای اطمینان از راه‌اندازی ربات
    time.sleep(2)
    
    # راه‌اندازی وب اپلیکیشن
    web_process = start_web_app()
    
    logger.info("همه اجزای سیستم با موفقیت راه‌اندازی شدند!")
    logger.info("برای خروج، کلیدهای Ctrl+C را فشار دهید")
    
    # مانیتورینگ خروجی فرآیندها
    import threading
    bot_monitor = threading.Thread(target=monitor_output, args=(bot_process, "BOT"))
    web_monitor = threading.Thread(target=monitor_output, args=(web_process, "WEB"))
    
    bot_monitor.daemon = True
    web_monitor.daemon = True
    
    bot_monitor.start()
    web_monitor.start()
    
    # حلقه اصلی برای نگه داشتن برنامه
    try:
        while all(p.poll() is None for p in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("دریافت KeyboardInterrupt، در حال خروج...")
    finally:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
