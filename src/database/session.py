"""
TrustAgent.Forensics — Database Session Factory (Phase 4)

Cung cấp AsyncSession cho FastAPI dependency injection.

Chiến lược:
- SQLite + aiosqlite cho dev/test (DATABASE_URL mặc định)
- PostgreSQL 17 + asyncpg cho production (chỉ đổi DATABASE_URL)
- create_tables() chạy lúc startup — tạo bảng nếu chưa có
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from src.config import get_settings
from src.database.models import Base

logger = logging.getLogger(__name__)

# Module-level singletons — khởi tạo khi app start
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    """Tạo engine dựa trên DATABASE_URL trong settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url

        # Chuyển đổi URL sync → async nếu cần
        # (ví dụ: "sqlite:///..." → "sqlite+aiosqlite:///...")
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("sqlite:///") and "+aiosqlite" not in db_url:
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # SQLite cần connect_args để cho phép dùng nhiều threads
        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}

        _engine = create_async_engine(
            db_url,
            echo=False,           # True để debug SQL
            connect_args=connect_args,
        )
        logger.info(f"[DB] Engine tạo thành công: {db_url[:50]}...")

    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Tạo session factory (singleton)."""
    global _session_factory
    if _session_factory is None:
        engine = _get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,   # Giữ objects sau commit (quan trọng)
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def create_tables() -> None:
    """
    Tạo tất cả bảng trong database nếu chưa tồn tại.
    Gọi lúc FastAPI startup (lifespan event).
    """
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("[DB] Bảng đã được tạo/kiểm tra")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency — cung cấp DB session cho mỗi request.

    Dùng trong route:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def dispose_engine() -> None:
    """Đóng engine khi app shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("[DB] Engine đã đóng")
