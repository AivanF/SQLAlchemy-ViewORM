# FastAPI Example with SQLAlchemy-ViewORM

This example demonstrates how to integrate SQLAlchemy-ViewORM with FastAPI for an efficient, async-friendly leaderboard service using materialized views.

## Overview

This example showcases a game leaderboard system that:

1. Uses SQLAlchemy-ViewORM for creating and managing materialized views
2. Leverages FastAPI's async capabilities for high-performance API endpoints
3. Implements periodic refresh of materialized views in the background
4. Handles dialect-specific SQL between different database engines (PostgreSQL/SQLite)

## Project Structure

- `src/`
  - `main.py` - FastAPI application setup
  - `db.py` - Database connection management
  - `tables.py` - Base table definitions
  - `views.py` - Materialized view definition and refresh logic
  - `periodic.py` - Background task scheduling
  - `settings.py` - Application configuration

## Key Components

### Materialized View Definition

The `LeaderboardMV` class in `views.py` defines a materialized view that calculates player rankings based on game results:

```python
class LeaderboardMV(ViewBase):
    __tablename__ = "leaderboard_mv"
    __view_config__ = ViewConfig(
        definer=get_leaderboard_select,
        materialized=True,
        materialized_as_table=True,  # For SQLite compatibility
    )

    # View columns...
```

### Database Dialect Handling

The view definition automatically adapts to different database dialects:

```python
def get_leaderboard_select(dialect_name: str):
    if "sqlite" in dialect_name:
        # SQLite-specific date handling
        filters = [
            GameMatch.created >= func.date(func.now(), f"-{int(LB_DAYS)} days"),
            GameMatch.finished == True,
        ]
    else:
        # PostgreSQL-style interval
        filters = [
            GameMatch.created >= func.now() - text(f"INTERVAL '{LB_DAYS} days'"),
            GameMatch.finished == True,
        ]
    # Query definition...
```

### Async View Management

The example provides async helper functions for creating, dropping, and refreshing views:

```python
async def create_all_mv(conn: AsyncConnection):
    for view_cls in ViewBase.get_children():
        for cmd in view_cls.get_create_cmds(conn.engine):
            await conn.execute(cmd)
```

### Periodic Refresh

A background task refreshes the materialized view periodically:

```python
# In main.py
run_repeated(periodic_refresh_mv, period=5 * 60)  # Refresh every 5 minutes

# In periodic.py
async def run_repeated(func, period):
    while True:
        try:
            await func()
        except Exception as e:
            logger.error(f"Error in periodic task: {e}")
        await asyncio.sleep(period)
```

## Omitted Parts

For brevity, this example omits several components you would typically include in a production application:

1. **API Endpoints** - The actual FastAPI route handlers are not included. In a real application, you would define endpoints to query the leaderboard, e.g.:
   ```python
   @app.get("/leaderboard", response_model=List[LeaderboardEntrySchema])
   async def get_leaderboard(limit: int = 10, session: AsyncSession = Depends(get_session)):
       query = select(LeaderboardMV).limit(limit)
       result = await session.execute(query)
       return result.scalars().all()
   ```

2. **Pydantic Models** - Response/request models using Pydantic are not defined but would be important in a complete API

3. **Authentication/Authorization** - User authentication and permission checks are not implemented

4. **Full Error Handling** - Comprehensive error handling and validation would be needed in production

5. **Logging Configuration** - A proper logging setup would be essential for monitoring

6. **Tests** - Unit and integration tests would be crucial for a production application

7. **Migrations** - Database migration scripts for schema evolution

## Performance Benefits

Using materialized views provides significant performance benefits for complex queries:

- **Precomputed Results**: The expensive leaderboard calculation is performed once during refresh rather than on every request
- **Optimal Query Planning**: Database engines can optimize the materialized data for faster retrieval
- **Reduced Load**: Database load is distributed more evenly through periodic refreshes instead of on-demand calculations
- **Faster Response Times**: API endpoints can serve results with minimal processing
