import contextlib
from typing import Any, AsyncIterator

import sqlalchemy.pool
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.settings import db_settings

if "sqlite" in db_settings.protocol:
    poolclass = sqlalchemy.pool.StaticPool
    if db_settings.file:
        DATABASE_URL = f"{db_settings.protocol}:///{db_settings.file}"
    else:
        DATABASE_URL = f"{db_settings.protocol}:///:memory:"
else:
    poolclass = sqlalchemy.pool.AsyncAdaptedQueuePool
    DATABASE_URL = f"{db_settings.protocol}://{db_settings.user}:{db_settings.pw}@{db_settings.host}:{db_settings.port}/{db_settings.name}"


class DatabaseSessionManager:
    def __init__(self, database_url: str, **engine_kwargs: dict[str, Any]):
        self._engine = create_async_engine(database_url, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            expire_on_commit=False,
        )

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(
    DATABASE_URL,
    # echo=True,  # print SQL
    connect_args={
        # "server_settings": {},
        "timeout": db_settings.connect_timeout,
    },
    poolclass=poolclass,
)


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session
