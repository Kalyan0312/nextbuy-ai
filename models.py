from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    interactions = db.relationship('UserInteraction', backref='user', lazy=True)
    sessions = db.relationship('Session', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    recommendation_requests = db.relationship('RecommendationRequest', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    location = db.Column(db.String(100), nullable=True)
    preferred_category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    interests = db.Column(db.JSON, nullable=True)
    lifecycle_stage = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category_name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    products = db.relationship('Product', backref='category', lazy=True)

class Brand(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    products = db.relationship('Product', backref='brand', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Float, default=0.0) # Added to support existing data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    interactions = db.relationship('UserInteraction', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    recommendation_results = db.relationship('RecommendationResult', backref='product', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    session_end = db.Column(db.DateTime, nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    interactions = db.relationship('UserInteraction', backref='session', lazy=True)
    recommendation_requests = db.relationship('RecommendationRequest', backref='session', lazy=True)

class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False) # view, click, add_to_cart, purchase, search, wishlist
    interaction_value = db.Column(db.Float, nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecommendationRequest(db.Model):
    __tablename__ = 'recommendation_requests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=True)
    request_context = db.Column(db.JSON, nullable=True) # device, location, time
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=True)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    results = db.relationship('RecommendationResult', backref='request', lazy=True)

class RecommendationResult(db.Model):
    __tablename__ = 'recommendation_results'
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('recommendation_requests.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rank_position = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Float, nullable=True)
    reason_code = db.Column(db.String(50), nullable=True)
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    order_total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Shipped, Out for Delivery, Delivered
    payment_method = db.Column(db.String(50), nullable=True) # COD, UPI, Card
    shipping_address = db.Column(db.Text, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product')

class Model(db.Model):
    __tablename__ = 'models'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=True) # Collaborative, Content, Hybrid, Deep Learning
    version = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=True)
    trained_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    features = db.relationship('ModelFeature', backref='model', lazy=True)
    training_runs = db.relationship('ModelTrainingRun', backref='model', lazy=True)
    datasets = db.relationship('TrainingDataset', backref='model', lazy=True)

class ModelFeature(db.Model):
    __tablename__ = 'model_features'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    feature_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)

class TrainingDataset(db.Model):
    __tablename__ = 'training_datasets'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    source_type = db.Column(db.String(100), nullable=True) # behavior / product / user / content
    data_period_start = db.Column(db.DateTime, nullable=True)
    data_period_end = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    training_runs = db.relationship('ModelTrainingRun', backref='dataset', lazy=True)

class ModelTrainingRun(db.Model):
    __tablename__ = 'model_training_runs'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('models.id'), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('training_datasets.id'), nullable=False)
    run_started_at = db.Column(db.DateTime, default=datetime.utcnow)
    run_completed_at = db.Column(db.DateTime, nullable=True)
    training_metrics = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=True)
