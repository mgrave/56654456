#!/bin/bash
# اسکریپت برای آپلود مجدد کد به گیتهاب
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
    echo -e "${BLUE}=== آپلود مجدد کد به گیتهاب ===${NC}"
    echo ""
    echo -e "این اسکریپت به شما کمک می‌کند تا کد خود را به صورت کامل به گیتهاب آپلود کنید."
    echo -e "برای استفاده، اطلاعات زیر را فراهم کنید:"
    echo ""
    echo -e "${YELLOW}1. توکن شخصی گیتهاب${NC} (Personal Access Token)"
    echo -e "${YELLOW}2. نام کاربری گیتهاب${NC}"
    echo -e "${YELLOW}3. نام مخزن${NC} (نام ریپازیتوری)"
    echo ""
    echo -e "${RED}توجه:${NC} اجرای این اسکریپت باعث حذف و بازنویسی کامل مخزن شما می‌شود!"
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
read -p "توکن شخصی گیتهاب: " github_token
read -p "نام کاربری گیتهاب: " github_username
read -p "نام مخزن (ریپازیتوری): " github_repo

# تأیید نهایی
echo ""
echo -e "${RED}هشدار:${NC} این فرآیند تمام محتوای موجود در مخزن '$github_username/$github_repo' را حذف و بازنویسی خواهد کرد."
echo -e "${YELLOW}آیا مطمئن هستید؟ (بنویسید: CONFIRM)${NC}"
read -p " " final_confirm

if [ "$final_confirm" != "CONFIRM" ]; then
    echo -e "${RED}عملیات لغو شد.${NC}"
    exit 0
fi

# شروع فرآیند
echo ""
echo -e "${BLUE}فرآیند آپلود آغاز شد...${NC}"

# گام 1: حذف مخزن گیت محلی در صورت وجود
echo -e "${YELLOW}گام 1:${NC} حذف مخزن گیت محلی در صورت وجود..."
if [ -d ".git" ]; then
    rm -rf .git
    echo -e "${GREEN}مخزن محلی حذف شد.${NC}"
else
    echo -e "${GREEN}مخزن محلی یافت نشد.${NC}"
fi

# گام 2: ایجاد مخزن گیت جدید
echo -e "${YELLOW}گام 2:${NC} ایجاد مخزن گیت جدید..."
git init
echo -e "${GREEN}مخزن گیت جدید ایجاد شد.${NC}"

# گام 3: اضافه کردن تمام فایل‌ها به مخزن
echo -e "${YELLOW}گام 3:${NC} اضافه کردن تمام فایل‌ها به مخزن..."
git add .
echo -e "${GREEN}تمام فایل‌ها اضافه شدند.${NC}"

# گام 4: ثبت تغییرات
echo -e "${YELLOW}گام 4:${NC} ثبت تغییرات..."
git commit -m "آپلود کامل کد - بازسازی مخزن"
echo -e "${GREEN}تغییرات ثبت شدند.${NC}"

# گام 5: تنظیم remote
echo -e "${YELLOW}گام 5:${NC} تنظیم ریموت..."
git remote add origin https://${github_token}@github.com/${github_username}/${github_repo}.git
echo -e "${GREEN}ریموت تنظیم شد.${NC}"

# گام 6: فشار دادن کد روی شاخه main با فورس
echo -e "${YELLOW}گام 6:${NC} فشار دادن کد به گیتهاب (force push)..."
git push -f origin main
push_result=$?

if [ $push_result -eq 0 ]; then
    echo -e "${GREEN}آپلود کامل شد!${NC}"
    echo -e "کد شما اکنون در ${BLUE}https://github.com/${github_username}/${github_repo}${NC} در دسترس است."
else
    echo -e "${RED}آپلود با خطا مواجه شد.${NC}"
    echo -e "لطفاً موارد زیر را بررسی کنید:"
    echo -e "  - صحت توکن شخصی گیتهاب"
    echo -e "  - دسترسی‌های توکن (نیاز به دسترسی repo کامل)"
    echo -e "  - وجود مخزن در گیتهاب"
    echo -e "  - اتصال اینترنت"
fi

echo ""
echo -e "${BLUE}پایان فرآیند.${NC}"