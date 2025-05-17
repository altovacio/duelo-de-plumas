import asyncio
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from alembic import context

# Import all models to ensure they're registered with Base.metadata
from app.db.models.user import User
from app.db.models.text import Text
from app.db.models.contest import Contest
from app.db.models.contest_text import ContestText
from app.db.models.contest_judge import ContestJudge
from app.db.models.vote import Vote
from app.db.models.agent import Agent
from app.db.models.agent_execution import AgentExecution
from app.db.models.credit_transaction import CreditTransaction

from app.db.database import Base
from app.core.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Update db URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """Run migrations in a transaction."""
    context.configure(connection=connection, target_metadata=target_metadata)
    context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    # Create async engine using the DATABASE_URL from settings
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    import sys
    if "pytest" in sys.modules:
        # When pytest (with pytest-asyncio) is running, an event loop is active.
        # Alembic's synchronous commands (called from async pytest fixtures) load this env.py.
        # We must avoid calling asyncio.run() again.
        # Instead, perform migrations using a synchronous SQLAlchemy engine connection.
        print("INFO [migrations/env.py]: Pytest detected, using synchronous engine for migrations.")
        
        # Construct a synchronous database URL (e.g., remove "+asyncpg")
        sync_db_url = settings.DATABASE_URL # This is DATABASE_URL_TEST due to override in conftest
        if "+asyncpg" in sync_db_url:
            sync_db_url = sync_db_url.replace("+asyncpg", "")
            print(f"INFO [migrations/env.py]: Using synchronous DB URL: {sync_db_url}")
        
        sync_engine = create_engine(sync_db_url) # Use regular SQLAlchemy sync engine with a sync dialect URL
        with sync_engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            # Explicitly begin transaction if do_run_migrations doesn't manage it for sync context
            with context.begin_transaction(): 
                context.run_migrations() # This calls do_run_migrations internally
        sync_engine.dispose()
        print("INFO [migrations/env.py]: Synchronous migrations completed for pytest.")
    else:
        # Standard CLI execution (e.g. "alembic upgrade head")
        print("INFO [migrations/env.py]: Standard CLI execution, using asyncio.run() for migrations.")
        asyncio.run(run_migrations_online()) 