"""
Configuration and fixtures for pytest.

This file provides common test fixtures and configuration
for testing the SQLAlchemy-ViewORM library.
"""
import os
import tempfile
from typing import Generator, Tuple

import pytest
from sqlalchemy import Boolean, Column, Float, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session

# Import the library components
from sqlalchemy_view_orm import ViewBase, ViewConfig, ViewMethod


# Define a base class for our models
class Base(DeclarativeBase):
    pass


# Define a sample table
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    score = Column(Float, default=0.0)


@pytest.fixture
def sqlite_engine() -> Generator[Engine, None, None]:
    """Create a temporary SQLite database engine for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    engine = create_engine(f"sqlite:///{db_path}")

    # Create tables
    Base.metadata.create_all(engine)

    yield engine

    # Clean up
    engine.dispose()
    os.close(fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_engine() -> Engine:
    """Create an in-memory SQLite database engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(sqlite_engine: Engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture
def sample_users(db_session: Session) -> None:
    """Add sample users to the database."""
    users = [
        User(id=1, name="Alice", email="alice@example.com", active=True, score=10.0),
        User(id=2, name="Bob", email="bob@example.com", active=True, score=5.0),
        User(
            id=3, name="Charlie", email="charlie@example.com", active=False, score=8.0
        ),
        User(id=4, name="Diana", email="diana@example.com", active=True, score=0.0),
    ]
    db_session.add_all(users)
    db_session.commit()


@pytest.fixture
def setup_and_teardown_view(
    sqlite_engine: Engine,
) -> Generator[Tuple[ViewBase, Engine], None, None]:
    """
    Generic fixture to set up and tear down a view for testing.

    Usage:
        def test_something(setup_and_teardown_view):
            view_class, engine = setup_and_teardown_view(MyViewClass)
            # Test code here...
    """

    def _setup_and_teardown(
        view_class: type[ViewBase],
    ) -> Generator[Tuple[type[ViewBase], Engine], None, None]:
        # Create the view
        with sqlite_engine.begin() as conn:
            for cmd in view_class.get_create_cmds(sqlite_engine):
                conn.execute(cmd)

        yield view_class, sqlite_engine

        # Drop the view
        with sqlite_engine.begin() as conn:
            for cmd in view_class.get_drop_cmds(sqlite_engine, if_exists=True):
                conn.execute(cmd)

    return _setup_and_teardown
