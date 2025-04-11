# راهنمای ادغام پرداخت ارز دیجیتال

این راهنما نحوه تنظیم و یکپارچه‌سازی NowPayments API با سیستم مدیریت اشتراک تلگرام پرمیوم را توضیح می‌دهد.

## NowPayments چیست؟

[NowPayments](https://nowpayments.io/) یک سرویس پرداخت ارز دیجیتال است که به شما امکان پذیرش بیش از 150 ارز دیجیتال مختلف را می‌دهد. این سیستم به راحتی با اپلیکیشن‌ها ادغام می‌شود و مدیریت تراکنش‌ها را ساده می‌کند.

## پیش‌نیازها

1. یک حساب NowPayments (ثبت‌نام در [nowpayments.io](https://nowpayments.io))
2. کلید API از پنل حساب کاربری NowPayments 
3. ارز دیجیتال برای دریافت پرداخت (به صورت پیش‌فرض TRX)

## تنظیم NowPayments API

### 1. ثبت‌نام و ایجاد کلید API

1. در [nowpayments.io](https://nowpayments.io) ثبت‌نام کنید
2. پروسه تأیید هویت (KYC) را تکمیل کنید
3. به بخش "Store Settings" بروید
4. یک کلید API جدید ایجاد کنید
5. آدرس کیف پول‌های خود را برای دریافت پرداخت‌ها تنظیم کنید

### 2. تنظیم IPN (Instant Payment Notification)

برای دریافت اعلان‌های پرداخت به صورت خودکار:

1. در پنل NowPayments به بخش "Store Settings" بروید
2. در قسمت IPN، آدرس IPN زیر را وارد کنید:
   ```
   https://your-domain.com/api/ipn/nowpayments
   ```
3. کلید IPN Secret را در فایل `.env` خود ذخیره کنید

### 3. تنظیم متغیرهای محیطی

فایل `.env` را با اطلاعات NowPayments خود به‌روزرسانی کنید:

```
NOWPAYMENTS_API_KEY=your_api_key_here
NOWPAYMENTS_IPN_SECRET=your_ipn_secret_here
NOWPAYMENTS_DEFAULT_CURRENCY=TRX
```

## ساختار کد یکپارچه‌سازی

اصلی‌ترین بخش ادغام NowPayments در فایل `nowpayments.py` قرار دارد. این فایل کلاس `NowPayments` را پیاده‌سازی می‌کند که API انتزاعی برای تعامل با سرویس NowPayments فراهم می‌کند.

### توابع اصلی کلاس NowPayments

1. **ایجاد پرداخت جدید**: `create_payment(price, currency, pay_currency, order_id, order_description)`
2. **بررسی وضعیت پرداخت**: `get_payment_status(payment_id)`
3. **ایجاد فاکتور پرداخت**: `create_invoice(price, currency, order_id, order_description, success_url, cancel_url)`
4. **تأیید اعتبار IPN**: `verify_ipn_callback(ipn_data)`

## فرآیند پرداخت

### 1. ایجاد سفارش 

وقتی کاربر یک پلن را انتخاب می‌کند، سیستم یک سفارش ایجاد می‌کند:

```python
# ایجاد سفارش در دیتابیس
order = Order(
    order_id=generate_order_id(),
    user_id=user.id,
    plan_id=plan_id,
    plan_name=plan_name,
    amount=plan_price,
    status="PENDING",
    telegram_username=telegram_username
)
db_session.add(order)
db_session.commit()
```

### 2. ایجاد لینک پرداخت

برای ایجاد درخواست پرداخت از NowPayments:

```python
nowpayments = NowPayments(api_key=os.environ.get("NOWPAYMENTS_API_KEY"))
payment = nowpayments.create_payment(
    price=order.amount,
    currency="USD",
    pay_currency="TRX",
    order_id=order.order_id,
    order_description=f"تلگرام پرمیوم - {order.plan_name}"
)

# ذخیره اطلاعات پرداخت در دیتابیس
if payment and "id" in payment:
    order.payment_id = payment["id"]
    order.payment_url = payment["invoice_url"]
    db_session.commit()
```

### 3. دریافت اعلان‌های پرداخت (IPN)

زمانی که پرداخت انجام می‌شود، NowPayments یک IPN به آدرس تنظیم شده ارسال می‌کند:

```python
@app.route("/api/ipn/nowpayments", methods=["POST"])
def nowpayments_ipn_webhook():
    # دریافت داده‌های IPN
    ipn_data = request.json
    
    # تأیید اعتبار IPN
    nowpayments = NowPayments(api_key=os.environ.get("NOWPAYMENTS_API_KEY"))
    if not nowpayments.verify_ipn_callback(ipn_data):
        return jsonify({"status": "error", "message": "Invalid IPN signature"}), 400
    
    # پردازش داده‌های IPN
    payment_id = ipn_data.get("payment_id")
    payment_status = ipn_data.get("payment_status")
    
    # به‌روزرسانی وضعیت سفارش در دیتابیس
    if payment_status == "confirmed" or payment_status == "complete":
        order = Order.query.filter_by(payment_id=payment_id).first()
        if order:
            order.status = "PAID"
            # ایجاد تراکنش جدید
            transaction = PaymentTransaction(
                payment_id=payment_id,
                order_id=order.id,
                amount=ipn_data.get("price_amount"),
                currency=ipn_data.get("price_currency"),
                pay_currency=ipn_data.get("pay_currency"),
                status="COMPLETED",
                ipn_data=ipn_data,
                completed_at=datetime.utcnow()
            )
            db_session.add(transaction)
            db_session.commit()
            
            # اطلاع‌رسانی به ادمین و کاربر
            notify_admins_about_payment(order, transaction)
            notify_customer_about_payment(order, transaction)
    
    return jsonify({"status": "success"}), 200
```

## تست یکپارچه‌سازی پرداخت

برای تست یکپارچه‌سازی پرداخت:

1. **حالت Sandbox**: NowPayments حالت Sandbox ارائه نمی‌دهد، اما می‌توانید با مبالغ کوچک تست کنید.

2. **تست با مبالغ کوچک**: برای تست از مبالغ بسیار کوچک (مثلاً 0.1 TRX) استفاده کنید.

3. **لاگ کردن اطلاعات**: برای عیب‌یابی، تمام درخواست‌ها و پاسخ‌های API را لاگ کنید:
   ```python
   payment_logger.debug(f"NowPayments API Request: {data}")
   payment_logger.debug(f"NowPayments API Response: {response.text}")
   ```

## عیب‌یابی مشکلات رایج

### 1. پرداخت انجام شده اما سیستم آن را تشخیص نداده است

- بررسی کنید که آدرس IPN به درستی تنظیم شده است
- بررسی کنید که سرور شما از اینترنت قابل دسترسی است
- لاگ‌های IPN را بررسی کنید

### 2. خطای "Invalid API Key"

- مطمئن شوید که کلید API به درستی در فایل `.env` ذخیره شده است
- کلید API را در پنل NowPayments تجدید کنید

### 3. مشکلات تطبیق Payment ID

- مطمئن شوید که `payment_id` به درستی در جداول Order و PaymentTransaction ذخیره می‌شود
- از تطابق `payment_id` در IPN و دیتابیس اطمینان حاصل کنید

## ارزهای دیجیتال پشتیبانی شده

به صورت پیش‌فرض، سیستم از ارز TRX استفاده می‌کند، اما می‌توانید از ارزهای دیگر نیز استفاده کنید:

- BTC (Bitcoin)
- ETH (Ethereum)
- LTC (Litecoin)
- DOGE (Dogecoin)
- و بیش از 150 ارز دیگر

برای تغییر ارز پیش‌فرض:

1. متغیر `NOWPAYMENTS_DEFAULT_CURRENCY` را در فایل `.env` به‌روزرسانی کنید
2. یا پارامتر `pay_currency` را در تابع `create_payment` تغییر دهید

## منابع و مستندات بیشتر

- [مستندات رسمی NowPayments API](https://documenter.getpostman.com/view/7907941/S1a32n38)
- [راهنمای یکپارچه‌سازی NowPayments](https://nowpayments.io/help/what-is-the-best-way-to-integrate-with-your-platform)