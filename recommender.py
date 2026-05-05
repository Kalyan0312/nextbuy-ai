import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from models import db, User, Product, UserInteraction, Category, Order, OrderItem, Model
from sqlalchemy import func

class RecommenderSystem:
    def __init__(self, app):
        self.app = app
        self.interaction_matrix = None
        self.user_similarity_df = None
        self.products_df = None
        
        self.refresh_data()

    def refresh_data(self):
        with self.app.app_context():
            # Load Data from DB into DataFrames for vector calculations
            interactions = UserInteraction.query.all()
            self.interactions_df = pd.DataFrame([{
                'user_id': i.user_id,
                'product_id': i.product_id,
                'interaction_type': i.interaction_type,
                'value': i.interaction_value
            } for i in interactions])
            
            products = Product.query.all()
            self.products_df = pd.DataFrame([{
                'product_id': p.id,
                'name': p.name,
                'category': p.category.category_name if p.category else 'Uncategorized',
                'price': p.price,
                'rating': p.rating,
                'image_url': p.image_url
            } for p in products])
            
            users = User.query.all()
            self.users_count = len(users)
            
            if not self.interactions_df.empty:
                self._prepare_matrix()

    def _prepare_matrix(self):
        # User-Product Interaction Matrix
        self.interaction_matrix = self.interactions_df.pivot_table(
            index='user_id', 
            columns='product_id', 
            values='value',
            aggfunc='max'
        ).fillna(0)
        
        # Calculate User-User Cosine Similarity
        if not self.interaction_matrix.empty:
            user_similarity = cosine_similarity(self.interaction_matrix)
            self.user_similarity_df = pd.DataFrame(
                user_similarity, 
                index=self.interaction_matrix.index, 
                columns=self.interaction_matrix.index
            )
        
    def get_user_recommendations(self, user_id, n_recommendations=8):
        if self.interaction_matrix is None or user_id not in self.interaction_matrix.index:
            print(f"User {user_id} not in interaction matrix. Falling back to top products.")
            return self.get_top_products(n_recommendations)
            
        # Get similarity scores for this user
        user_scores = self.user_similarity_df[user_id]
        
        # Get products the user has already bought/viewed
        user_interacted_products = self.interaction_matrix.loc[user_id]
        user_interacted_products = user_interacted_products[user_interacted_products > 0].index.tolist()
        
        # Collaborative filtering: score products based on similar users' interactions
        # We exclude the user themselves (index[1:])
        similar_users = user_scores.sort_values(ascending=False).index[1:20] # Top 20 similar users
        
        product_scores = {}
        for sim_user in similar_users:
            sim_score = user_scores[sim_user]
            if sim_score <= 0: continue
            
            sim_user_interactions = self.interaction_matrix.loc[sim_user]
            # Only consider products with high interaction (purchase/click)
            for product_id, val in sim_user_interactions.items():
                if val > 0 and product_id not in user_interacted_products:
                    if product_id not in product_scores:
                        product_scores[product_id] = 0
                    # Weight by similarity score AND interaction value
                    product_scores[product_id] += sim_score * val
                    
        if not product_scores:
            print(f"No personalized recommendations for user {user_id}. Falling back to top products.")
            return self.get_top_products(n_recommendations)
            
        # Sort and get top N
        sorted_product_ids = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]
        rec_ids = [pid for pid, score in sorted_product_ids]
        
        # Return full product details
        recs = []
        for pid in rec_ids:
            p = Product.query.get(pid)
            if p:
                recs.append({
                    'product_id': p.id,
                    'name': p.name,
                    'category': p.category.category_name if p.category else 'General',
                    'price': p.price,
                    'rating': p.rating,
                    'image_url': p.image_url
                })
        
        print(f"Generated {len(recs)} personalized recommendations for user {user_id}")
        return recs
        
    def get_top_products(self, n=5):
        top_products = self.products_df.sort_values(by='rating', ascending=False).head(n)
        return top_products.to_dict('records')

    def get_dashboard_insights(self):
        with self.app.app_context():
            total_users = User.query.count()
            total_products = Product.query.count()
            total_interactions = UserInteraction.query.count()
            
            purchases_count = UserInteraction.query.filter_by(interaction_type='purchase').count()
            conversion_rate = (purchases_count / total_interactions * 100) if total_interactions > 0 else 0
            
            # Revenue from Orders table
            total_revenue = db.session.query(func.sum(Order.order_total)).scalar() or 0
            
            # Active users (with interactions)
            active_users_count = db.session.query(UserInteraction.user_id).distinct().count()
            retention_rate = (active_users_count / total_users * 100) if total_users > 0 else 0
            
            # Top categories from Category table
            categories_count = db.session.query(Category.category_name, func.count(Product.id)).\
                join(Product).group_by(Category.category_name).all()
            top_categories = {name: count for name, count in categories_count}
            
            return {
                'total_users': total_users,
                'total_products': total_products,
                'conversion_rate': round(conversion_rate, 2),
                'retention_rate': round(retention_rate, 2),
                'total_revenue': round(total_revenue, 2),
                'top_categories': top_categories
            }
