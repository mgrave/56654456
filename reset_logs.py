
"""
اسکریپت برای پاک کردن لاگ‌ها و ایجاد مجدد پوشه لاگ
"""

import os
import shutil
from datetime import datetime

def reset_logs():
    """پاک کردن و بازسازی پوشه لاگ"""
    log_dir = "logs"
    
    # حذف پوشه لاگ اگر وجود دارد
    if os.path.exists(log_dir):
        print(f"در حال حذف پوشه لاگ موجود: {log_dir}")
        try:
            shutil.rmtree(log_dir)
            print("✅ پوشه لاگ با موفقیت حذف شد")
        except Exception as e:
            print(f"❌ خطا در حذف پوشه لاگ: {str(e)}")
            # تلاش برای حذف فایل به فایل
            try:
                for filename in os.listdir(log_dir):
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"حذف فایل: {file_path}")
                print("✅ فایل‌های لاگ با موفقیت حذف شدند")
            except Exception as e2:
                print(f"❌ خطا در حذف فایل‌های لاگ: {str(e2)}")
    
    # ایجاد پوشه لاگ جدید
    try:
        os.makedirs(log_dir)
        print(f"✅ پوشه لاگ جدید ایجاد شد: {log_dir}")
        
        # تنظیم مجوزهای پوشه
        os.chmod(log_dir, 0o755)
        print(f"✅ مجوزهای پوشه لاگ به 755 تنظیم شد")
        
        # ایجاد فایل README در پوشه لاگ
        readme_path = os.path.join(log_dir, "README.txt")
        with open(readme_path, "w") as f:
            f.write(f"این پوشه حاوی فایل‌های لاگ سیستم است.\n")
            f.write(f"ایجاد شده در: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        print(f"✅ فایل README ایجاد شد: {readme_path}")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد پوشه لاگ جدید: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== اسکریپت پاک‌سازی لاگ‌ها ===")
    success = reset_logs()
    
    if success:
        print("\n✅ عملیات پاک‌سازی لاگ‌ها با موفقیت انجام شد.")
        print("اکنون می‌توانید برنامه را اجرا کنید تا فایل‌های لاگ جدید ایجاد شوند.")
    else:
        print("\n❌ عملیات پاک‌سازی لاگ‌ها با مشکل مواجه شد.")
        print("لطفاً دستی پوشه logs را بررسی کنید.")
