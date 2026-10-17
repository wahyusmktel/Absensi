"""
Konfigurasi koneksi database PostgreSQL dengan SQLAlchemy Asynchronous & Synchronous.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Engine database asynchronous (asyncpg) untuk performa super cepat
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # Memastikan koneksi valid sebelum digunakan
)

# Pabrik sesi database asynchronous
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class untuk seluruh ORM model
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator untuk mendapatkan sesi database per-request.
    Secara otomatis menutup sesi ketika request selesai.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
