import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from src import tables, views
from src.db import sessionmanager
from src.periodic import run_repeated
from src.settings import db_settings


async def periodic_refresh_mv():
    async with sessionmanager.session() as session:
        await views.refresh_all_mv(session)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with sessionmanager.connect() as conn:
            if db_settings.create_all:
                await conn.run_sync(tables.Base.metadata.create_all)
            await views.create_all_mv(conn)

    except asyncio.exceptions.TimeoutError:
        raise ValueError("DB connection timeout")

    run_repeated(periodic_refresh_mv, period=5 * 60)

    yield

    if sessionmanager._engine is not None:
        await sessionmanager.close()


app = FastAPI(
    root_path="/api",
    title="CrossWords Game API",
    summary="",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    lifespan=lifespan,
)
