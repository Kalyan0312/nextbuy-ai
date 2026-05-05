from app import app, db
from models import Product
import random

with app.app_context():
    products = Product.query.all()
    for p in products:
        p.price = round(random.uniform(499.0, 4999.0), 2)
    db.session.commit()
    print(f"Successfully updated {len(products)} product prices to a lower range (₹499 - ₹4,999).")
