from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from recommender import RecommenderSystem
from models import db, User, Product, UserInteraction, Category, Brand, Order, OrderItem, CartItem, Model
import os
import threading
import time

app = Flask(__name__)
app.secret_key = 'nextgen_secret_key_super_secure'

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:kalyan03@localhost/nextbuy_db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Initialize Recommender System
recommender = None
try:
    recommender = RecommenderSystem(app)
except Exception as e:
    print(f"Error initializing recommender: {e}")

def automate_order_status(app_context, order_id):
    """Background task to simulate order progress every 30 seconds"""
    statuses = ['Shipped', 'Out for Delivery', 'Delivered']
    for status in statuses:
        time.sleep(30)
        with app_context:
            order = Order.query.get(order_id)
            if order:
                order.status = status
                db.session.commit()
                print(f"Order #{order_id} automatically updated to: {status}")
            else:
                break

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user_name = session.get('user_name', f'User {user_id}')
    
    # Get personalized recommendations
    if recommender:
        recommended_products = recommender.get_user_recommendations(user_id, n_recommendations=8)
        top_products = recommender.get_top_products(n=4)
    else:
        recommended_products = []
        top_products = []
        
    return render_template('index.html', 
                           user_name=user_name, 
                           recommended_products=recommended_products,
                           top_products=top_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        if user_id and user_id.isdigit():
            u_id = int(user_id)
            user = User.query.get(u_id)
            if user:
                session['user_id'] = u_id
                session['user_name'] = user.name
                session['is_admin'] = user.is_admin
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='User not found.')
        else:
            return render_template('login.html', error='Invalid User ID. Please enter a number between 1 and 50.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return render_template('access_denied.html'), 403
        
    if recommender:
        insights = recommender.get_dashboard_insights()
    else:
        insights = {}
        
    return render_template('dashboard.html', insights=insights)

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not recommender or not query:
        return jsonify([])
        
    results = Product.query.filter(
        (Product.name.ilike(f'%{query}%')) | 
        (Product.description.ilike(f'%{query}%'))
    ).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'image_url': p.image_url
    } for p in results])

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    product = Product.query.get_or_404(product_id)
    
    # Log interaction
    interaction = UserInteraction(
        user_id=session['user_id'],
        product_id=product_id,
        interaction_type='view',
        interaction_value=1.0
    )
    db.session.add(interaction)
    db.session.commit()
    
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Please login first'}), 401
        
    user_id = session['user_id']
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
        db.session.add(cart_item)
    
    # Log interaction
    interaction = UserInteraction(
        user_id=user_id,
        product_id=product_id,
        interaction_type='add_to_cart',
        interaction_value=2.0
    )
    db.session.add(interaction)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Product added to cart'})

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id == session['user_id']:
        db.session.delete(cart_item)
        db.session.commit()
        
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
    if not cart_items:
        return redirect(url_for('index'))
        
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    payment_method = request.form.get('payment_method')
    shipping_address = request.form.get('address')
    
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return redirect(url_for('index'))
        
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    new_order = Order(
        user_id=user_id,
        order_total=total,
        status='Pending',
        payment_method=payment_method,
        shipping_address=shipping_address,
        tracking_number=f'NB{user_id}{int(datetime.utcnow().timestamp())}'
    )
    db.session.add(new_order)
    db.session.flush() # Get order ID
    
    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)
        
        # Log purchase interaction
        interaction = UserInteraction(
            user_id=user_id,
            product_id=item.product_id,
            interaction_type='purchase',
            interaction_value=5.0
        )
        db.session.add(interaction)
        
        # Remove from cart
        db.session.delete(item)
        
    db.session.commit()
    
    # Refresh recommender data to include new purchase
    if recommender:
        recommender.refresh_data()
    
    # Start background automation for status updates
    automation_thread = threading.Thread(
        target=automate_order_status, 
        args=(app.app_context(), new_order.id)
    )
    automation_thread.daemon = True
    automation_thread.start()
    
    return redirect(url_for('track_order', order_id=new_order.id))

@app.route('/track_order/<int:order_id>')
def track_order(order_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    order = Order.query.get_or_404(order_id)
    if order.user_id != session['user_id']:
        return "Access Denied", 403
        
    return render_template('track_order.html', order=order)

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/models')
def models_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        return render_template('access_denied.html'), 403
        
    all_models = Model.query.all()
    return render_template('models.html', models=all_models)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
