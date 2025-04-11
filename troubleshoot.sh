#!/bin/bash
# اسکریپت عیب‌یابی برای سیستم مدیریت اشتراک تلگرام پرمیوم
# نویسنده: سیستم هوش مصنوعی
# تاریخ: آوریل 2025

# رنگ‌های متن
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# نمایش بنر شروع
echo -e "${BLUE}=== اسکریپت عیب‌یابی سیستم مدیریت اشتراک تلگرام پرمیوم ===${NC}"
echo ""
echo -e "این اسکریپت برای عیب‌یابی و بررسی وضعیت سیستم استفاده می‌شود."
echo -e "موارد زیر بررسی خواهند شد:"
echo -e "  - پیش‌نیازهای سیستم"
echo -e "  - فایل‌های تنظیمات"
echo -e "  - اتصال به دیتابیس"
echo -e "  - وضعیت ربات تلگرام"
echo -e "  - مجوزهای فایل‌ها"
echo -e "  - فضای دیسک"
echo -e ""
echo -e "${YELLOW}فرآیند عیب‌یابی آغاز می‌شود...${NC}"
echo ""

# بررسی پیش‌نیازهای سیستم
echo -e "${BLUE}[1/7] بررسی پیش‌نیازهای سیستم${NC}"

# بررسی پایتون
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "  ${GREEN}✓ پایتون نصب شده است: $PYTHON_VERSION${NC}"
else
    echo -e "  ${RED}✗ پایتون نصب نشده است. لطفاً پایتون 3.8 یا بالاتر را نصب کنید.${NC}"
fi

# بررسی pip
if command -v pip3 &> /dev/null; then
    PIP_VERSION=$(pip3 --version)
    echo -e "  ${GREEN}✓ pip نصب شده است: $PIP_VERSION${NC}"
else
    echo -e "  ${RED}✗ pip نصب نشده است. لطفاً pip را نصب کنید.${NC}"
fi

# بررسی PostgreSQL
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    echo -e "  ${GREEN}✓ PostgreSQL نصب شده است: $PSQL_VERSION${NC}"
else
    echo -e "  ${RED}✗ PostgreSQL نصب نشده است. لطفاً PostgreSQL را نصب کنید.${NC}"
fi

# بررسی وابستگی‌های پایتون
echo ""
echo -e "${BLUE}[2/7] بررسی وابستگی‌های پایتون${NC}"

REQUIRED_PACKAGES=("flask" "sqlalchemy" "psycopg2" "telebot" "requests" "flask-login" "python-dotenv" "alembic")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" &> /dev/null; then
        echo -e "  ${GREEN}✓ $package نصب شده است${NC}"
    else
        echo -e "  ${RED}✗ $package نصب نشده است${NC}"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}بسته‌های گم شده را نصب می‌کنید؟ (y/n)${NC}"
    read -p " " install_packages
    
    if [ "$install_packages" = "y" ] || [ "$install_packages" = "Y" ]; then
        echo -e "نصب بسته‌های گم شده..."
        pip3 install ${MISSING_PACKAGES[@]}
        echo -e "${GREEN}بسته‌ها نصب شدند.${NC}"
    fi
fi

# بررسی فایل‌های تنظیمات
echo ""
echo -e "${BLUE}[3/7] بررسی فایل‌های تنظیمات${NC}"

if [ -f ".env" ]; then
    echo -e "  ${GREEN}✓ فایل .env وجود دارد${NC}"
    
    # بررسی متغیرهای ضروری در .env
    ENV_ISSUES=0
    
    if grep -q "TELEGRAM_BOT_TOKEN" .env; then
        echo -e "  ${GREEN}✓ TELEGRAM_BOT_TOKEN در .env تنظیم شده است${NC}"
    else
        echo -e "  ${RED}✗ TELEGRAM_BOT_TOKEN در .env تنظیم نشده است${NC}"
        ENV_ISSUES=$((ENV_ISSUES+1))
    fi
    
    if grep -q "DATABASE_URL" .env; then
        echo -e "  ${GREEN}✓ DATABASE_URL در .env تنظیم شده است${NC}"
    else
        echo -e "  ${RED}✗ DATABASE_URL در .env تنظیم نشده است${NC}"
        ENV_ISSUES=$((ENV_ISSUES+1))
    fi
    
    if [ $ENV_ISSUES -gt 0 ]; then
        echo -e "  ${YELLOW}⚠ $ENV_ISSUES مشکل در فایل .env یافت شد. لطفاً آن را بررسی کنید.${NC}"
    fi
else
    echo -e "  ${RED}✗ فایل .env یافت نشد${NC}"
    echo -e "  ${YELLOW}ایجاد فایل .env از نمونه؟ (y/n)${NC}"
    read -p " " create_env
    
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "  ${GREEN}✓ فایل .env از نمونه ایجاد شد. لطفاً آن را ویرایش کنید.${NC}"
        else
            echo -e "  ${RED}✗ فایل .env.example نیز یافت نشد. نمی‌توان .env را ایجاد کرد.${NC}"
        fi
    fi
fi

# بررسی اتصال به دیتابیس
echo ""
echo -e "${BLUE}[4/7] بررسی اتصال به دیتابیس${NC}"

if [ -f ".env" ] && grep -q "DATABASE_URL" .env; then
    # استخراج اطلاعات اتصال از DATABASE_URL
    DB_URL=$(grep "DATABASE_URL" .env | cut -d '=' -f2-)
    
    echo -e "  بررسی اتصال به دیتابیس..."
    
    # آزمایش اتصال با کد پایتون
    if python3 -c "
import os, sqlalchemy
from sqlalchemy import create_engine
try:
    os.environ['DATABASE_URL'] = '$DB_URL'
    engine = create_engine(os.environ['DATABASE_URL'])
    connection = engine.connect()
    connection.close()
    print('Connected to database successfully')
    exit(0)
except Exception as e:
    print(f'Error connecting to database: {e}')
    exit(1)
" 2>/dev/null; then
        echo -e "  ${GREEN}✓ اتصال به دیتابیس موفقیت‌آمیز بود${NC}"
    else
        echo -e "  ${RED}✗ خطا در اتصال به دیتابیس${NC}"
        echo -e "  ${YELLOW}⚠ مطمئن شوید که DATABASE_URL صحیح است و سرویس PostgreSQL در حال اجراست.${NC}"
    fi
else
    echo -e "  ${RED}✗ DATABASE_URL یافت نشد یا فایل .env وجود ندارد${NC}"
fi

# بررسی وضعیت ربات تلگرام
echo ""
echo -e "${BLUE}[5/7] بررسی وضعیت ربات تلگرام${NC}"

if [ -f ".env" ] && grep -q "TELEGRAM_BOT_TOKEN" .env; then
    BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" .env | cut -d '=' -f2-)
    
    echo -e "  بررسی ارتباط با API تلگرام..."
    
    # بررسی اتصال به API تلگرام
    if curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe" | grep -q "\"ok\":true"; then
        echo -e "  ${GREEN}✓ ارتباط با API تلگرام برقرار است${NC}"
        
        # دریافت نام ربات
        BOT_USERNAME=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe" | grep -o '"username":"[^"]*"' | cut -d '"' -f 4)
        echo -e "  ${GREEN}✓ نام ربات: @$BOT_USERNAME${NC}"
        
        # بررسی وضعیت وب‌هوک
        WEBHOOK_INFO=$(curl -s "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo")
        
        if echo "$WEBHOOK_INFO" | grep -q "\"url\":\"\""; then
            echo -e "  ${YELLOW}⚠ وب‌هوک تنظیم نشده است. ربات در حالت polling کار خواهد کرد.${NC}"
        else
            WEBHOOK_URL=$(echo "$WEBHOOK_INFO" | grep -o '"url":"[^"]*"' | cut -d '"' -f 4)
            echo -e "  ${GREEN}✓ وب‌هوک تنظیم شده است: $WEBHOOK_URL${NC}"
            
            # بررسی خطاهای وب‌هوک
            if echo "$WEBHOOK_INFO" | grep -q "\"last_error_date\":[^0]"; then
                LAST_ERROR=$(echo "$WEBHOOK_INFO" | grep -o '"last_error_message":"[^"]*"' | cut -d '"' -f 4)
                echo -e "  ${RED}✗ خطای وب‌هوک: $LAST_ERROR${NC}"
            fi
        fi
    else
        echo -e "  ${RED}✗ خطا در ارتباط با API تلگرام${NC}"
        echo -e "  ${YELLOW}⚠ مطمئن شوید که TELEGRAM_BOT_TOKEN صحیح است.${NC}"
    fi
else
    echo -e "  ${RED}✗ TELEGRAM_BOT_TOKEN یافت نشد یا فایل .env وجود ندارد${NC}"
fi

# بررسی مجوزهای فایل‌ها
echo ""
echo -e "${BLUE}[6/7] بررسی مجوزهای فایل‌ها${NC}"

# بررسی مجوزهای اجرایی اسکریپت‌ها
SCRIPTS=("install.sh" "setup_https.sh" "polling_mode.sh" "one_click_install_en.sh" "set_webhook.py" "troubleshoot.sh")
SCRIPT_ISSUES=0

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "  ${GREEN}✓ $script دارای مجوز اجرایی است${NC}"
        else
            echo -e "  ${RED}✗ $script فاقد مجوز اجرایی است${NC}"
            SCRIPT_ISSUES=$((SCRIPT_ISSUES+1))
        fi
    else
        echo -e "  ${YELLOW}⚠ $script یافت نشد${NC}"
    fi
done

if [ $SCRIPT_ISSUES -gt 0 ]; then
    echo -e "  ${YELLOW}مجوزهای اجرایی را برای همه اسکریپت‌ها تنظیم می‌کنید؟ (y/n)${NC}"
    read -p " " fix_permissions
    
    if [ "$fix_permissions" = "y" ] || [ "$fix_permissions" = "Y" ]; then
        for script in "${SCRIPTS[@]}"; do
            if [ -f "$script" ] && [ ! -x "$script" ]; then
                chmod +x "$script"
                echo -e "  ${GREEN}✓ مجوز اجرایی برای $script تنظیم شد${NC}"
            fi
        done
    fi
fi

# بررسی فضای دیسک
echo ""
echo -e "${BLUE}[7/7] بررسی فضای دیسک${NC}"

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}')
DISK_AVAIL=$(df -h . | awk 'NR==2 {print $4}')

echo -e "  فضای استفاده شده: $DISK_USAGE"
echo -e "  فضای در دسترس: $DISK_AVAIL"

DISK_USAGE_NUM=${DISK_USAGE%\%}
if [ "$DISK_USAGE_NUM" -gt 90 ]; then
    echo -e "  ${RED}⚠ فضای دیسک بسیار کم است! لطفاً فایل‌های اضافی را پاک کنید.${NC}"
elif [ "$DISK_USAGE_NUM" -gt 80 ]; then
    echo -e "  ${YELLOW}⚠ فضای دیسک در حال اتمام است.${NC}"
else
    echo -e "  ${GREEN}✓ فضای دیسک کافی است${NC}"
fi

# بررسی لاگ‌ها
echo ""
echo -e "${BLUE}[بررسی اضافی] بررسی فایل‌های لاگ${NC}"

if [ -d "logs" ]; then
    LOG_SIZE=$(du -sh logs | awk '{print $1}')
    echo -e "  اندازه دایرکتوری logs: $LOG_SIZE"
    
    # نمایش خطاهای اخیر
    if [ -f "logs/errors.log" ]; then
        ERROR_COUNT=$(grep -c "ERROR" logs/errors.log)
        echo -e "  تعداد خطاهای ثبت شده: $ERROR_COUNT"
        
        if [ $ERROR_COUNT -gt 0 ]; then
            echo -e "  ${YELLOW}5 خطای اخیر:${NC}"
            grep "ERROR" logs/errors.log | tail -5
        fi
    fi
else
    echo -e "  ${YELLOW}⚠ دایرکتوری logs یافت نشد${NC}"
    mkdir -p logs
    echo -e "  ${GREEN}✓ دایرکتوری logs ایجاد شد${NC}"
fi

# نمایش خلاصه و پیشنهادات
echo ""
echo -e "${BLUE}=== خلاصه عیب‌یابی ===${NC}"

TOTAL_ISSUES=$((ENV_ISSUES + SCRIPT_ISSUES))
if [ $TOTAL_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ هیچ مشکل جدی یافت نشد. سیستم به نظر آماده کار است.${NC}"
else
    echo -e "${YELLOW}⚠ $TOTAL_ISSUES مشکل یافت شد که باید برطرف شود.${NC}"
fi

echo ""
echo -e "${BLUE}پیشنهادات:${NC}"
if [ $ENV_ISSUES -gt 0 ]; then
    echo -e "- فایل .env را بررسی و اطمینان حاصل کنید که تمام متغیرهای لازم تنظیم شده‌اند."
fi

if [ $SCRIPT_ISSUES -gt 0 ]; then
    echo -e "- مجوزهای اجرایی را برای اسکریپت‌ها تنظیم کنید (دستور: chmod +x *.sh)"
fi

if [ ! -f ".env" ] || ! grep -q "DATABASE_URL" .env; then
    echo -e "- اتصال به دیتابیس را تنظیم کنید."
fi

if [ ! -f ".env" ] || ! grep -q "TELEGRAM_BOT_TOKEN" .env; then
    echo -e "- توکن ربات تلگرام را در .env تنظیم کنید."
fi

echo ""
echo -e "${GREEN}عیب‌یابی کامل شد.${NC}"
echo -e "${BLUE}برای کمک بیشتر به مستندات پروژه مراجعه کنید یا از طریق تلگرام با پشتیبانی تماس بگیرید.${NC}"