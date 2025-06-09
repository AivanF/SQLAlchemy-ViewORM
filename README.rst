SQLAlchemy-ViewORM
===============

A flexible library for defining and managing SQL views, including materialized views, in SQLAlchemy ORM.

|PyPI version| |License: MIT| |Python Versions|

Overview
--------

SQLAlchemy-ViewORM extends SQLAlchemy's ORM to provide a clean, Pythonic interface for creating and managing database views. It supports:

- **Standard views**: Traditional SQL views that execute their query on each access
- **Materialized views**: Views that store their results physically for faster access
- **Table-simulated views**: For databases that don't support views or materialized views
- **Cross-database compatibility**: Works with PostgreSQL, MySQL, SQLite, and more
- **Dialect-aware features**: Uses the most efficient approach for each database

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

Features
--------

View Types
~~~~~~~~~

- **Simple Views**: Standard non-materialized views

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=False  # Default
      )

- **Materialized Views**: Physically stored query results

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=True
      )

- **Table Views**: For databases without native view support

  .. code-block:: python

      __view_config__ = ViewConfig(
          definition=my_select_query,
          materialized=True,
          materialized_as_table=True  # Use tables to simulate materialized views
      )

Cross-Database Support
~~~~~~~~~~~~~~~~~~~~~

The library automatically adapts to the database dialect:

- **PostgreSQL**: Full support for materialized views with concurrent refresh
- **MySQL**: Views and materialized views (as of MySQL 8.0)
- **SQLite**: Simple views and table-simulated materialized views
- **Other Databases**: Functionality based on dialect capabilities

Documentation
------------

For complete documentation, examples, and API reference, visit:
https://github.com/AivanF/SQLAlchemy-ViewORM/docs

License
-------

This project is licensed under the MIT License - see the LICENSE file for details.

.. |PyPI version| image:: https://badge.fury.io/py/SQLAlchemy-ViewORM.svg
   :target: https://badge.fury.io/py/SQLAlchemy-ViewORM
.. |License: MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/SQLAlchemy-ViewORM.svg
   :target: https://pypi.org/project/SQLAlchemy-ViewORM/
