#!/usr/bin/env python3
"""
Flask example of using SQLAlchemy-ViewORM.

This example demonstrates:
1. Integrating SQLAlchemy-ViewORM with Flask
2. Using materialized views to improve API endpoint performance
3. Refreshing materialized views on data changes
"""

import os

from flask import Flask, jsonify, request
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from sqlalchemy_view_orm import ViewBase, ViewConfig

# Initialize Flask application
app = Flask(__name__)

# Create a SQLite database for demonstration
DB_PATH = "flask_example.db"
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Configure SQLAlchemy
engine = create_engine(f"sqlite:///{DB_PATH}")
session_factory = sessionmaker(bind=engine)
db_session = scoped_session(session_factory)


# Create a base class for regular models
class Base(DeclarativeBase):
    pass


# Define a regular SQLAlchemy model
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)


# Define a materialized view for product statistics
class ProductStatsView(ViewBase):
    __tablename__ = "product_stats_view"

    category = Column(String(50), primary_key=True)
    product_count = Column(Integer)
    avg_price = Column(Float)
    min_price = Column(Float)
    max_price = Column(Float)

    __view_config__ = ViewConfig(
        definition=select(
            Product.category,
            func.count(Product.id).label("product_count"),
            func.avg(Product.price).label("avg_price"),
            func.min(Product.price).label("min_price"),
            func.max(Product.price).label("max_price"),
        )
        .where(Product.in_stock == True)
        .group_by(Product.category),
        materialized=True,
        materialized_as_table=True,  # Use table for SQLite
    )


# Create all tables and views
Base.metadata.create_all(engine)
for cmd in ProductStatsView.get_create_cmds(engine):
    with engine.begin() as conn:
        conn.execute(cmd)


# Sample data initialization
def init_db():
    with Session(engine) as session:
        # Check if data already exists
        if session.query(Product).count() > 0:
            return

        # Add sample products
        products = [
            Product(name="Laptop", category="Electronics", price=999.99),
            Product(name="Smartphone", category="Electronics", price=499.99),
            Product(name="Headphones", category="Electronics", price=79.99),
            Product(name="Python Programming", category="Books", price=39.99),
            Product(name="Database Design", category="Books", price=45.99),
            Product(name="T-Shirt", category="Clothing", price=19.99),
            Product(name="Jeans", category="Clothing", price=59.99),
            Product(name="Coffee Maker", category="Kitchen", price=89.99),
            Product(name="Blender", category="Kitchen", price=49.99),
            Product(
                name="Out of Stock Item",
                category="Electronics",
                price=299.99,
                in_stock=False,
            ),
        ]
        session.add_all(products)
        session.commit()

    # Refresh materialized view
    refresh_stats_view()


# Function to refresh the materialized view
def refresh_stats_view():
    for cmd in ProductStatsView.get_refresh_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)


# API Routes
@app.route("/products", methods=["GET"])
def get_products():
    """Get all products or filter by category."""
    category = request.args.get("category")

    with Session(engine) as session:
        query = session.query(Product).filter(Product.in_stock == True)

        if category:
            query = query.filter(Product.category == category)

        products = query.all()

        return jsonify(
            {
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "category": p.category,
                        "price": p.price,
                    }
                    for p in products
                ]
            }
        )


@app.route("/products", methods=["POST"])
def add_product():
    """Add a new product."""
    data = request.json

    if not all(k in data for k in ["name", "category", "price"]):
        return jsonify({"error": "Missing required fields"}), 400

    with Session(engine) as session:
        product = Product(
            name=data["name"],
            category=data["category"],
            price=float(data["price"]),
            in_stock=data.get("in_stock", True),
        )
        session.add(product)
        session.commit()

        # Refresh stats view after adding a product
        refresh_stats_view()

        return (
            jsonify(
                {
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "in_stock": product.in_stock,
                }
            ),
            201,
        )


@app.route("/stats", methods=["GET"])
def get_stats():
    """Get product statistics from the materialized view."""
    with Session(engine) as session:
        stats = session.query(ProductStatsView).all()

        return jsonify(
            {
                "stats": [
                    {
                        "category": s.category,
                        "product_count": s.product_count,
                        "avg_price": round(s.avg_price, 2),
                        "min_price": s.min_price,
                        "max_price": s.max_price,
                    }
                    for s in stats
                ]
            }
        )


@app.route("/stats/refresh", methods=["POST"])
def refresh_stats():
    """Manually refresh the stats view."""
    refresh_stats_view()
    return jsonify({"message": "Stats refreshed successfully"})


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Remove the database session at the end of the request."""
    db_session.remove()


if __name__ == "__main__":
    # Initialize the database with sample data
    init_db()

    # Run the Flask application
    app.run(debug=True, port=5000)

    # Usage examples:
    #
    # Get all products:
    # curl http://localhost:5000/products
    #
    # Get products by category:
    # curl http://localhost:5000/products?category=Electronics
    #
    # Add a new product:
    # curl -X POST -H "Content-Type: application/json" -d '{"name":"New Product","category":"Electronics","price":199.99}' http://localhost:5000/products
    #
    # Get statistics from materialized view:
    # curl http://localhost:5000/stats
    #
    # Refresh the statistics view:
    # curl -X POST http://localhost:5000/stats/refresh
