#!/usr/bin/env python3
"""
Advanced example of using SQLAlchemy-ViewORM.

This example demonstrates more complex scenarios:
1. Creating dialect-specific view definitions
2. Working with PostgreSQL-specific features
3. Using different view types based on database dialect
4. View refreshing strategies
"""

import os

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    create_engine,
    func,
    select,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Session, relationship

# Import SQLAlchemy-ViewORM components
from sqlalchemy_view_orm import ViewBase, ViewConfig, ViewMethod


# Create a base class for regular models
class Base(DeclarativeBase):
    pass


# Define regular SQLAlchemy models
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    products = relationship("Product", back_populates="category")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    vip = Column(Boolean, default=False)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    shipped = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# Define a function to create dialect-specific view definition
def create_product_sales_query(dialect_name):
    """Create a query for product sales that adapts to the dialect."""
    if dialect_name == "postgresql":
        # PostgreSQL-specific query with window functions
        return (
            select(
                Product.id,
                Product.name,
                Category.name.label("category"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.quantity * Product.price).label("total_sales"),
                func.rank()
                .over(
                    partition_by=Category.id,
                    order_by=func.sum(OrderItem.quantity * Product.price).desc(),
                )
                .label("rank_in_category"),
            )
            .select_from(Product)
            .join(Category)
            .join(OrderItem)
            .where(Product.active == True)
            .group_by(Product.id, Product.name, Category.name, Category.id)
        )
    else:
        # Simpler query for other database dialects
        return (
            select(
                Product.id,
                Product.name,
                Category.name.label("category"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.quantity * Product.price).label("total_sales"),
                # No ranking for non-PostgreSQL databases
                func.cast(0, Integer).label("rank_in_category"),
            )
            .select_from(Product)
            .join(Category)
            .join(OrderItem)
            .where(Product.active == True)
            .group_by(Product.id, Product.name, Category.name)
        )


# Define a materialized view for product sales
class ProductSalesView(ViewBase):
    __tablename__ = "product_sales_view"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    category = Column(String(50))
    total_quantity = Column(Integer)
    total_sales = Column(Float)
    rank_in_category = Column(Integer)

    # Define view configuration with dialect-specific query
    __view_config__ = ViewConfig(
        definer=create_product_sales_query,  # Dynamic query based on dialect
        materialized=True,  # Create as materialized view when supported
        materialized_as_table=True,  # Fall back to table simulation if needed
        concurrently=True,  # Use concurrent refresh on PostgreSQL
    )


# Define a view for VIP customer orders
class VipOrdersView(ViewBase):
    __tablename__ = "vip_orders_view"

    order_id = Column(Integer, primary_key=True)
    customer_name = Column(String(100))
    order_date = Column(String(10))
    product_name = Column(String(100))
    quantity = Column(Integer)
    total = Column(Float)

    # Define the view using a standard definition
    __view_config__ = ViewConfig(
        definition=select(
            Order.id.label("order_id"),
            Customer.name.label("customer_name"),
            Order.order_date,
            Product.name.label("product_name"),
            OrderItem.quantity,
            (OrderItem.quantity * Product.price).label("total"),
        )
        .select_from(Order)
        .join(Customer)
        .join(OrderItem)
        .join(Product)
        .where(Customer.vip == True),
        # This view is not materialized
        materialized=False,
    )


def populate_sample_data(session):
    """Add sample data to the database."""
    # Add categories
    categories = [
        Category(name="Electronics"),
        Category(name="Books"),
        Category(name="Clothing"),
    ]
    session.add_all(categories)
    session.flush()

    # Add products
    products = [
        Product(name="Laptop", price=999.99, category_id=categories[0].id),
        Product(name="Smartphone", price=499.99, category_id=categories[0].id),
        Product(name="Headphones", price=79.99, category_id=categories[0].id),
        Product(name="Python Programming", price=39.99, category_id=categories[1].id),
        Product(name="Database Design", price=45.99, category_id=categories[1].id),
        Product(name="T-Shirt", price=19.99, category_id=categories[2].id),
        Product(name="Jeans", price=59.99, category_id=categories[2].id),
        Product(
            name="Tablet", price=349.99, category_id=categories[0].id, active=False
        ),
    ]
    session.add_all(products)
    session.flush()

    # Add customers
    customers = [
        Customer(name="John Doe", email="john@example.com", vip=True),
        Customer(name="Jane Smith", email="jane@example.com", vip=False),
        Customer(name="Robert Brown", email="robert@example.com", vip=True),
    ]
    session.add_all(customers)
    session.flush()

    # Add orders
    orders = [
        Order(customer_id=customers[0].id, order_date="2023-01-15"),
        Order(customer_id=customers[0].id, order_date="2023-02-20"),
        Order(customer_id=customers[1].id, order_date="2023-01-18"),
        Order(customer_id=customers[2].id, order_date="2023-02-05"),
    ]
    session.add_all(orders)
    session.flush()

    # Add order items
    order_items = [
        # John's first order
        OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=1),
        OrderItem(order_id=orders[0].id, product_id=products[2].id, quantity=1),
        # John's second order
        OrderItem(order_id=orders[1].id, product_id=products[3].id, quantity=2),
        # Jane's order
        OrderItem(order_id=orders[2].id, product_id=products[1].id, quantity=1),
        OrderItem(order_id=orders[2].id, product_id=products[5].id, quantity=3),
        # Robert's order
        OrderItem(order_id=orders[3].id, product_id=products[0].id, quantity=1),
        OrderItem(order_id=orders[3].id, product_id=products[4].id, quantity=1),
        OrderItem(order_id=orders[3].id, product_id=products[6].id, quantity=2),
    ]
    session.add_all(order_items)
    session.commit()


def main():
    """Run the advanced example."""
    # For this example, we'll use SQLite, but this would work with any supported database
    db_file = "advanced_example.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    engine = create_engine(f"sqlite:///{db_file}", echo=True)

    # Create all tables
    Base.metadata.create_all(engine)

    # Create the views
    for view_class in [ProductSalesView, VipOrdersView]:
        for cmd in view_class.get_create_cmds(engine):
            with engine.begin() as conn:
                conn.execute(cmd)

    # Populate the database with sample data
    with Session(engine) as session:
        populate_sample_data(session)

    # Refresh the materialized views
    for cmd in ProductSalesView.get_refresh_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)

    # Query and display the views
    with Session(engine) as session:
        print("\n== Product Sales (from materialized view) ==")
        product_sales = (
            session.query(ProductSalesView)
            .order_by(ProductSalesView.total_sales.desc())
            .all()
        )
        for product in product_sales:
            print(f"Product: {product.name} (Category: {product.category})")
            print(f"  Total Quantity: {product.total_quantity}")
            print(f"  Total Sales: ${product.total_sales:.2f}")
            print(f"  Rank in Category: {product.rank_in_category}")
            print()

        print("\n== VIP Customer Orders (from view) ==")
        vip_orders = (
            session.query(VipOrdersView).order_by(VipOrdersView.order_date).all()
        )
        current_order_id = None
        order_total = 0

        for item in vip_orders:
            if current_order_id != item.order_id:
                if current_order_id is not None:
                    print(f"  Order Total: ${order_total:.2f}\n")
                current_order_id = item.order_id
                order_total = 0
                print(f"Order ID: {item.order_id}")
                print(f"Customer: {item.customer_name}")
                print(f"Date: {item.order_date}")
                print("Items:")

            print(f"  - {item.product_name} (Qty: {item.quantity}) - ${item.total:.2f}")
            order_total += item.total

        if current_order_id is not None:
            print(f"  Order Total: ${order_total:.2f}\n")

    # Demonstrate view method detection
    print("\n== View Method Detection ==")
    dialect_methods = {
        "postgresql": {
            "ProductSalesView": ProductSalesView.get_method("postgresql"),
            "VipOrdersView": VipOrdersView.get_method("postgresql"),
        },
        "sqlite": {
            "ProductSalesView": ProductSalesView.get_method("sqlite"),
            "VipOrdersView": VipOrdersView.get_method("sqlite"),
        },
        "mysql": {
            "ProductSalesView": ProductSalesView.get_method("mysql"),
            "VipOrdersView": VipOrdersView.get_method("mysql"),
        },
    }

    for dialect, views in dialect_methods.items():
        print(f"\nOn {dialect.upper()}:")
        for view_name, method in views.items():
            print(f"  {view_name} would be created as: {method.value}")

    # Clean up - drop the views
    for view_class in [VipOrdersView, ProductSalesView]:
        for cmd in view_class.get_drop_cmds(engine, if_exists=True):
            with engine.begin() as conn:
                conn.execute(cmd)

    # Drop the tables
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    main()
