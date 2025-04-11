from app import app  # noqa: F401

# Ensure app can be imported by Gunicorn
# این بخش برای اطمینان از اجرای درست ربات با Gunicorn اضافه شده است

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
