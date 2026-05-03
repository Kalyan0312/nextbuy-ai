from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from recommender import RecommenderSystem
import os

app = Flask(__name__)
app.secret_key = 'nextgen_secret_key_super_secure'

# Initialize Recommender System
recommender = None
try:
    recommender = RecommenderSystem()
except Exception as e:
    print(f"Error initializing recommender: {e}")

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
            session['user_id'] = int(user_id)
            session['user_name'] = f'User {user_id}'
            return redirect(url_for('index'))
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
        
    # Simple search on products
    products = recommender.products_df
    results = products[products['name'].str.lower().str.contains(query) | 
                       products['category'].str.lower().str.contains(query)]
    
    return jsonify(results.head(10).to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
