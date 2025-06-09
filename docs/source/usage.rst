=====
Usage
=====

This guide will walk you through the key components and usage patterns of SQLAlchemy-ViewORM.

Basic Concepts
-------------

SQLAlchemy-ViewORM extends SQLAlchemy's ORM with specialized classes for creating and managing database views:

* ``ViewBase``: A base class for creating view-backed ORM models
* ``ViewConfig``: A configuration class for defining view properties
* ``ViewMethod``: An enumeration of view creation methods (SIMPLE, MATERIALIZED, TABLE)

Creating Views
-------------

To create a view, define a class that inherits from ``ViewBase`` and includes a ``__view_config__`` attribute:

.. code-block:: python

    from sqlalchemy import Column, Integer, String, Boolean, select
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy_view_orm import ViewBase, ViewConfig

    # Regular SQLAlchemy model
    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        email = Column(String)
        active = Column(Boolean, default=True)

    # Define a view class
    class ActiveUserView(ViewBase):
        __tablename__ = "active_users_view"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        email = Column(String)

        # Define view configuration
        __view_config__ = ViewConfig(
            definition=select(
                User.id, User.name, User.email
            ).where(User.active == True)
        )

The ``__view_config__`` attribute takes several parameters:

* ``definition``: A SQLAlchemy ``select()`` statement defining the view's query
* ``definer``: Alternative to ``definition``; a function that returns a query based on dialect
* ``materialized``: Boolean indicating if the view should be materialized
* ``materialized_as_table``: Boolean to use tables to simulate materialized views
* ``concurrently``: Boolean enabling concurrent refresh for PostgreSQL

Creating View Instances in the Database
--------------------------------------

Unlike regular SQLAlchemy models, view-backed models need explicit creation:

.. code-block:: python

    from sqlalchemy import create_engine

    # Create database engine
    engine = create_engine("postgresql://user:pass@localhost/dbname")

    # Create regular tables
    Base.metadata.create_all(engine)

    # Create views
    with engine.begin() as conn:
        for cmd in ActiveUserView.get_create_cmds(engine):
            conn.execute(cmd)

You can customize view creation with options:

.. code-block:: python

    # Create with additional options
    for cmd in ActiveUserView.get_create_cmds(
        engine,
        or_replace=True,  # Use CREATE OR REPLACE (where supported)
        if_not_exists=True,  # Use IF NOT EXISTS
        options={"security_barrier": True}  # View-specific options
    ):
        with engine.begin() as conn:
            conn.execute(cmd)

Working with Views
-----------------

Once created, you can use view-backed models like any SQLAlchemy model:

.. code-block:: python

    from sqlalchemy.orm import Session

    # Query the view
    with Session(engine) as session:
        active_users = session.query(ActiveUserView).all()
        for user in active_users:
            print(f"ID: {user.id}, Name: {user.name}")

Materialized Views
-----------------

For materialized views, you need to explicitly refresh the data:

.. code-block:: python

    # Define a materialized view
    class UserScoreView(ViewBase):
        __tablename__ = "user_scores_view"

        id = Column(Integer, primary_key=True)
        score = Column(Float)

        __view_config__ = ViewConfig(
            definition=select(User.id, User.score).where(User.score > 0),
            materialized=True,
            concurrently=True  # PostgreSQL only
        )

    # Create the view
    for cmd in UserScoreView.get_create_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)

    # Refresh the view after data changes
    for cmd in UserScoreView.get_refresh_cmds(engine):
        with engine.begin() as conn:
            conn.execute(cmd)

Dialect-Specific Definitions
---------------------------

You can create dialect-specific view definitions using the ``definer`` parameter:

.. code-block:: python

    def create_query(dialect_name):
        if dialect_name == 'postgresql':
            # Use PostgreSQL-specific features
            return select(
                User.id,
                func.lower(User.email).label('email'),
                func.rank().over(
                    order_by=User.score.desc()
                ).label('rank')
            )
        else:
            # Simpler version for other databases
            return select(
                User.id,
                func.lower(User.email).label('email'),
                literal(0).label('rank')
            )

    class UserRankView(ViewBase):
        __tablename__ = "user_rank_view"

        id = Column(Integer, primary_key=True)
        email = Column(String)
        rank = Column(Integer)

        __view_config__ = ViewConfig(
            definer=create_query,
            materialized=True
        )

Dropping Views
-------------

To remove views from the database:

.. code-block:: python

    # Drop a view
    for cmd in ActiveUserView.get_drop_cmds(
        engine,
        cascade=False,  # Set to True to cascade to dependent objects
        if_exists=True  # Only attempt to drop if the view exists
    ):
        with engine.begin() as conn:
            conn.execute(cmd)

Best Practices
-------------

1. **Column Matching**: Ensure the columns in your view class match the columns in your view definition.

2. **Refreshing Strategy**: For materialized views, develop a strategy for when to refresh them.

3. **Database Compatibility**: Be aware of dialect differences when working with multiple database systems.

4. **Error Handling**: Wrap view operations in try/except blocks to handle database-specific errors.

5. **Transactions**: Use transactions for view operations to ensure atomicity.

Example:

.. code-block:: python

    try:
        # Create view in a transaction
        with engine.begin() as conn:
            for cmd in ActiveUserView.get_create_cmds(engine, if_not_exists=True):
                conn.execute(cmd)
    except Exception as e:
        print(f"Error creating view: {e}")

More Examples
-------------

1. `Flask server <https://github.com/AivanF/SQLAlchemy-ViewORM/blob/main/examples/flask_example.py>`_
  - single-file server
  - Materialized View integrated into API
  - refresh by request

2. `FastAPI server <https://github.com/AivanF/SQLAlchemy-ViewORM/tree/main/examples/FastAPI-example>`_
  - multiple-file server draft
  - Materialized View + async DB proper setup
  - refresh by a background job
