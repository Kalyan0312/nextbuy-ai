import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

def generate_mock_data():
    # 1. Users
    users_data = []
    locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'London', 'Paris', 'Tokyo']
    for i in range(1, 51):
        users_data.append({
            'user_id': i,
            'name': f'User {i}',
            'age': random.randint(18, 65),
            'gender': random.choice(['M', 'F', 'O']),
            'location': random.choice(locations)
        })
    users_df = pd.DataFrame(users_data)
    users_df.to_csv('data/users.csv', index=False)

    # 2. Products
    products_data = []
    categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books']
    
    product_names = {
        'Electronics': ['Smartphone Pro', 'Wireless Earbuds', 'Smart Watch', 'Laptop Ultra', 'Gaming Console', '4K TV', 'Bluetooth Speaker', 'Digital Camera', 'Tablet Pad', 'Power Bank'],
        'Clothing': ['Classic T-Shirt', 'Denim Jeans', 'Hoodie Oversized', 'Summer Dress', 'Leather Jacket', 'Running Shoes', 'Formal Shirt', 'Silk Scarf', 'Woolen Sweater', 'Cotton Socks'],
        'Home & Garden': ['Smart Bulb', 'Robot Vacuum', 'Coffee Maker', 'Office Chair', 'Garden Tools', 'Luxury Bedding', 'Ceramic Vase', 'Kitchen Scale', 'Wall Clock', 'Plush Rug'],
        'Sports': ['Yoga Mat', 'Dumbbells Set', 'Basketball', 'Football Boots', 'Swimming Goggles', 'Tennis Racket', 'Cycling Helmet', 'Jump Rope', 'Hiking Bag', 'Resistance Bands'],
        'Books': ['Mystery Novel', 'Sci-Fi Epic', 'Self-Help Guide', 'Cooking Recipes', 'History Book', 'Biography', 'Art Collection', 'Travel Guide', 'Poetry Book', 'Children\'s Story']
    }

    for i in range(1, 201):
        category = random.choice(categories)
        # Map categories to local images for relevance
        category_images = {
            'Electronics': '/static/images/electronics.png',
            'Clothing': '/static/images/clothing.png',
            'Home & Garden': '/static/images/home.png',
            'Sports': '/static/images/sports.png',
            'Books': '/static/images/books.png'
        }
        
        name_base = random.choice(product_names[category])
        
        products_data.append({
            'product_id': i,
            'name': f'{name_base} {i}',
            'category': category,
            'price': round(random.uniform(500.0, 60000.0), 0),
            'rating': round(random.uniform(3.5, 5.0), 1),
            'image_url': category_images.get(category, '/static/images/electronics.png')
        })
    products_df = pd.DataFrame(products_data)
    products_df.to_csv('data/products.csv', index=False)

    # 3. Interactions (Views, Clicks, Purchases, Ratings)
    interactions_data = []
    types = ['view', 'click', 'purchase', 'rating']
    
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(1000):
        user_id = random.randint(1, 50)
        product_id = random.randint(1, 100)
        interaction = random.choice(types)
        
        # Determine score/value based on interaction type to simulate ratings/purchases
        value = 1
        if interaction == 'rating':
            value = random.randint(1, 5)
        elif interaction == 'purchase':
            value = 5
        elif interaction == 'click':
            value = 2
        elif interaction == 'view':
            value = 1
            
        interactions_data.append({
            'user_id': user_id,
            'product_id': product_id,
            'interaction_type': interaction,
            'value': value, # Implicit or explicit rating
            'timestamp': start_date + timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        })
        
    interactions_df = pd.DataFrame(interactions_data)
    interactions_df.to_csv('data/interactions.csv', index=False)
    
    print("Mock data generated successfully in data/ directory.")

if __name__ == '__main__':
    generate_mock_data()
