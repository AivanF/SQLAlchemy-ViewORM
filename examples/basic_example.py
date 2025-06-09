#!/usr/bin/env python3
"""
Basic example of using SQLAlchemy-ViewORM.

This example demonstrates:
1. Setting up SQLAlchemy models
2. Creating a simple view
3. Creating a materialized view
4. Working with the views using SQLAlchemy ORM
"""

import os

from sqlalchemy import Boolean, Column, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session

# Import SQLAlchemy-ViewORM components
from sqlalchemy_view_orm import ViewBase, ViewConfig


# Create a base class for regular models
class Base(DeclarativeBase):
    pass


# Define a regular SQLAlchemy model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


# Define a simple view for active users
class ActiveUserView(ViewBase):
    __tablename__ = "active_users_view"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))

    # Define view configuration
    __view_config__ = ViewConfig(
        definition=select(User.id, User.name, User.email).where(User.active == True),
        # This is a simple (non-materialized) view
        materialized=False,
    )


# Define a materialized view for user emails
class UserEmailView(ViewBase):
    __tablename__ = "user_email_view"

    id = Column(Integer, primary_key=True)
    email = Column(String(100))

    # Define view configuration
    __view_config__ = ViewConfig(
        definition=select(User.id, User.email).select_from(User),
        # This is a materialized view
        materialized=True,
        # Allow concurrent refresh on PostgreSQL
        concurrently=True,
    )


def main():
    # Create a SQLite database engine for demonstration
    db_file = "example.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    engine = create_engine(f"sqlite:///{db_file}", echo=True)

    # Create all tables and views
    Base.metadata.create_all(engine)

    # For ViewBase models, we need to create them separately
    # because they're not attached to Base.metadata
    with engine.begin() as conn:
        for cmd in ActiveUserView.get_create_cmds(engine):
            conn.execute(cmd)

    for cmd in UserEmailView.get_create_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)

    # Insert sample data
    with Session(engine) as session:
        users = [
            User(name="Alice Smith", email="alice@example.com", active=True),
            User(name="Bob Jones", email="bob@example.com", active=True),
            User(name="Charlie Brown", email="charlie@example.com", active=False),
            User(name="Diana Prince", email="diana@example.com", active=True),
        ]
        session.add_all(users)
        session.commit()

    # Refresh the materialized view to load the data
    for cmd in UserEmailView.get_refresh_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)

    # Query the views
    with Session(engine) as session:
        print("\n== Active Users (from view) ==")
        active_users = session.query(ActiveUserView).all()
        for user in active_users:
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}")

        print("\n== User Emails (from materialized view) ==")
        user_emails = session.query(UserEmailView).all()
        for user in user_emails:
            print(f"ID: {user.id}, Email: {user.email}")

    # Clean up - drop the views
    for cmd in UserEmailView.get_drop_cmds(engine, if_exists=True):
        with engine.begin() as conn:
            conn.execute(cmd)

    for cmd in ActiveUserView.get_drop_cmds(engine, if_exists=True):
        with engine.begin() as conn:
            conn.execute(cmd)

    # Drop the tables
    Base.metadata.drop_all(engine)


if __name__ == "__main__":
    main()
