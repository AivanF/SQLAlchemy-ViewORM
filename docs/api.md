# SQLAlchemy-ViewORM API Reference

This document provides a comprehensive reference for the SQLAlchemy-ViewORM library API.

## Core Components

### ViewBase

`ViewBase` is the primary base class for creating view-backed ORM models. It extends SQLAlchemy's `DeclarativeBase` and provides methods for creating, managing, and refreshing database views.

#### Class Attributes

- `__abstract__`: Set to `True`, indicating this is an abstract base class.
- `__view_config__`: Required instance of `ViewConfig` that defines the view's configuration.

#### Class Methods

##### `get_children()`

Returns a list of all view classes that inherit from this base class.

**Returns**: `list[ViewBase]` - List of view class objects.

##### `get_column_names()`

Returns a list of column names defined in the view.

**Returns**: `list[str]` - List of column names.

##### `get_method(dialect_name: str)`

Determines the appropriate view creation method based on the database dialect and configuration.

**Parameters**:
- `dialect_name`: Name of the SQLAlchemy dialect (e.g., 'postgresql', 'sqlite').

**Returns**: `ViewMethod` - The method to use for creating the view.

##### `get_create_cmds(engine: Engine, or_replace=False, if_not_exists=True, options=None)`

Generates SQL commands to create the view in the database.

**Parameters**:
- `engine`: SQLAlchemy Engine instance providing the dialect.
- `or_replace`: If True, replace the view if it exists (not supported by all dialects).
- `if_not_exists`: If True, only create the view if it doesn't already exist.
- `options`: Optional dict of view-specific options (dialect-dependent).

**Returns**: Generator yielding SQLAlchemy `Executable` objects representing the commands.

##### `get_drop_cmds(engine: Engine, cascade=False, if_exists=False)`

Generates SQL commands to drop the view from the database.

**Parameters**:
- `engine`: SQLAlchemy Engine instance providing the dialect.
- `cascade`: If True, drop dependent objects as well.
- `if_exists`: If True, only attempt to drop the view if it exists.

**Returns**: Generator yielding SQLAlchemy `Executable` objects representing the commands.

##### `get_refresh_cmds(engine: Engine)`

Generates SQL commands to refresh the view's data.

**Parameters**:
- `engine`: SQLAlchemy Engine instance providing the dialect.

**Returns**: Generator yielding SQLAlchemy `Executable` objects representing the commands.

### ViewConfig

`ViewConfig` is a dataclass that holds configuration options for a view.

#### Attributes

- `definition`: A SQLAlchemy `Selectable` object representing the view's query.
- `definer`: A callable that returns a `Selectable` based on the dialect name.
- `method`: Optional `ViewMethod` to explicitly set the view creation method.
- `materialized`: Boolean indicating if the view should be materialized (default: False).
- `materialized_as_table`: Boolean indicating if a materialized view should be simulated as a table (default: False).
- `concurrently`: Boolean indicating if a materialized view should be refreshed concurrently (PostgreSQL only, default: False).

#### Methods

##### `get_definition(dialect)`

Returns the view's definition based on the configured definition or definer.

**Parameters**:
- `dialect`: SQLAlchemy dialect object.

**Returns**: SQLAlchemy `Selectable` representing the view's query.

**Raises**: `ValueError` if no definition is available.

### ViewMethod

`ViewMethod` is an enumeration of the possible methods for creating database views.

#### Values

- `SIMPLE`: Standard non-materialized view.
- `MATERIALIZED`: Materialized view that stores data physically.
- `TABLE`: Regular table, used to simulate materialized views when not supported.

## Usage Examples

### Creating a Simple View

```python
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy_view_orm import ViewBase, ViewConfig

# Define a regular model
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    active = Column(Boolean, default=True)

# Define a view
class ActiveUserView(ViewBase):
    __tablename__ = "active_users_view"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    __view_config__ = ViewConfig(
        definition=select(User.id, User.name).where(User.active == True)
    )
```

### Creating a Materialized View

```python
class UserEmailView(ViewBase):
    __tablename__ = "user_email_view"

    id = Column(Integer, primary_key=True)
    email = Column(String)

    __view_config__ = ViewConfig(
        definition=select(User.id, User.email),
        materialized=True,  # Create as materialized view
        concurrently=True   # Enable concurrent refresh on PostgreSQL
    )
```

### Creating Database Views

```python
# Create engine
engine = create_engine("postgresql://user:pass@localhost/dbname")

# Create all tables (for regular models)
Base.metadata.create_all(engine)

# Create views
with engine.begin() as conn:
    for cmd in ActiveUserView.get_create_cmds(engine):
        conn.execute(cmd)

for cmd in UserEmailView.get_create_cmds(engine):
    with engine.begin() as conn:
        conn.execute(cmd)
```

### Refreshing Materialized Views

```python
# Refresh materialized view
for cmd in UserEmailView.get_refresh_cmds(engine):
    with engine.begin() as conn:
        conn.execute(cmd)
```

### Dropping Views

```python
# Drop views
for cmd in UserEmailView.get_drop_cmds(engine, if_exists=True):
    with engine.begin() as conn:
        conn.execute(cmd)

for cmd in ActiveUserView.get_drop_cmds(engine, if_exists=True):
    with engine.begin() as conn:
        conn.execute(cmd)
```

## Implementation Details

### Dialect-Specific Behavior

SQLAlchemy-ViewORM adapts its behavior based on the database dialect:

- **PostgreSQL**: Full support for materialized views with concurrent refresh
- **MySQL**: Supports both simple and materialized views
- **SQLite**: Only supports simple views or table-simulated materialized views
- **Other Dialects**: Feature support varies by dialect capabilities

### Materialized Views

For databases that support materialized views (like PostgreSQL):
- Views are created with `CREATE MATERIALIZED VIEW`
- Refreshed with `REFRESH MATERIALIZED VIEW`
- Concurrent refresh is available via the `concurrently` option

For databases without native materialized view support:
- When `materialized_as_table=True`, creates a regular table
- Refreshes by deleting all rows and re-inserting from the view definition
