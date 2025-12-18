"""
Утилиты для работы с базой данных
Подключение, сессии, зависимости
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Создание async движка БД
engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool if settings.ENVIRONMENT == "development" else None,
    echo=settings.DEBUG,
)

# Создание фабрики async сессий
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Базовый класс для моделей
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency для получения сессии БД
    Используется в FastAPI endpoints
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise


def init_db():
    """
    Инициализация базы данных
    Создание всех таблиц (для разработки)
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized successfully")


def drop_db():
    """
    Удаление всех таблиц (для тестирования)
    """
    logger.warning("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("✅ All tables dropped")
