
import threading
import time
import requests
import logging
import os
import subprocess
import sys
import signal

# تنظیم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("keep_alive")

# آدرس و پورت وب‌سرور
HOST = "0.0.0.0"
PORT = 5000

# متغیر برای نگهداری فرآیند ربات
bot_process = None
last_restart_time = 0
restart_count = 0

def run_flask_server():
    """راه‌اندازی یک وب‌سرور ساده برای جلوگیری از خواب رفتن replit"""
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return "ربات تلگرام در حال اجراست! آخرین راه‌اندازی مجدد: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_restart_time))
    
    @app.route('/status')
    def status():
        global bot_process
        if bot_process and bot_process.poll() is None:
            return "ربات در حال اجراست"
        else:
            return "ربات متوقف شده است"
    
    @app.route('/restart')
    def restart():
        restart_bot()
        return "فرمان راه‌اندازی مجدد ارسال شد"
    
    app.run(host=HOST, port=PORT)

def start_bot():
    """راه‌اندازی ربات تلگرام"""
    global bot_process, last_restart_time, restart_count
    
    # بررسی فرآیند قبلی
    if bot_process and bot_process.poll() is None:
        logger.info("ربات در حال حاضر در حال اجراست")
        return
        
    try:
        # کشتن تمام فرآیندهای قبلی با نام مشابه
        kill_zombie_processes()
        
        # راه‌اندازی مجدد ربات
        logger.info("در حال راه‌اندازی ربات تلگرام...")
        bot_process = subprocess.Popen(
            [sys.executable, "run_telegram_bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        last_restart_time = time.time()
        restart_count += 1
        
        # راه‌اندازی یک نخ برای خواندن و ثبت خروجی ربات
        threading.Thread(target=log_output, args=(bot_process,), daemon=True).start()
        
        logger.info(f"ربات تلگرام با PID {bot_process.pid} راه‌اندازی شد")
    except Exception as e:
        logger.error(f"خطا در راه‌اندازی ربات: {str(e)}")

def log_output(process):
    """ثبت خروجی فرآیند در لاگ‌ها"""
    try:
        for line in process.stdout:
            logger.info(f"BOT: {line.strip()}")
    except Exception as e:
        logger.error(f"خطا در خواندن خروجی ربات: {str(e)}")

def check_bot_status():
    """بررسی وضعیت ربات و راه‌اندازی مجدد در صورت نیاز"""
    global bot_process
    
    while True:
        try:
            if not bot_process or bot_process.poll() is not None:
                logger.warning("ربات متوقف شده است! در حال راه‌اندازی مجدد...")
                start_bot()
            else:
                # هر یک ساعت یک بار ربات را راه‌اندازی مجدد می‌کنیم تا از مشکلات احتمالی جلوگیری شود
                current_time = time.time()
                if current_time - last_restart_time > 3600:  # یک ساعت
                    logger.info("راه‌اندازی مجدد دوره‌ای ربات...")
                    restart_bot()
        except Exception as e:
            logger.error(f"خطا در بررسی وضعیت ربات: {str(e)}")
            
        time.sleep(30)  # بررسی هر 30 ثانیه

def restart_bot():
    """راه‌اندازی مجدد ربات"""
    global bot_process
    
    logger.info("در حال راه‌اندازی مجدد ربات...")
    
    # متوقف کردن فرآیند فعلی
    if bot_process:
        try:
            bot_process.terminate()
            # صبر برای خاتمه
            try:
                bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                bot_process.kill()
        except Exception as e:
            logger.error(f"خطا در متوقف کردن ربات: {str(e)}")
    
    # راه‌اندازی مجدد
    start_bot()

def kill_zombie_processes():
    """کشتن فرآیندهای زامبی"""
    try:
        output = subprocess.check_output(["ps", "aux"], universal_newlines=True)
        lines = output.strip().split('\n')
        
        for line in lines:
            if "run_telegram_bot.py" in line and "python" in line:
                # استخراج PID
                parts = line.split()
                if len(parts) > 1:
                    pid = int(parts[1])
                    
                    # کشتن فرآیند
                    try:
                        os.kill(pid, signal.SIGTERM)
                        logger.info(f"فرآیند زامبی با PID {pid} متوقف شد")
                    except ProcessLookupError:
                        pass
                    except Exception as e:
                        logger.error(f"خطا در کشتن فرآیند زامبی: {str(e)}")
    except Exception as e:
        logger.error(f"خطا در یافتن فرآیندهای زامبی: {str(e)}")

def main():
    """تابع اصلی برای راه‌اندازی و نگهداری ربات"""
    logger.info("سیستم نگهداری ربات تلگرام در حال راه‌اندازی...")
    
    # راه‌اندازی ربات
    start_bot()
    
    # راه‌اندازی نخ‌های نظارت
    status_thread = threading.Thread(target=check_bot_status, daemon=True)
    status_thread.start()
    
    # راه‌اندازی وب‌سرور در نخ اصلی
    try:
        run_flask_server()
    except KeyboardInterrupt:
        logger.info("دریافت سیگنال توقف از کاربر. در حال خروج...")
    except Exception as e:
        logger.error(f"خطا در اجرای وب‌سرور: {str(e)}")
    finally:
        # متوقف کردن ربات هنگام خروج
        if bot_process:
            bot_process.terminate()
            logger.info("ربات متوقف شد")

if __name__ == "__main__":
    main()
