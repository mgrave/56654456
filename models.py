from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# ایجاد یک base model
Base = declarative_base()

class User(Base):
    """Model representing a Telegram user"""
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = relationship('Order', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Order(Base):
    """Model representing a subscription order"""
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    plan_id = Column(String(50), nullable=False)
    plan_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    status = Column(String(50), nullable=False)
    telegram_username = Column(String(100), nullable=False)
    admin_notes = Column(Text)
    payment_id = Column(String(100))
    payment_url = Column(String(255))
    activation_link = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    
    payments = relationship('PaymentTransaction', backref='order_rel', lazy=True)
    
    def __repr__(self):
        return f'<Order {self.order_id}>'

class PaymentTransaction(Base):
    """Model representing a payment transaction"""
    __tablename__ = 'payment_transaction'
    id = Column(Integer, primary_key=True)
    payment_id = Column(String(100), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey('order.id'), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    pay_currency = Column(String(10), default='TRX')
    status = Column(String(50), nullable=False)
    ipn_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    
    def __repr__(self):
        return f'<PaymentTransaction {self.payment_id}>'

class AdminUser(UserMixin, Base):
    """Model representing an admin user for the web interface"""
    __tablename__ = 'admin_user'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_super_admin = Column(Boolean, default=False)
    api_key_hash = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to broadcast messages
    broadcast_messages = relationship('BroadcastMessage', backref='admin', lazy=True)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'

class BroadcastMessage(Base):
    """Model representing a broadcast message sent to all users"""
    __tablename__ = 'broadcast_message'
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admin_user.id'), nullable=False)
    message_text = Column(Text, nullable=False)
    sent_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    status = Column(String(20), default='PENDING')  # PENDING, SENDING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f'<BroadcastMessage id={self.id} status={self.status}>'
