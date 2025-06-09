============
Installation
============

SQLAlchemy-ViewORM can be installed from PyPI:

.. code-block:: bash

    pip install SQLAlchemy-ViewORM

Requirements
-----------

SQLAlchemy-ViewORM requires:

* Python 3.9+
* SQLAlchemy 2.0.0+

The library is tested against the following databases:

* PostgreSQL 12+
* MySQL 8.0+
* SQLite 3.31.0+

But it should work with other database systems as well, with varying levels of feature support.

Development Installation
-----------------------

To install the development version of SQLAlchemy-ViewORM directly from the GitHub repository:

.. code-block:: bash

    pip install git+https://github.com/AivanF/SQLAlchemy-ViewORM.git

For development purposes, clone the repository and install in development mode:

.. code-block:: bash

    git clone https://github.com/AivanF/sqlalchemy-views.git
    cd sqlalchemy-views
    pip install -e ".[dev]"

This will install all development dependencies, including testing tools.
