"""SQLAlchemy-ViewORM.

SQLAlchemy-ViewORM provides a flexible and dialect-aware approach to creating
and managing database views in SQLAlchemy-based applications.

This library extends SQLAlchemy's ORM to support:
- Standard (simple) views
- Materialized views
- Table-simulated views for databases lacking native view support
- Automated view creation, refresh, and cleanup

Main components:
---------------
- ViewBase: Base class for creating view-backed ORM models
- ViewConfig: Configuration class for view creation and management
- ViewMethod: Enumeration of view creation methods

Basic usage:
-----------
```python
from sqlalchemy import Column, Integer, String, select
from sqlalchemy_view_orm import ViewBase, ViewConfig

# Define a view
class UserEmailView(ViewBase):
    __tablename__ = "user_email_view"

    id = Column(Integer, primary_key=True)
    email = Column(String)

    # Define view configuration
    __view_config__ = ViewConfig(
        definition=select(User.id, User.email).select_from(User),
        materialized=True  # Create as materialized view
    )
```

For more examples and usage details, see the documentation.
"""

from sqlalchemy_view_orm.base import ViewBase, ViewConfig, ViewMethod

__version__ = "0.1.1"
__author__ = "AivanF."

__all__ = ["ViewBase", "ViewConfig", "ViewMethod"]
