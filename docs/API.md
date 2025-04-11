# مستندات API ربات تلگرام پرمیوم

این سند، API رسمی سیستم مدیریت اشتراک تلگرام پرمیوم را مستند می‌کند که امکان ادغام با سیستم‌های خارجی را فراهم می‌کند.

## نقطه پایانی API

تمام درخواست‌های API باید به آدرس زیر ارسال شوند:

```
https://[your-domain]/api/[endpoint]
```

## احراز هویت

برای دسترسی به API، باید کلید API معتبر در هدر درخواست قرار دهید:

```
X-API-KEY: your_api_key
```

این کلید را می‌توانید از پنل مدیریت در بخش API ایجاد کنید.

## نقاط پایانی موجود

### ایجاد سفارش جدید

**نقطه پایانی:** `POST /api/orders/create`

**درخواست:**

```json
{
  "telegram_username": "username",
  "plan_id": "premium_monthly"
}
```

**پاسخ موفق:**

```json
{
  "success": true,
  "order_id": "12345",
  "message": "سفارش با موفقیت ایجاد شد و منتظر تأیید است."
}
```

**پاسخ خطا:**

```json
{
  "success": false,
  "error": "کد خطا",
  "message": "توضیحات خطا"
}
```

### دریافت وضعیت سفارش

**نقطه پایانی:** `GET /api/orders/status/{order_id}`

**پاسخ موفق:**

```json
{
  "success": true,
  "order_id": "12345",
  "status": "PENDING",
  "created_at": "2025-04-10T12:00:00Z",
  "telegram_username": "username",
  "plan_id": "premium_monthly",
  "amount": 10.99
}
```

### لیست سفارشات

**نقطه پایانی:** `GET /api/orders/list`

**پارامترهای اختیاری Query:**
- `status`: فیلتر بر اساس وضعیت (مثال: PENDING, APPROVED)
- `telegram_username`: فیلتر بر اساس نام کاربری تلگرام
- `page`: شماره صفحه (پیش‌فرض: 1)
- `limit`: تعداد نتایج در هر صفحه (پیش‌فرض: 10)

**پاسخ موفق:**

```json
{
  "success": true,
  "total_count": 150,
  "page": 1,
  "limit": 10,
  "orders": [
    {
      "order_id": "12345",
      "status": "APPROVED",
      "created_at": "2025-04-10T12:00:00Z",
      "telegram_username": "username1",
      "plan_id": "premium_monthly",
      "amount": 10.99
    },
    ...
  ]
}
```

## کدهای وضعیت HTTP

API از کدهای وضعیت HTTP استاندارد استفاده می‌کند:

- `200 OK`: درخواست با موفقیت انجام شد
- `400 Bad Request`: درخواست نامعتبر است
- `401 Unauthorized`: کلید API نامعتبر یا منقضی شده است
- `404 Not Found`: منبع درخواستی یافت نشد
- `429 Too Many Requests`: تعداد درخواست‌ها بیش از حد مجاز است
- `500 Internal Server Error`: خطای داخلی سرور

## محدودیت نرخ درخواست

برای جلوگیری از سوء استفاده، API دارای محدودیت است:

- حداکثر 100 درخواست در دقیقه برای هر کلید API

## مثال کد (Python)

```python
import requests

API_URL = "https://your-domain.com/api"
API_KEY = "your_api_key"

def create_order(telegram_username, plan_id):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "telegram_username": telegram_username,
        "plan_id": plan_id
    }
    response = requests.post(f"{API_URL}/orders/create", json=data, headers=headers)
    return response.json()

def get_order_status(order_id):
    headers = {
        "X-API-KEY": API_KEY
    }
    response = requests.get(f"{API_URL}/orders/status/{order_id}", headers=headers)
    return response.json()

# مثال استفاده
result = create_order("user123", "premium_monthly")
print(result)
```

## پلن‌های موجود

پلن‌های موجود که می‌توانید در API استفاده کنید:

| شناسه پلن | نام | توضیحات |
|------------|------|-------------|
| premium_monthly | اشتراک ماهانه | اشتراک پرمیوم تلگرام به مدت یک ماه |
| premium_yearly | اشتراک سالانه | اشتراک پرمیوم تلگرام به مدت یک سال |
| premium_6month | اشتراک شش ماهه | اشتراک پرمیوم تلگرام به مدت شش ماه |

## گزارش مشکلات

اگر با مشکلی در استفاده از API مواجه شدید، لطفاً از طریق ایمیل پشتیبانی با ما در تماس باشید.