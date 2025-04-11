#!/bin/bash
# اسکریپت ایجاد مخزن گیت‌هاب جدید و آپلود کدها
# نویسنده: سیستم هوش مصنوعی
# تاریخ: 10 آوریل 2025

# رنگ‌های متن
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# نمایش راهنمای استفاده
show_help() {
    echo -e "${BLUE}=== ایجاد مخزن گیت‌هاب جدید و آپلود کدها ===${NC}"
    echo ""
    echo -e "این اسکریپت به شما کمک می‌کند تا یک مخزن گیت‌هاب جدید ایجاد کرده و"
    echo -e "کدهای پروژه را در آن آپلود کنید."
    echo ""
    echo -e "${YELLOW}برای استفاده، اطلاعات زیر را فراهم کنید:${NC}"
    echo -e "1. توکن شخصی گیت‌هاب (Personal Access Token) با دسترسی کامل به مخازن"
    echo -e "2. نام کاربری گیت‌هاب"
    echo -e "3. نام مخزن جدید"
    echo -e "4. توضیحات مخزن (اختیاری)"
    echo ""
    echo -e "${RED}نکته:${NC} برای ایجاد توکن شخصی گیت‌هاب به آدرس زیر مراجعه کنید:"
    echo -e "https://github.com/settings/tokens"
    echo -e "توکن باید دسترسی ${YELLOW}repo${NC} را داشته باشد."
}

# نمایش راهنما
show_help

echo ""
echo -e "${YELLOW}آیا مایل به ادامه کار هستید؟ (y/n)${NC}"
read -p " " continue_answer

if [ "$continue_answer" != "y" ] && [ "$continue_answer" != "Y" ]; then
    echo -e "${RED}عملیات لغو شد.${NC}"
    exit 0
fi

# دریافت اطلاعات از کاربر
echo ""
read -p "توکن شخصی گیت‌هاب: " github_token
read -p "نام کاربری گیت‌هاب: " github_username
read -p "نام مخزن جدید (بدون فاصله، ترجیحاً با حروف انگلیسی): " github_repo
read -p "توضیحات مخزن (اختیاری): " github_description
read -p "مخزن خصوصی باشد؟ (y/n، پیش‌فرض: عمومی): " is_private

# تنظیم نوع مخزن
if [ "$is_private" = "y" ] || [ "$is_private" = "Y" ]; then
    private_flag="true"
else
    private_flag="false"
fi

# تأیید نهایی
echo ""
echo -e "${BLUE}اطلاعات مخزن جدید:${NC}"
echo -e "نام کاربری: ${YELLOW}$github_username${NC}"
echo -e "نام مخزن: ${YELLOW}$github_repo${NC}"
if [ -n "$github_description" ]; then
    echo -e "توضیحات: ${YELLOW}$github_description${NC}"
fi
if [ "$private_flag" = "true" ]; then
    echo -e "نوع مخزن: ${YELLOW}خصوصی${NC}"
else
    echo -e "نوع مخزن: ${YELLOW}عمومی${NC}"
fi

echo ""
echo -e "${YELLOW}آیا مطمئن هستید؟ (y/n)${NC}"
read -p " " final_confirm

if [ "$final_confirm" != "y" ] && [ "$final_confirm" != "Y" ]; then
    echo -e "${RED}عملیات لغو شد.${NC}"
    exit 0
fi

# شروع فرآیند
echo ""
echo -e "${BLUE}فرآیند ایجاد مخزن و آپلود آغاز شد...${NC}"

# گام 1: ایجاد مخزن گیت‌هاب جدید با API
echo -e "${YELLOW}گام 1:${NC} ایجاد مخزن گیت‌هاب جدید..."

# تنظیم توضیحات مخزن برای API
if [ -z "$github_description" ]; then
    github_description="Premium Telegram Bot - Automatic subscription management for Telegram Premium"
fi

# ساخت درخواست API
api_response=$(curl -s -X POST -H "Authorization: token $github_token" \
    -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/user/repos \
    -d "{\"name\":\"$github_repo\",\"description\":\"$github_description\",\"private\":$private_flag}")

# بررسی پاسخ API
if [[ "$api_response" == *"Bad credentials"* ]]; then
    echo -e "${RED}خطا: توکن گیت‌هاب نامعتبر است.${NC}"
    exit 1
elif [[ "$api_response" == *"Repository creation failed"* ]]; then
    echo -e "${RED}خطا: ایجاد مخزن با مشکل مواجه شد.${NC}"
    exit 1
elif [[ "$api_response" == *"name already exists on this account"* ]]; then
    echo -e "${RED}خطا: مخزنی با این نام از قبل وجود دارد.${NC}"
    read -p "آیا مایل به ادامه و آپلود به همان مخزن هستید؟ (y/n) " continue_existing
    if [ "$continue_existing" != "y" ] && [ "$continue_existing" != "Y" ]; then
        exit 1
    fi
    echo -e "${YELLOW}ادامه با مخزن موجود...${NC}"
else
    echo -e "${GREEN}مخزن گیت‌هاب جدید با موفقیت ایجاد شد.${NC}"
fi

# گام 2: ایجاد .gitignore مناسب
echo -e "${YELLOW}گام 2:${NC} ایجاد فایل .gitignore..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
.env

# Log files
logs/
*.log

# Database files
*.db
*.sqlite
*.sqlite3

# OS specific files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.idea/
.vscode/
*.swp
*.swo
EOF
echo -e "${GREEN}فایل .gitignore ایجاد شد.${NC}"

# گام 3: حذف مخزن گیت محلی در صورت وجود
echo -e "${YELLOW}گام 3:${NC} حذف مخزن گیت محلی در صورت وجود..."
if [ -d ".git" ]; then
    rm -rf .git
    echo -e "${GREEN}مخزن محلی قبلی حذف شد.${NC}"
else
    echo -e "${GREEN}مخزن محلی قبلی یافت نشد.${NC}"
fi

# گام 4: ایجاد README.md پایه
echo -e "${YELLOW}گام 4:${NC} ایجاد فایل README.md..."
cat > README.md << EOF
# $github_repo

$github_description

## خصوصیات

- مدیریت خودکار اشتراک تلگرام پرمیوم
- پرداخت با ارزهای دیجیتال
- پنل مدیریت ادمین
- API برای ادغام با سرویس‌های خارجی

## نصب

برای نصب این پروژه، دستورات زیر را اجرا کنید:

\`\`\`bash
git clone https://github.com/$github_username/$github_repo.git
cd $github_repo
bash install.sh
\`\`\`

## نصب یک خطی

برای نصب سریع با یک دستور:

\`\`\`bash
bash <(curl -s https://raw.githubusercontent.com/$github_username/$github_repo/main/one_click_install_en.sh)
\`\`\`

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.
EOF
echo -e "${GREEN}فایل README.md ایجاد شد.${NC}"

# گام 5: ایجاد مخزن گیت محلی
echo -e "${YELLOW}گام 5:${NC} ایجاد مخزن گیت محلی..."
git init
echo -e "${GREEN}مخزن گیت محلی ایجاد شد.${NC}"

# گام 6: اضافه کردن تمام فایل‌ها به مخزن
echo -e "${YELLOW}گام 6:${NC} اضافه کردن تمام فایل‌ها به مخزن..."
git add .
echo -e "${GREEN}تمام فایل‌ها به مخزن اضافه شدند.${NC}"

# گام 7: ثبت تغییرات
echo -e "${YELLOW}گام 7:${NC} ثبت تغییرات اولیه..."
git commit -m "Initial commit: Premium Telegram Bot project"
echo -e "${GREEN}تغییرات ثبت شدند.${NC}"

# گام 8: تنظیم remote
echo -e "${YELLOW}گام 8:${NC} تنظیم مخزن remote..."
git remote add origin https://${github_token}@github.com/${github_username}/${github_repo}.git
echo -e "${GREEN}مخزن remote تنظیم شد.${NC}"

# گام 9: آپلود کدها به شاخه main
echo -e "${YELLOW}گام 9:${NC} آپلود کدها به شاخه main..."
git push -u origin main
push_result=$?

if [ $push_result -eq 0 ]; then
    echo -e "${GREEN}آپلود کدها با موفقیت انجام شد!${NC}"
    echo -e "مخزن شما اکنون در آدرس زیر در دسترس است:"
    echo -e "${BLUE}https://github.com/${github_username}/${github_repo}${NC}"
else
    echo -e "${RED}خطا در آپلود کدها.${NC}"
    echo -e "لطفاً موارد زیر را بررسی کنید:"
    echo -e "  - دسترسی‌های توکن گیت‌هاب (نیاز به دسترسی repo کامل)"
    echo -e "  - اتصال اینترنت"
    echo -e "  - محدودیت‌های حساب گیت‌هاب"
fi

echo ""
echo -e "${BLUE}فرآیند ایجاد مخزن و آپلود کدها به پایان رسید.${NC}"