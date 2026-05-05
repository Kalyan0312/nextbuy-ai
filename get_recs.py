from app import app, recommender
from models import Product

with app.app_context():
    recs = recommender.get_user_recommendations(50, n_recommendations=5)
    print("--- RECOMMENDATIONS FOR USER 50 ---")
    for r in recs:
        print(f"- {r['name']} ({r['category']}) | Price: INR {r['price']}")
