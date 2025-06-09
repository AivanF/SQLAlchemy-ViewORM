"""SQLAlchemy View ORM implementation.

This module provides classes for creating and managing database views in SQLAlchemy ORM.
It supports standard views, materialized views, and table-simulated views for databases
lacking native view support.
"""

__author__ = "AivanF."

import enum
from dataclasses import dataclass
from typing import Any, Callable, Generator, Optional, Union

from sqlalchemy import Dialect, Executable, Selectable, delete, text
from sqlalchemy.engine import Compiled, Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import CreateColumn
from sqlalchemy.sql.compiler import DDLCompiler

has_matview: set[str] = {"postgresql", "oracle"}
or_replace_table: set[str] = set()
or_replace_view: set[str] = {"postgresql", "oracle", "mysql", "mssql", "sqlite"}
or_replace_matview: set[str] = {"postgresql", "oracle"}


class ViewMethod(str, enum.Enum):
    """Enumeration of view creation methods.

    Defines the possible methods for creating views in a database,
    such as simple views, materialized views, or tables.

    Attributes:
        SIMPLE (str): Represents a simple, non-materialized view.
            Stored as a virtual table that executes the query on access.
        MATERIALIZED (str): Represents a materialized view.
            Stores the query result physically, requiring "manual" refresh.
        TABLE (str): Represents a physical table.
            Used to mock views or materialized views.
    """

    SIMPLE = "simple"
    MATERIALIZED = "materialized"
    TABLE = "table"


@dataclass
class ViewConfig:
    """Settings for creating and managing database views.

    Attributes:
        definition (Selectable):
            A SQLAlchemy Selectable object representing the view's query.
            This query must produce the same columns as the ORM view definition.
            Typically a `select()` statement or equivalent.
        definer (Callable):
            A function that returns a Selectable based on the dialect name.
            Alternative to providing a fixed definition.
        method (Optional[ViewMethod]):
            The method used to create or update the view.
            If None, the default method is inferred
            considering settings and database dialect.
        materialized (bool):
            Whether the view is materialized.
            Materialized views store data physically, improving query performance
            but requiring explicit refresh operations.
            Defaults to False (standard view).
        materialized_as_table (bool):
            Whether to mock a materialized view as a table.
            Useful for DBMSs lacking materialized views support like SQLite or MySQL.
            When True, the view is created as a table with the same structure.
            Defaults to False.
        concurrently (bool):
            Whether to refresh materialized views concurrently.
            Concurrent refresh allows the view to remain accessible during updates
            but requires a unique constraint on the view's data.
            Ignored for simple views or databases without concurrent refresh support.
            Defaults to False.
    """

    definition: Optional[Selectable] = None
    definer: Optional[Callable[[str], Selectable]] = None
    method: Optional[ViewMethod] = None
    materialized: bool = False
    materialized_as_table: bool = False
    concurrently: bool = False

    def get_definition(self, dialect: Dialect) -> Selectable:
        """Get the view definition based on dialect.

        Returns the appropriate definition for the given dialect, using either
        the fixed definition or the dialect-specific definer function.

        Args:
            dialect: SQLAlchemy dialect object

        Returns:
            Selectable: The view definition

        Raises:
            ValueError: If neither definition nor definer is provided
        """
        if self.definition is not None:
            return self.definition
        elif self.definer is not None:
            return self.definer(dialect.name)
        raise ValueError("No definition provided")


class ViewBase(DeclarativeBase):
    """Base class for view-backed ORM models.

    This class extends SQLAlchemy's DeclarativeBase to provide functionality
    for creating, dropping, and refreshing database views. Subclasses must define
    a __view_config__ attribute containing a ViewConfig instance.
    """

    __abstract__ = True
    __view_config__: ViewConfig

    @classmethod
    def get_children(cls) -> list["ViewBase"]:
        """Get all view classes that inherit from this base class.

        Returns:
            list: All view classes in the registry
        """
        return [m.class_ for m in cls.registry.mappers]  # type: ignore

    @classmethod
    def get_column_names(cls) -> list[str]:
        """Get the column names defined in this view.

        Returns:
            list: Names of all columns in the view
        """
        return [c.name for c in cls.__table__.columns]

    @classmethod
    def get_method(cls, dialect_name: str) -> ViewMethod:
        """Determine the view method to use based on dialect and configuration.

        Args:
            dialect_name: Name of the SQLAlchemy dialect

        Returns:
            ViewMethod: The method to use for this view
        """
        if cls.__view_config__.method:
            return cls.__view_config__.method

        if not cls.__view_config__.materialized:
            return ViewMethod.SIMPLE

        if "sqlite" in dialect_name:
            # SQLite has no materialised views.
            if cls.__view_config__.materialized_as_table:
                return ViewMethod.TABLE
            else:
                return ViewMethod.SIMPLE

        else:
            return ViewMethod.MATERIALIZED

    @classmethod
    def get_create_cmds(
        cls,
        engine: Union[Engine, AsyncEngine],
        or_replace: bool = False,
        if_not_exists: bool = True,
        options: Optional[dict[Any, Any]] = None,
    ) -> Generator[Executable, None, None]:
        """Generate commands to create the view.

        Args:
            engine: The SQLAlchemy Engine providing the dialect.
            or_replace: If True, the view's definition will be updated.
                Otherwise, an exception may be raised if the view exists.
                Note that it's not supported by some DBMSs, including Postgres.
            if_not_exists: If True, only create the view if it doesn't already exist.
            options: Specify optional parameters for a view. It translates into
                'WITH ( view_option_name [= view_option_value] [, ... ] )'

        Yields:
            Executable: commands to create the view, 1 pc in most cases.

        Raises:
            ValueError: If the View class has definition errors.
        """
        # dialect = engine.url.get_dialect()
        dialect = engine.dialect
        compiler: DDLCompiler = dialect.ddl_compiler(dialect, None)  # type: ignore
        preparer = compiler.preparer
        method = cls.get_method(dialect.name)

        q = "\nCREATE "

        if method == ViewMethod.SIMPLE:
            if or_replace and dialect.name in or_replace_view:
                q += "OR REPLACE "
            q += "VIEW "
        elif method == ViewMethod.MATERIALIZED:
            if or_replace and dialect.name in or_replace_matview:
                q += "OR REPLACE "
            q += "MATERIALIZED VIEW "
        elif method == ViewMethod.TABLE:
            if or_replace and dialect.name in or_replace_table:
                q += "OR REPLACE "
            q += "TABLE "
        else:
            raise ValueError(f"Got unknown {method=}")

        if if_not_exists:
            q += "IF NOT EXISTS "
        q += preparer.format_table(cls.__table__)

        columns = [
            CreateColumn(column) for column in cls.__table__.columns  # type: ignore
        ]
        if columns:
            column_names = [preparer.format_column(col.element) for col in columns]
            q += "("
            q += ", ".join(column_names)
            q += ") "
        if options:
            ops = []
            for opname, opval in options.items():
                ops.append("=".join([str(opname), str(opval)]))

            q += "WITH (%s) " % (", ".join(ops))

        definition = cls.__view_config__.get_definition(dialect)
        compiled_definition = (
            definition
            if isinstance(definition, Compiled)
            else compiler.sql_compiler.process(definition, literal_binds=True)
        )
        if method != ViewMethod.TABLE:
            q += "AS %s\n\n" % compiled_definition
        yield text(q)

    @classmethod
    def get_drop_cmds(
        cls,
        engine: Union[Engine, AsyncEngine],
        cascade: bool = False,
        if_exists: bool = False,
    ) -> Generator[Executable, None, None]:
        """Generate commands to drop the view.

        Args:
            engine: The SQLAlchemy Engine providing the dialect.
            cascade: Drop dependent views, if any.
            if_exists: Do nothing if the view does not exist.
                Otherwise, an exception may be raised for missing views.

        Yields:
            Executable: commands to drop the view, 1 pc in most cases.

        Raises:
            ValueError: If the View class has definition errors.
        """
        # dialect = engine.url.get_dialect()
        dialect = engine.dialect
        compiler: DDLCompiler = dialect.ddl_compiler(dialect, None)  # type: ignore
        preparer = compiler.preparer
        method = cls.get_method(dialect.name)

        q = "\nDROP "
        if method == ViewMethod.SIMPLE:
            q += "VIEW "
        elif method == ViewMethod.MATERIALIZED:
            q += "MATERIALIZED VIEW "
        elif method == ViewMethod.TABLE:
            q += "TABLE "
        else:
            raise ValueError(f"Got unknown {method=}")

        if if_exists:
            q += "IF EXISTS "

        q += preparer.format_table(cls.__table__)
        if cascade:
            q += " CASCADE"
        yield text(q)

    @classmethod
    def get_refresh_cmds(
        cls, engine: Union[Engine, AsyncEngine]
    ) -> Generator[Executable, None, None]:
        """Generate commands to refresh the view.

        Args:
            engine: The SQLAlchemy Engine providing the dialect.

        Yields:
            Executable: Commands to refresh the view.

        Raises:
            ValueError: If the View class has definition errors.
        """
        dialect = engine.dialect
        method = cls.get_method(engine.url.get_dialect().name)

        if method == ViewMethod.SIMPLE:
            return

        elif method == ViewMethod.MATERIALIZED:
            q = "REFRESH MATERIALIZED VIEW"
            if cls.__view_config__.concurrently:
                q += " CONCURRENTLY"
            q += f" {cls.__table__};"
            yield text(q)

        elif method == ViewMethod.TABLE:
            # Performance issues expected,
            # not recommended for production use!
            yield delete(cls.__table__)  # type: ignore
            yield cls.__table__.insert().from_select(  # type: ignore
                cls.get_column_names(),
                cls.__view_config__.get_definition(dialect),
            )

        else:
            raise ValueError(f"Got unknown {method=}")
