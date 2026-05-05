import pandas as pd
import os
import random
from app import app, db
from models import (User, Product, UserInteraction, Category, Brand, 
                    UserProfile, Session, Order, OrderItem, Model, 
                    ModelFeature, TrainingDataset, ModelTrainingRun)
from datetime import datetime, timedelta

def migrate_and_mock():
    with app.app_context():
        print("Clearing and recreating database tables...")
        db.drop_all()
        db.create_all()
        
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        
        # 1. Migrate Users from CSV
        print("Migrating Users...")
        users_df = pd.read_csv(os.path.join(data_dir, 'users.csv'))
        user_ids = []
        for _, row in users_df.iterrows():
            user = User(
                id=int(row['user_id']),
                name=row['name'],
                email=f"user{row['user_id']}@example.com",
                gender=row['gender'],
                is_admin=(int(row['user_id']) == 50)
            )
            db.session.add(user)
            db.session.flush()
            user_ids.append(user.id)
            
            profile = UserProfile(
                user_id=user.id,
                location=row['location'],
                interests=["Electronics", "Fashion", "Books"] if random.random() > 0.5 else ["Home", "Beauty"],
                lifecycle_stage="Active"
            )
            db.session.add(profile)
            
        # 2. Create Brands (Mock)
        print("Creating Mock Brands...")
        brand_names = ["TechNova", "EcoStyle", "PureEssence", "GlowUp", "EliteEdge"]
        brands = []
        for name in brand_names:
            brand = Brand(brand_name=name)
            db.session.add(brand)
            db.session.flush()
            brands.append(brand)
            
        # 3. Migrate Products from CSV
        print("Migrating Products and Categories...")
        products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
        
        categories = products_df['category'].unique()
        category_map = {}
        for cat_name in categories:
            cat = Category(category_name=cat_name)
            db.session.add(cat)
            db.session.flush()
            category_map[cat_name] = cat.id
            
        product_ids = []
        for _, row in products_df.iterrows():
            product = Product(
                id=int(row['product_id']),
                name=row['name'],
                price=float(row['price']),
                rating=float(row['rating']),
                image_url=row['image_url'],
                category_id=category_map.get(row['category']),
                brand_id=random.choice(brands).id,
                description=f"High-quality {row['category']} product from our latest collection.",
                sku=f"SKU-{row['product_id']:04d}"
            )
            db.session.add(product)
            db.session.flush()
            product_ids.append(product.id)
            
        # 4. Create Sessions (Mock)
        print("Creating Mock Sessions...")
        for uid in user_ids:
            for _ in range(3): # 3 sessions per user
                start = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                sess = Session(
                    user_id=uid,
                    session_start=start,
                    session_end=start + timedelta(minutes=random.randint(5, 60)),
                    device_type=random.choice(["Mobile", "Desktop", "Tablet"]),
                    ip_address=f"192.168.1.{random.randint(1, 254)}"
                )
                db.session.add(sess)
        
        # 5. Migrate Interactions from CSV
        print("Migrating Interactions...")
        interactions_df = pd.read_csv(os.path.join(data_dir, 'interactions.csv'))
        for _, row in interactions_df.iterrows():
            try:
                ts = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S.%f')
            except:
                ts = datetime.utcnow()
                
            interaction = UserInteraction(
                user_id=int(row['user_id']),
                product_id=int(row['product_id']),
                interaction_type=row['interaction_type'],
                interaction_value=float(row['value']),
                created_at=ts
            )
            db.session.add(interaction)
            
        # 6. Create Orders (Mock)
        print("Creating Mock Orders...")
        for uid in user_ids:
            # User 50 is admin, others get history. 
            # Every user should have 10 orders to establish a clear buying pattern.
            if uid < 50:
                num_orders = 10
                # Assign a "preferred category" to this user to create a distinct pattern
                preferred_category = random.choice(categories)
                # Filter products of that category
                cat_prods = [p.id for p in Product.query.filter_by(category_id=category_map[preferred_category]).all()]
                other_prods = [p.id for p in Product.query.filter(Product.category_id != category_map[preferred_category]).all()]
            else:
                num_orders = 0
                
            for _ in range(num_orders):
                order = Order(
                    user_id=uid,
                    order_date=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                    order_total=0.0,
                    status="Delivered",
                    payment_method=random.choice(["COD", "UPI", "Card"]),
                    shipping_address=f"{random.randint(100, 999)} AI Street, {random.choice(['Silicon Valley', 'New Delhi', 'Bangalore', 'London'])}",
                    tracking_number=f"NB{uid}{random.randint(100000, 999999)}"
                )
                db.session.add(order)
                db.session.flush()
                
                total = 0
                # User buys 2-3 items per order, 70% chance it's from their favorite category
                for _ in range(random.randint(1, 3)):
                    if random.random() < 0.7 and cat_prods:
                        pid = random.choice(cat_prods)
                    else:
                        pid = random.choice(other_prods) if other_prods else random.choice(product_ids)
                        
                    prod = db.session.get(Product, pid)
                    item = OrderItem(
                        order_id=order.id,
                        product_id=pid,
                        quantity=random.randint(1, 2),
                        price=prod.price
                    )
                    total += item.price * item.quantity
                    db.session.add(item)
                    
                    # Add purchase interaction for recommender
                    interaction = UserInteraction(
                        user_id=uid,
                        product_id=pid,
                        interaction_type='purchase',
                        interaction_value=5.0,
                        created_at=order.order_date
                    )
                    db.session.add(interaction)
                order.order_total = total
                
        # 7. Create AI Model Info (Mock)
        print("Creating Mock AI Model info...")
        model = Model(
            model_name="CollaborativeFiltering-v1",
            model_type="Collaborative",
            version="1.0.0",
            status="Active",
            trained_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(model)
        db.session.flush()
        
        feature = ModelFeature(
            model_id=model.id,
            feature_name="UserInteractionHistory",
            feature_type="Sequence",
            description="Sequence of user product views and purchases"
        )
        db.session.add(feature)
        
        dataset = TrainingDataset(
            model_id=model.id,
            source_type="behavior",
            data_period_start=datetime.utcnow() - timedelta(days=90),
            data_period_end=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(dataset)
        db.session.flush()
        
        run = ModelTrainingRun(
            model_id=model.id,
            dataset_id=dataset.id,
            run_started_at=datetime.utcnow() - timedelta(hours=26),
            run_completed_at=datetime.utcnow() - timedelta(hours=25),
            training_metrics={"rmse": 0.85, "precision": 0.72},
            status="Success"
        )
        db.session.add(run)
            
        db.session.commit()
        print("Migration and Mock data generation completed successfully!")

if __name__ == '__main__':
    migrate_and_mock()
