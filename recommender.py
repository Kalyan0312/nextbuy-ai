import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os

class RecommenderSystem:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.users_df = pd.read_csv(os.path.join(self.data_dir, 'users.csv'))
        self.products_df = pd.read_csv(os.path.join(self.data_dir, 'products.csv'))
        self.interactions_df = pd.read_csv(os.path.join(self.data_dir, 'interactions.csv'))
        
        self.interaction_matrix = None
        self.user_similarity_df = None
        
        self._prepare_data()

    def _prepare_data(self):
        # Data Cleaning
        self.interactions_df.drop_duplicates(inplace=True)
        
        # User-Product Interaction Matrix
        self.interaction_matrix = self.interactions_df.pivot_table(
            index='user_id', 
            columns='product_id', 
            values='value',
            aggfunc='max'
        ).fillna(0)
        
        # Calculate User-User Cosine Similarity
        user_similarity = cosine_similarity(self.interaction_matrix)
        self.user_similarity_df = pd.DataFrame(
            user_similarity, 
            index=self.interaction_matrix.index, 
            columns=self.interaction_matrix.index
        )
        
    def get_user_recommendations(self, user_id, n_recommendations=5):
        if user_id not in self.interaction_matrix.index:
            # Cold start: return top rated products
            return self.get_top_products(n_recommendations)
            
        # Get similar users
        similar_users = self.user_similarity_df[user_id].sort_values(ascending=False).index[1:]
        
        # Get products the user has already interacted with
        user_interacted_products = self.interaction_matrix.loc[user_id]
        user_interacted_products = user_interacted_products[user_interacted_products > 0].index
        
        recommendations = {}
        for sim_user in similar_users:
            sim_user_products = self.interaction_matrix.loc[sim_user]
            for product_id, score in sim_user_products.items():
                if score > 0 and product_id not in user_interacted_products:
                    if product_id not in recommendations:
                        recommendations[product_id] = 0
                    recommendations[product_id] += score * self.user_similarity_df.loc[user_id, sim_user]
                    
        # Sort recommendations
        sorted_recs = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:n_recommendations]
        rec_product_ids = [req[0] for req in sorted_recs]
        
        return self.products_df[self.products_df['product_id'].isin(rec_product_ids)].to_dict('records')
        
    def get_top_products(self, n=5):
        # Based on average rating and number of interactions
        top_products = self.products_df.sort_values(by='rating', ascending=False).head(n)
        return top_products.to_dict('records')

    def get_dashboard_insights(self):
        # Dashboard: Top products, conversion rate, customer retention, revenue insights
        total_interactions = len(self.interactions_df)
        purchases = self.interactions_df[self.interactions_df['interaction_type'] == 'purchase']
        
        conversion_rate = (len(purchases) / total_interactions * 100) if total_interactions > 0 else 0
        
        # Revenue Insights (Dummy logic based on purchases)
        revenue = sum(
            self.products_df[self.products_df['product_id'] == pid]['price'].values[0]
            for pid in purchases['product_id']
        ) if len(purchases) > 0 else 0
        
        # Active users (users with > 1 interaction)
        user_counts = self.interactions_df['user_id'].value_counts()
        retained_users = len(user_counts[user_counts > 1])
        retention_rate = (retained_users / len(self.users_df) * 100) if len(self.users_df) > 0 else 0
        
        return {
            'total_users': len(self.users_df),
            'total_products': len(self.products_df),
            'conversion_rate': round(conversion_rate, 2),
            'retention_rate': round(retention_rate, 2),
            'total_revenue': round(revenue, 2),
            'top_categories': self.products_df['category'].value_counts().head(5).to_dict()
        }
