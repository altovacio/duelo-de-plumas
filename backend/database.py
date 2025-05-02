from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

# Import settings from the config file within the v2 directory
from .fastapi_config import settings
from .models import Base # Import Base from v2/models.py

# Create the async engine using the DATABASE_URL from settings
# Ensure echo=True only for debugging if needed
async_engine = create_async_engine(
    str(settings.DATABASE_URL), # Use the validated URL from settings
    echo=settings.DEBUG, # Log SQL queries only if DEBUG is True
    pool_pre_ping=True, # Check connections before use
    # pool_size=10, # Example: Configure pool size if needed
    # max_overflow=20 # Example: Configure max overflow
)

# Create an async session factory bound to the engine
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    autoflush=False, # Recommended default for async sessions
    expire_on_commit=False, # Recommended default for async/FastAPI
    class_=AsyncSession
)

# Dependency function to get an async database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async SQLAlchemy session per request."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            # Optional: commit here if you want automatic commit per request
            # await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # The session is automatically closed by the context manager
            pass

# Optional: Function to initialize the database (create tables)
# Useful for initial setup or testing, but migrations (Alembic) are preferred for production
async def init_db():
    async with async_engine.begin() as conn:
        # Drop and recreate tables (Use with caution!)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

# Example of running init_db (can be run from a script or CLI)
# if __name__ == "__main__":
#     import asyncio
#     print("Initializing database...")
#     asyncio.run(init_db())
#     print("Database initialization complete.") 