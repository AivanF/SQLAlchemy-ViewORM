# SQLAlchemy-ViewORM

A flexible library for defining and managing SQL views, including materialized views, in SQLAlchemy ORM.

[![PyPI version](https://badge.fury.io/py/SQLAlchemy-ViewORM.svg)](https://badge.fury.io/py/SQLAlchemy-ViewORM)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/SQLAlchemy-ViewORM.svg)](https://pypi.org/project/SQLAlchemy-ViewORM/)
[![Tests](https://github.com/AivanF/SQLAlchemy-ViewORM/actions/workflows/python-package.yml/badge.svg)](https://github.com/AivanF/SQLAlchemy-ViewORM/actions/workflows/python-package.yml)

## Overview

SQLAlchemy ViewORM extends SQLAlchemy's ORM to provide a clean, Pythonic interface for creating and managing database views. It supports:

- **Standard views**: Traditional simple SQL views that execute their query on each access
- **Materialized views**: Views that store their results physically for faster access
- **Table-simulated views**: For databases that don't support views or materialized views
- **Cross-database compatibility**: Works with PostgreSQL, MySQL, SQLite, and more
- **Materialized view emulation**: for DBMSs without materialized views support like SQLite,
  you can choose what method to use for each model:
  treat as a simple view or mock by a regular table – useful for tests.
- **Dialect-aware features**: Allows views' queries customisation for each database
- **Type annotations**: Fully typed with mypy support.

Well, I developed the lib for my own needs, because lots of other implementations that I found look too weak, and I strive for flexibility with comprehensive features.

## Installation

```bash
pip install SQLAlchemy-ViewORM
```

## Quick Example

```python
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
```

## Features

### View Types

- **Simple Views**: Standard non-materialized views.
  ```python
  __view_config__ = ViewConfig(
      definition=my_select_query,
      materialized=False  # Default
  )
  ```

- **Materialized Views**: Physically stored query results, in DBMSs that supported materialized views (e.g. PostgreSQL and Oracle), and simple views are used in other cases.
  ```python
  __view_config__ = ViewConfig(
      definition=my_select_query,
      materialized=True
  )
  ```

- **Table Views**: For databases without native materialized view support (like SQLite, MySQL), you easily can emulate them with tables.
  ```python
  __view_config__ = ViewConfig(
      definition=my_select_query,
      materialized=True,
      materialized_as_table=True  # Use tables to simulate materialized views
  )
  ```

Which is pretty helpful when developing apps for Postgres while testing with SQLite. Frankly speaking, this is why I developed the lib 🙂

### Advanced Usage

Define views with dynamic queries to adjust by considering database dialect:

```python
def build_query(dialect):
    # Adapt the query based on the database dialect
    if dialect == 'postgresql':
        return select(User.id, func.lower(User.email).label('email'))
    else:
        # Simpler version for other databases
        return select(User.id, User.email)

class UserEmailView(ViewBase):
    __tablename__ = "user_email_view"

    id = Column(Integer, primary_key=True)
    email = Column(String)

    __view_config__ = ViewConfig(
        definer=build_query,  # Pass a function instead of a fixed query
        materialized=True
    )
```

## Why Use SQLAlchemy ViewORM?

Database views offer numerous advantages:

1. **Abstraction**: Hide complex queries behind simple interfaces
2. **Performance**: Materialized views improve query speed for complex calculations
3. **Consistency**: Ensure the same ORM-based query logic is used across your application
4. **Security**: Restrict access to sensitive data

This library makes it easy to leverage these benefits within your SQLAlchemy applications.

## Documentation

For complete documentation, examples, and API reference, visit:
[https://github.com/AivanF/SQLAlchemy-ViewORM/docs](https://github.com/AivanF/SQLAlchemy-ViewORM/docs)

## Project Status

This project is in passive development. We welcome contributions, bug reports, and feature requests, especially with suggested solutions. See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

Full documentation is available in the [docs](https://github.com/AivanF/SQLAlchemy-ViewORM/tree/main/docs) directory.

## Examples

Check out the [examples](https://github.com/AivanF/SQLAlchemy-ViewORM/tree/main/examples) directory for complete working code:

- `basic_example.py`: Simple view usage with SQLite
- `advanced_example.py`: Complex views with dialect-specific features
- `flask_example.py`: Integration with Flask web applications
- `FastAPI-example/`: Deeper example with async FastAPI web applications and updates

## Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# With coverage
pytest --cov=sqlalchemy_view_orm
```

## Author

- **AivanF** - [GitHub Profile](https://github.com/AivanF)
