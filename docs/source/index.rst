SQLAlchemy-ViewORM
===============

A flexible library for defining and managing database views in SQLAlchemy ORM.

.. image:: https://badge.fury.io/py/SQLAlchemy-ViewORM.svg
    :target: https://badge.fury.io/py/SQLAlchemy-ViewORM
    :alt: PyPI version

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: License: MIT

.. image:: https://img.shields.io/pypi/pyversions/SQLAlchemy-ViewORM.svg
    :target: https://pypi.org/project/SQLAlchemy-ViewORM/
    :alt: Python Versions

Overview
--------

SQLAlchemy-ViewORM extends SQLAlchemy's ORM to provide a clean, Pythonic interface for creating and managing database views. It supports:

- **Standard views**: Traditional simple SQL views that execute their query on each access
- **Materialized views**: Views that store their results physically for faster access
- **Table-simulated views**: For databases that don't support views or materialized views
- **Cross-database compatibility**: Works with PostgreSQL, MySQL, SQLite, and more
- **Materialized view emulation**: for DBMSs without materialized views like SQLite,
  for each model you can choose what method to use:
  treat as a simple view or mock by a regular table – useful for tests.
- **Dialect-aware features**: Allows views' queries customisation for each database
- **Type annotations**: Fully typed with mypy support.

Well, I developed the lib for my own needs, because lots of other implementations that I found look too weak, and I strive for flexibility with comprehensive features.

Installation
-----------

.. code-block:: bash

    pip install SQLAlchemy-ViewORM

Quick Example
------------

.. code-block:: python

    from sqlalchemy import Column, Integer, String, select
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

    # Define a view based on the User model
    class ActiveUserView(ViewBase):
        __tablename__ = "active_users_view"

        id = Column(Integer, primary_key=True)
        name = Column(String)
        email = Column(String)

        # Define view configuration
        __view_config__ = ViewConfig(
            # Define the view's query
            definition=select(
                User.id, User.name, User.email
            ).where(User.active == True),

            # Create as materialized view for better performance
            materialized=True,

            # Enable concurrent refresh (PostgreSQL)
            concurrently=True
        )

    # Create the view in the database
    engine = create_engine("postgresql://user:pass@localhost/dbname")
    ActiveUserView.metadata.create_all(engine)

    # Refresh materialized view data
    with engine.begin() as conn:
        for cmd in ActiveUserView.get_refresh_cmds(engine):
            conn.execute(cmd)

Documentation
------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api
   examples
   contributing
   history

Features
--------

View Types
~~~~~~~~~

- **Simple Views**: Standard non-materialized views.

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=False  # Default
      )

- **Materialized Views**: Physically stored query results, in DBMSs that supported materialized views (e.g. PostgreSQL and Oracle), and simple views are used in other cases.

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=True
      )

- **Table Views**: For databases without native materialized view support (like SQLite, MySQL), you easily can emulate them with tables.

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=True,
          materialized_as_table=True  # Use tables to simulate materialized views
      )

Which is pretty helpful when developing apps for Postgres while testing with SQLite.
Frankly speaking, this is why I developed the lib 🙂

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
