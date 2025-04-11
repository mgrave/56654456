import os
import logging
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

# تنظیم سیستم لاگینگ
import logging_config
loggers = logging_config.loggers
logger = loggers['app']

# میانه‌افزار ثبت درخواست‌های HTTP
class RequestLogger:
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        
    def before_request(self):
        logger.debug(f"درخواست دریافت شد: {request.method} {request.path} - IP: {request.remote_addr}")
        
    def after_request(self, response):
        logger.debug(f"پاسخ ارسال شد: {response.status_code} - مسیر: {request.path}")
        return response

# Initialize database
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# فعال‌سازی میانه‌افزار لاگینگ
request_logger = RequestLogger(app)
logger.info("میانه‌افزار لاگینگ Flask فعال شد")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///telegram_premium.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database with the app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models
import models
# Make each model available directly
User = models.User
Order = models.Order
PaymentTransaction = models.PaymentTransaction
AdminUser = models.AdminUser
BroadcastMessage = models.BroadcastMessage

# Set up SQLAlchemy session factory
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Create engine and session
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], pool_recycle=300, pool_pre_ping=True)
models.Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
db_session = Session()

# Import API clients
import config_manager
from nowpayments import NowPayments

@login_manager.user_loader
def load_user(user_id):
    return db_session.query(AdminUser).get(int(user_id))

# Create the database tables
with app.app_context():
    # Create all tables
    models.Base.metadata.create_all(engine)
    
    # Create a default admin user if none exists
    admin_user = db_session.query(AdminUser).filter_by(username="admin").first()
    if not admin_user:
        admin = AdminUser(
            username="admin",
            password_hash=generate_password_hash("admin"),  # Change this in production
            is_super_admin=True
        )
        db_session.add(admin)
        db_session.commit()
        logger.info("Default admin user created")

# Register API Blueprint
from api import api_bp
app.register_blueprint(api_bp)

# API Documentation Route
@app.route('/api/docs')
def api_docs():
    """Public API documentation page"""
    return render_template('api_docs.html')

# Import routes after db is defined
from nowpayments import NowPayments
import config_manager

# Initialize NowPayments API client
nowpayments_api = NowPayments(os.environ.get("NOWPAYMENTS_API_KEY", ""))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = db_session.query(AdminUser).filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    # Count orders by status
    pending_count = db_session.query(Order).filter(Order.status.in_(['PENDING', 'ADMIN_REVIEW', 'AWAITING_PAYMENT'])).count()
    completed_count = db_session.query(Order).filter(Order.status == 'APPROVED').count()
    cancelled_count = db_session.query(Order).filter(Order.status == 'REJECTED').count()
    
    # Recent orders
    recent_orders = db_session.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    
    # Count payments
    successful_payments = db_session.query(Order).filter(Order.status == 'APPROVED').count()
    
    return render_template('admin/dashboard.html', 
                           pending_count=pending_count,
                           completed_count=completed_count,
                           cancelled_count=cancelled_count,
                           recent_orders=recent_orders,
                           successful_payments=successful_payments)

@app.route('/admin/orders')
@login_required
def admin_orders():
    # Filter by status
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    query = db_session.query(Order)
    
    # Apply status filter if provided
    if status:
        query = query.filter(Order.status == status)
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Order.order_id.like(search_term),
                Order.telegram_username.like(search_term),
                Order.status.like(search_term),
                Order.plan_name.like(search_term)
            )
        )
    
    # Order by most recent first
    query = query.order_by(Order.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Manual pagination
    offset = (page - 1) * per_page
    orders = query.offset(offset).limit(per_page).all()
    
    # Create pagination data
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'items': orders
    }
    
    return render_template(
        'admin/orders.html', 
        orders=orders, 
        pagination=pagination,
        current_status=status,
        search_query=search
    )

@app.route('/admin/orders/<order_id>')
@login_required
def admin_order_detail(order_id):
    order = db_session.query(Order).filter_by(order_id=order_id).first()
    if not order:
        abort(404)
    payments = db_session.query(PaymentTransaction).filter_by(order_id=order.id).all()
    
    return render_template('admin/order_detail.html', order=order, payments=payments)

@app.route('/admin/orders/<order_id>/approve', methods=['POST'])
@login_required
def admin_approve_order(order_id):
    order = db_session.query(Order).filter_by(order_id=order_id).first()
    if not order:
        abort(404)
    
    # Get form data
    activation_link = request.form.get('activation_link', '')
    admin_notes = request.form.get('admin_notes', '')
    
    # Update order
    order.status = 'APPROVED'
    order.updated_at = datetime.utcnow()
    order.admin_notes = admin_notes
    
    # Set activation link if provided
    if activation_link:
        order.activation_link = activation_link
    
    # Save all changes
    db_session.commit()
    
    flash(f'Order {order_id} has been approved', 'success')
    
    # Trigger notification to user via Telegram bot (will be implemented in run_telegram_bot.py)
    # This is a placeholder and will be connected to the actual bot
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/orders/<order_id>/reject', methods=['POST'])
@login_required
def admin_reject_order(order_id):
    order = db_session.query(Order).filter_by(order_id=order_id).first()
    if not order:
        abort(404)
    
    # Update order status
    order.status = 'REJECTED'
    order.updated_at = datetime.utcnow()
    order.admin_notes = request.form.get('admin_notes', '')
    
    db_session.commit()
    
    flash(f'Order {order_id} has been rejected', 'danger')
    
    # Trigger notification to user via Telegram bot (will be implemented in run_telegram_bot.py)
    # This is a placeholder and will be connected to the actual bot
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/plans')
@login_required
def admin_plans():
    plans = config_manager.get_subscription_plans()
    return render_template('admin/plans.html', plans=plans)

@app.route('/admin/plans/update', methods=['POST'])
@login_required
def admin_update_plan():
    plan_id = request.form.get('plan_id')
    plan_name = request.form.get('plan_name')
    plan_description = request.form.get('plan_description')
    plan_price = float(request.form.get('plan_price', 0))
    
    logger.info(f"Updating plan: ID={plan_id}, Name={plan_name}, Price={plan_price}")
    
    try:
        # Make sure price is converted to float properly
        try:
            plan_price = float(plan_price)
        except ValueError:
            flash(f'قیمت وارد شده نامعتبر است: {plan_price}', 'danger')
            return redirect(url_for('admin_plans'))
            
        # Print debugging information
        logger.debug(f"Before update - Plan: {plan_id}, Price: {plan_price}, Type: {type(plan_price)}")
        
        success = config_manager.update_subscription_plan(plan_id, plan_name, plan_description, plan_price)
        if success:
            logger.info(f"Plan updated successfully: {plan_id} with price {plan_price}")
            flash(f'طرح {plan_name} با موفقیت بروزرسانی شد', 'success')
        else:
            logger.error(f"Failed to update plan: {plan_id}")
            flash(f'خطا در بروزرسانی طرح {plan_name}', 'danger')
    except Exception as e:
        logger.error(f"Error updating plan: {str(e)}")
        flash(f'خطا در بروزرسانی طرح: {str(e)}', 'danger')
    
    return redirect(url_for('admin_plans'))

@app.route('/webhook/payment/callback', methods=['POST'])
def payment_webhook():
    logger.debug(f"Received payment webhook: {request.json}")
    
    if not request.json:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    # Process the payment notification
    payment_data = request.json
    
    # Find the related payment transaction
    payment_id = payment_data.get('payment_id')
    if not payment_id:
        return jsonify({"status": "error", "message": "No payment_id provided"}), 400
        
    transaction = db_session.query(PaymentTransaction).filter_by(payment_id=payment_id).first()
    if not transaction:
        return jsonify({"status": "error", "message": "Payment not found"}), 404
    
    # Update transaction status
    transaction.status = payment_data.get('payment_status', 'UNKNOWN')
    transaction.ipn_data = payment_data
    transaction.updated_at = datetime.utcnow()
    
    if transaction.status == 'COMPLETED':
        transaction.completed_at = datetime.utcnow()
        
        # Update the related order
        order = db_session.query(Order).get(transaction.order_id)
        if order:
            order.status = 'PAYMENT_RECEIVED'
            order.updated_at = datetime.utcnow()
    
    db_session.commit()
    logger.info(f"Updated payment transaction {payment_id} to status {transaction.status}")
    
    return jsonify({"status": "success"})

# Admin routes for new admin panel sections
@app.route('/admin/admins')
@login_required
def admin_admins():
    # Get list of bot admins from config
    bot_admins = config_manager.get_bot_admins()
    # Get list of web admin users using the db_session
    web_admins = db_session.query(AdminUser).all()
    
    return render_template('admin/admins.html', bot_admins=bot_admins, web_admins=web_admins)

@app.route('/admin/admins/add_bot_admin', methods=['POST'])
@login_required
def admin_add_bot_admin():
    admin_id = request.form.get('admin_id')
    if admin_id:
        success = config_manager.add_bot_admin(admin_id)
        if success:
            flash(f'Bot admin {admin_id} has been added', 'success')
        else:
            flash(f'Bot admin {admin_id} already exists', 'warning')
    else:
        flash('Admin ID is required', 'danger')
    
    return redirect(url_for('admin_admins'))

@app.route('/admin/admins/remove_bot_admin/<admin_id>', methods=['POST'])
@login_required
def admin_remove_bot_admin(admin_id):
    if admin_id:
        success = config_manager.remove_bot_admin(admin_id)
        if success:
            flash(f'Bot admin {admin_id} has been removed', 'success')
        else:
            flash(f'Bot admin {admin_id} not found', 'danger')
    
    return redirect(url_for('admin_admins'))

@app.route('/admin/admins/add_web_admin', methods=['POST'])
@login_required
def admin_add_web_admin():
    username = request.form.get('username')
    password = request.form.get('password')
    is_super_admin = 'is_super_admin' in request.form
    
    if not username or not password:
        flash('Username and password are required', 'danger')
        return redirect(url_for('admin_admins'))
    
    existing_admin = db_session.query(AdminUser).filter_by(username=username).first()
    if existing_admin:
        flash(f'Admin user {username} already exists', 'warning')
        return redirect(url_for('admin_admins'))
    
    new_admin = AdminUser(
        username=username,
        password_hash=generate_password_hash(password),
        is_super_admin=is_super_admin
    )
    
    db_session.add(new_admin)
    db_session.commit()
    
    flash(f'Admin user {username} has been added', 'success')
    return redirect(url_for('admin_admins'))

@app.route('/admin/admins/remove_web_admin/<int:admin_id>', methods=['POST'])
@login_required
def admin_remove_web_admin(admin_id):
    # Make sure the current user is a super admin
    if not current_user.is_super_admin:
        flash('Only super admins can remove admin users', 'danger')
        return redirect(url_for('admin_admins'))
    
    # Don't allow deleting self
    if current_user.id == admin_id:
        flash('You cannot remove yourself', 'danger')
        return redirect(url_for('admin_admins'))
    
    admin = db_session.query(AdminUser).get(admin_id)
    if not admin:
        flash('Admin user not found', 'danger')
        return redirect(url_for('admin_admins'))
    
    db_session.delete(admin)
    db_session.commit()
    
    flash(f'Admin user {admin.username} has been removed', 'success')
    return redirect(url_for('admin_admins'))

@app.route('/admin/channels')
@login_required
def admin_channels():
    # Use the dedicated channel getter functions
    admin_channel = config_manager.get_admin_channel()
    public_channel = config_manager.get_public_channel()
    required_channel = config_manager.get_required_channel()
    notification_enabled = config_manager.get_config_value('notification_enabled', False)
    channel_subscription_required = config_manager.is_channel_subscription_required()
    
    return render_template('admin/channels.html', 
                           admin_channel=admin_channel, 
                           public_channel=public_channel,
                           required_channel=required_channel,
                           notification_enabled=notification_enabled,
                           channel_subscription_required=channel_subscription_required)

@app.route('/admin/channels/update', methods=['POST'])
@login_required
def admin_update_channels():
    admin_channel = request.form.get('admin_channel')
    public_channel = request.form.get('public_channel')
    required_channel = request.form.get('required_channel')
    notification_enabled = 'notification_enabled' in request.form
    channel_subscription_required = 'channel_subscription_required' in request.form
    
    # Save to config using the dedicated functions
    config_manager.set_admin_channel(admin_channel)
    config_manager.set_public_channel(public_channel)
    config_manager.set_required_channel(required_channel)
    config_manager.set_channel_subscription_required(channel_subscription_required)
    config_manager.set_config_value('notification_enabled', notification_enabled)
    
    flash('Channel settings have been updated successfully', 'success')
    return redirect(url_for('admin_channels'))

@app.route('/admin/webhooks')
@login_required
def admin_webhooks():
    # Check if webhook is set up
    telegram_webhook_url = request.host_url.rstrip('/') + url_for('telegram_webhook')
    payment_webhook_url = request.host_url.rstrip('/') + url_for('payment_webhook')
    
    # Get admin API key if exists
    api_key = current_user.api_key_hash
    
    # Generate Premium API URL for documentation
    premium_api_url = request.host_url.rstrip('/') + url_for('api.create_premium_order')
    
    return render_template('admin/webhooks.html', 
                           telegram_webhook_url=telegram_webhook_url,
                           payment_webhook_url=payment_webhook_url,
                           api_key=api_key,
                           premium_api_url=premium_api_url)

@app.route('/admin/webhooks/generate_api_key', methods=['POST'])
@login_required
def admin_generate_api_key():
    """Generate a new API key for the current admin user"""
    import uuid
    
    # Generate a new API key
    api_key = str(uuid.uuid4())
    
    # Update the current user's API key
    current_user.api_key_hash = api_key
    db.session.commit()
    
    flash('New API key has been generated. Keep it secure!', 'success')
    return redirect(url_for('admin_webhooks'))

@app.route('/admin/support')
@login_required
def admin_support():
    # Get current support contact
    support_contact = config_manager.get_support_contact()
    return render_template('admin/support.html', support_contact=support_contact)

@app.route('/admin/support/update', methods=['POST'])
@login_required
def admin_update_support():
    support_contact = request.form.get('support_contact')
    
    if support_contact:
        config_manager.set_support_contact(support_contact)
        flash('Support contact has been updated', 'success')
    else:
        flash('Support contact is required', 'danger')
    
    return redirect(url_for('admin_support'))

@app.route('/admin/broadcasts')
@login_required
def admin_broadcasts():
    # Get all broadcast messages ordered by most recent first
    messages = db_session.query(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).all()
    
    # Count total registered users
    total_users = db_session.query(User).count()
    
    return render_template('admin/broadcasts.html', 
                          messages=messages,
                          total_users=total_users)

# System Logs Routes
@app.route('/admin/logs')
@login_required
def admin_logs():
    """View system logs"""
    # Read last 50 lines from each log file by default
    logs = {
        'app': _get_log_tail('logs/app.log', 50),
        'telegram': _get_log_tail('logs/telegram.log', 50),
        'api': _get_log_tail('logs/api.log', 50),
        'payment': _get_log_tail('logs/payment.log', 50),
        'webhook': _get_log_tail('logs/webhook.log', 50)
    }
    
    return render_template('admin/logs.html', logs=logs)

@app.route('/admin/logs/fetch/<log_type>')
@login_required
def admin_fetch_log(log_type):
    """Fetch log content dynamically"""
    allowed_types = ['app', 'telegram', 'api', 'payment', 'webhook']
    
    if log_type not in allowed_types:
        return "Invalid log type", 400
    
    lines = request.args.get('lines', 50, type=int)
    log_path = f'logs/{log_type}.log'
    log_content = _get_log_tail(log_path, lines)
    
    return log_content

@app.route('/admin/logs/download/<log_type>')
@login_required
def admin_download_log(log_type):
    """Download a log file"""
    allowed_types = ['app', 'telegram', 'api', 'payment', 'webhook']
    
    if log_type not in allowed_types:
        flash('Invalid log type', 'danger')
        return redirect(url_for('admin_logs'))
    
    log_path = f'logs/{log_type}.log'
    
    try:
        return send_file(log_path, as_attachment=True)
    except:
        flash(f'Error downloading {log_type} log', 'danger')
        return redirect(url_for('admin_logs'))

@app.route('/admin/logs/clear', methods=['POST'])
@login_required
def admin_clear_log():
    """Clear a log file or all logs"""
    log_type = request.form.get('log_type')
    allowed_types = ['app', 'telegram', 'api', 'payment', 'webhook', 'all']
    
    if log_type not in allowed_types:
        flash('Invalid log type', 'danger')
        return redirect(url_for('admin_logs'))
    
    if log_type == 'all':
        # Clear all logs
        for log_file in ['app', 'telegram', 'api', 'payment', 'webhook']:
            _clear_log(f'logs/{log_file}.log')
        flash('All logs have been cleared', 'success')
    else:
        # Clear specific log
        _clear_log(f'logs/{log_type}.log')
        flash(f'{log_type.capitalize()} log has been cleared', 'success')
    
    return redirect(url_for('admin_logs'))

# Helper function to get the last n lines of a log file
def _get_log_tail(file_path, lines=50):
    """Get the last n lines from a file"""
    try:
        if not os.path.exists(file_path):
            # Create the file if it doesn't exist
            with open(file_path, 'w') as f:
                f.write('')
            return ''
            
        # Use the tail command to get the last n lines
        result = os.popen(f'tail -n {lines} {file_path}').read()
        return result
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {e}")
        return f"Error reading log: {str(e)}"

# Helper function to clear a log file
def _clear_log(file_path):
    """Clear the contents of a log file"""
    try:
        with open(file_path, 'w') as f:
            f.write('')
        return True
    except Exception as e:
        logger.error(f"Error clearing log file {file_path}: {e}")
        return False

@app.route('/admin/broadcasts/send', methods=['POST'])
@login_required
def admin_send_broadcast():
    message_text = request.form.get('message_text')
    
    if not message_text:
        flash('Message text is required', 'danger')
        return redirect(url_for('admin_broadcasts'))
    
    # Create a new broadcast message
    broadcast = BroadcastMessage(
        admin_id=current_user.id,
        message_text=message_text,
        status='PENDING'
    )
    
    db_session.add(broadcast)
    db_session.commit()
    
    try:
        # Import the function from run_telegram_bot.py to send the broadcast
        from run_telegram_bot import send_broadcast_message
        
        # Start sending the broadcast in a background thread
        flash(f'Broadcast message #{broadcast.id} has been queued for sending', 'success')
        
        # Start sending in background
        threading.Thread(
            target=send_broadcast_message,
            args=(broadcast.id,),
            daemon=True
        ).start()
    except Exception as e:
        logger.error(f"Error sending broadcast: {str(e)}")
        flash(f'Error initiating broadcast: {str(e)}', 'danger')
    
    return redirect(url_for('admin_broadcasts'))

@app.route('/admin/orders/<order_id>/process_manual', methods=['POST'])
@login_required
def admin_process_manual_order(order_id):
    """Process an order manually after credit has been added to supplier account"""
    try:
        order = db_session.query(Order).filter_by(order_id=order_id).first()
        if not order:
            abort(404)
        
        # Ensure order is in the right state
        if order.status != 'AWAITING_CREDIT':
            flash(f'Order cannot be processed: current status is {order.status}', 'danger')
            return redirect(url_for('admin_order_detail', order_id=order_id))
            
        # Check if admin confirmed credit
        credit_confirmed = 'credit_confirmed' in request.form
        if not credit_confirmed:
            flash('You must confirm that credit has been added to supplier account', 'danger')
            return redirect(url_for('admin_order_detail', order_id=order_id))
            
        # Update the order status
        order.status = 'SUPPLIER_PROCESSING'
        order.updated_at = datetime.utcnow()
        order.admin_notes = (order.admin_notes or '') + "\n" + f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Order sent to supplier for processing."
        db_session.commit()
        
        # Here you would make the actual API call to your supplier
        # This is where you'd integrate with the supplier's API
        
        flash(f'Order {order_id} has been sent to supplier for processing', 'success')
        return redirect(url_for('admin_order_detail', order_id=order_id))
    except Exception as e:
        logger.error(f"Error processing manual order: {str(e)}")
        logger.exception(e)
        flash(f'Error processing order: {str(e)}', 'danger')
        return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/orders/<order_id>/confirm_supplier', methods=['POST'])
@login_required
def admin_confirm_supplier_complete(order_id):
    """Confirm that the supplier has completed the order"""
    try:
        order = db_session.query(Order).filter_by(order_id=order_id).first()
        if not order:
            abort(404)
        
        # Ensure order is in the right state
        if order.status != 'SUPPLIER_PROCESSING':
            flash(f'Order cannot be confirmed: current status is {order.status}', 'danger')
            return redirect(url_for('admin_order_detail', order_id=order_id))
            
        # Get activation link
        activation_link = request.form.get('activation_link', '')
        if not activation_link:
            flash('Activation link is required', 'danger')
            return redirect(url_for('admin_order_detail', order_id=order_id))
        
        # Update order status
        order.status = 'APPROVED'
        order.updated_at = datetime.utcnow()
        order.activation_link = activation_link
        order.admin_notes = (order.admin_notes or '') + "\n" + f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Order confirmed as completed by supplier."
        db_session.commit()
        
        # Send notification to customer via Telegram
        try:
            from run_telegram_bot import notify_customer_about_approval
            notify_customer_about_approval(order)
        except Exception as notify_err:
            logger.error(f"Error notifying customer: {str(notify_err)}")
            
        flash(f'Order {order_id} has been marked as completed and customer has been notified', 'success')
        return redirect(url_for('admin_order_detail', order_id=order_id))
    except Exception as e:
        logger.error(f"Error confirming supplier completion: {str(e)}")
        logger.exception(e)
        flash(f'Error confirming completion: {str(e)}', 'danger')
        return redirect(url_for('admin_order_detail', order_id=order_id))











@app.route('/admin/bot_settings')
@login_required
def admin_bot_settings():
    # Get current bot token and other settings
    bot_token = config_manager.get_config_value('bot_token', '')
    nowpayments_api_key = config_manager.get_config_value('nowpayments_api_key', '')
    bot_enabled = config_manager.get_config_value('bot_enabled', False)
    
    # Get supplier credit status from config, default to False if not set
    has_sufficient_credit = config_manager.get_config_value('has_sufficient_credit', False)
    
    return render_template('admin/bot_settings.html', 
                           bot_token=bot_token, 
                           nowpayments_api_key=nowpayments_api_key,
                           bot_enabled=bot_enabled,
                           has_sufficient_credit=has_sufficient_credit)

@app.route('/admin/bot_settings/update', methods=['POST'])
@login_required
def admin_update_bot_settings():
    bot_token = request.form.get('bot_token', '')
    nowpayments_api_key = request.form.get('nowpayments_api_key', '')
    bot_enabled = 'bot_enabled' in request.form
    
    # Save settings to config
    config_manager.set_config_value('bot_token', bot_token)
    config_manager.set_config_value('nowpayments_api_key', nowpayments_api_key)
    config_manager.set_config_value('bot_enabled', bot_enabled)
    
    flash('Bot settings have been updated', 'success')
    return redirect(url_for('admin_bot_settings'))

@app.route('/admin/bot_settings/start', methods=['POST'])
@login_required
def admin_start_bot():
    # Logic to start the bot
    try:
        # Import the required function
        import subprocess
        import sys
        
        # Set bot as enabled in config
        config_manager.set_config_value('bot_enabled', True)
        app.logger.info("Bot enabled in config")
        
        # Start the bot in a separate process
        # In this implementation, we're starting it in the background
        bot_token = config_manager.get_config_value('bot_token')
        if not bot_token:
            flash('Bot token is required to start the bot', 'danger')
            return redirect(url_for('admin_bot_settings'))
        
        # Check if we're in a subprocess already to avoid nested subprocesses
        is_subprocess = os.environ.get('BOT_SUBPROCESS') == '1'
        if not is_subprocess:
            app.logger.info("Starting bot in a separate process")
            env = os.environ.copy()
            env['BOT_SUBPROCESS'] = '1'
            
            # Run the bot script as a separate process
            subprocess.Popen([sys.executable, 'start_bot.py'], 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            env=env)
            
            flash('Bot has been started in background', 'success')
        else:
            app.logger.warning("Already in a subprocess, not starting another one")
            flash('Bot process already running', 'warning')
    except Exception as e:
        app.logger.error(f"Error starting bot: {str(e)}")
        app.logger.exception(e)
        flash(f'Failed to start bot: {str(e)}', 'danger')
    
    return redirect(url_for('admin_bot_settings'))

@app.route('/admin/bot_settings/stop', methods=['POST'])
@login_required
def admin_stop_bot():
    # Logic to stop the bot
    try:
        # Set bot as disabled in config
        config_manager.set_config_value('bot_enabled', False)
        app.logger.info("Bot disabled in config")
        
        # In a real production environment, you would need a proper process management
        # solution (like supervisord) to control the bot process
        # For now, we'll just rely on the bot checking the enabled flag in config
        
        flash('Bot has been disabled. The process will terminate on its next check cycle.', 'success')
    except Exception as e:
        app.logger.error(f"Error stopping bot: {str(e)}")
        app.logger.exception(e)
        flash(f'Failed to stop bot: {str(e)}', 'danger')
    
    return redirect(url_for('admin_bot_settings'))

@app.route('/admin/bot_settings/set_webhook', methods=['POST'])
@login_required
def admin_set_webhook():
    # Logic to set webhook for the bot
    try:
        bot_token = config_manager.get_config_value('bot_token', '')
        if not bot_token:
            flash('Bot token is required to set webhook', 'danger')
            return redirect(url_for('admin_bot_settings'))
        
        webhook_url = request.host_url.rstrip('/') + url_for('telegram_webhook')
        
        # First delete any existing webhook to ensure clean setup
        import requests
        delete_response = requests.get(f'https://api.telegram.org/bot{bot_token}/deleteWebhook')
        if not (delete_response.status_code == 200 and delete_response.json().get('ok')):
            app.logger.warning(f"Failed to delete existing webhook: {delete_response.text}")
            
        # Set up a new webhook with improved parameters
        webhook_params = {
            'url': webhook_url,
            'max_connections': 40,  # Optimal for most bots
            'drop_pending_updates': True,  # Important to avoid duplicate messages
            'allowed_updates': ['message', 'callback_query']  # Only listen for what we need
        }
        response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/setWebhook',
            json=webhook_params
        )
        
        if response.status_code == 200 and response.json().get('ok'):
            flash('Webhook has been set successfully', 'success')
        else:
            flash(f'Failed to set webhook: {response.json().get("description", "Unknown error")}', 'danger')
    except Exception as e:
        flash(f'Failed to set webhook: {str(e)}', 'danger')
    
    return redirect(url_for('admin_bot_settings'))

@app.route('/webhook/VSimsbot', methods=['POST'])
def telegram_webhook():
    """Endpoint for Telegram webhook, to be used with setWebhook"""
    try:
        # Import telegram bot logic
        from run_telegram_bot import process_webhook_update
        
        # Get the update data from Telegram
        update_json = request.get_json()
        if not update_json:
            app.logger.error("Empty update received in webhook")
            return jsonify({"status": "error", "message": "Empty update"})
        
        # Check if this update has already been processed (prevent duplicate processing)
        update_id = update_json.get('update_id')
        if update_id:
            # Use a simple in-memory cache to track recently processed updates
            # This can be enhanced with a more robust solution like Redis for production
            if not hasattr(app, 'processed_updates'):
                app.processed_updates = []
            
            if update_id in app.processed_updates:
                app.logger.info(f"Skipping already processed update_id: {update_id}")
                return jsonify({"status": "success", "message": "Already processed"})
            
            # Add this update to the processed list (keep it small to avoid memory issues)
            app.processed_updates.append(update_id)
            if len(app.processed_updates) > 100:  # Keep only the last 100 updates
                app.processed_updates = app.processed_updates[-100:]
        
        # Log webhook request for debugging
        app.logger.debug(f"Received Telegram update: {update_json}")
        
        # Process the update
        result = process_webhook_update(update_json)
        if result:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Failed to process update"})
    except Exception as e:
        app.logger.error(f"Error in webhook handler: {str(e)}")
        app.logger.exception(e)
        return jsonify({"status": "error", "message": str(e)})

@app.route('/webhook/nowpayments/ipn', methods=['POST'])
def nowpayments_ipn_webhook():
    """Endpoint for NowPayments IPN (Instant Payment Notification)"""
    try:
        # Verify that the request contains JSON data
        if not request.is_json:
            app.logger.error("Invalid payment webhook: Not JSON data")
            return jsonify({"status": "error", "message": "Invalid content type, expected JSON"}), 400
        
        # Get webhook data
        ipn_data = request.get_json()
        app.logger.info(f"Received payment IPN: {ipn_data}")
        
        # Verify IPN authenticity
        api_key = config_manager.get_config_value('nowpayments_api_key', '')
        if not api_key:
            app.logger.error("Cannot process IPN: NowPayments API key not set")
            return jsonify({"status": "error", "message": "API key not configured"}), 500
            
        # Initialize the API client
        from nowpayments import NowPayments
        nowpayments_api = NowPayments(api_key=api_key)
        
        # Verify the IPN signature
        is_valid = nowpayments_api.verify_ipn_callback(ipn_data)
        if not is_valid:
            app.logger.error("Invalid IPN signature")
            return jsonify({"status": "error", "message": "Invalid IPN signature"}), 400
            
        # Process the payment update
        payment_id = ipn_data.get('payment_id')
        payment_status = ipn_data.get('payment_status')
        
        if not payment_id or not payment_status:
            app.logger.error(f"Missing payment information in IPN: {ipn_data}")
            return jsonify({"status": "error", "message": "Missing payment information"}), 400
            
        app.logger.info(f"Processing payment update: Payment ID {payment_id}, Status: {payment_status}")
        
        # Find the payment transaction
        with db.session() as session:
            transaction = session.query(PaymentTransaction).filter_by(payment_id=payment_id).first()
            
            if not transaction:
                app.logger.error(f"Payment transaction not found: {payment_id}")
                return jsonify({"status": "error", "message": "Payment transaction not found"}), 404
                
            # Update transaction status and data
            transaction.status = payment_status
            transaction.ipn_data = ipn_data
            
            if payment_status in ["FINISHED", "CONFIRMED"]:
                transaction.completed_at = datetime.utcnow()
                
                # Update the corresponding order
                order = session.query(Order).get(transaction.order_id)
                if order:
                    previous_status = order.status
                    order.status = "PAYMENT_RECEIVED"
                    order.updated_at = datetime.utcnow()
                    
                    # Save changes
                    session.commit()
                    
                    app.logger.info(f"Payment confirmed for order #{order.order_id}: Status changed from {previous_status} to PAYMENT_RECEIVED")
                    
                    # Optionally notify admins about the payment
                    try:
                        from run_telegram_bot import notify_admins_about_payment
                        notify_admins_about_payment(order, transaction)
                    except Exception as notify_error:
                        app.logger.error(f"Error notifying admins: {str(notify_error)}")
                else:
                    app.logger.error(f"Order not found for payment: {payment_id}")
                    return jsonify({"status": "error", "message": "Order not found"}), 404
            else:
                # For other statuses, just update the transaction
                session.commit()
                app.logger.info(f"Payment status updated: {payment_id} to {payment_status}")
            
            return jsonify({"status": "success", "message": f"Payment updated: {payment_status}"})
    except Exception as e:
        app.logger.error(f"Error processing payment webhook: {str(e)}")
        app.logger.exception(e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
