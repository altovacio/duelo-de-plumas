import asyncio # Import asyncio
from logging.config import fileConfig

# Make sure all SQLAlchemy models are imported before loading Base
# Adust the import path according to your project structure
from backend.models import Base # Import Base from backend/models.py
from backend.fastapi_config import settings # Import settings from backend/fastapi_config.py

from sqlalchemy import pool
# Import create_engine for synchronous operation in migrations
from sqlalchemy import create_engine
# Import create_async_engine and AsyncEngine for the run_migrations_online async part
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# --- MODIFIED: Point to our Base metadata --- 
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# --- ADDED: Get database URL from our settings --- 
db_url = str(settings.DATABASE_URL)
if db_url.startswith("sqlite+aiosqlite"): # Autogenerate doesn't like the async driver part
    db_url_sync = db_url.replace("sqlite+aiosqlite", "sqlite")
elif db_url.startswith("postgresql+asyncpg"): # Autogenerate doesn't like the async driver part
    db_url_sync = db_url.replace("postgresql+asyncpg", "postgresql")
else:
    db_url_sync = db_url # Assume it's already sync or handle other cases
# --- END ADDED ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # --- MODIFIED: Use db_url_sync for offline mode --- 
    # url = config.get_main_option("sqlalchemy.url") # Original line
    url = db_url_sync # Use URL from settings
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # --- ADDED: To support detection of BIGINT etc for SQLite --- 
        render_as_batch=True if url.startswith("sqlite") else False 
    )

    with context.begin_transaction():
        context.run_migrations()

# --- ADDED: Asynchronous online migration function --- 
def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        # --- ADDED: To support detection of BIGINT etc for SQLite --- 
        render_as_batch=True if str(settings.DATABASE_URL).startswith("sqlite") else False
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # --- MODIFIED: Use async engine and connect --- 
    # connectable = engine_from_config( # Original sync engine setup
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    # Create async engine using URL from settings
    connectable = create_async_engine(db_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        # Pass the connection to the synchronous migration function
        await connection.run_sync(do_run_migrations)

    # Dispose the engine
    await connectable.dispose()
# --- END MODIFIED/ADDED ASYNC --- 

# --- MODIFIED: Call the correct online function --- 
if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async online migrations
    asyncio.run(run_migrations_online())
