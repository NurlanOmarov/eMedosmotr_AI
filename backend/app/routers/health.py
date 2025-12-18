"""
Health check endpoints
Проверка работоспособности API
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.utils.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Базовая проверка работоспособности
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """
    Проверка подключения к базе данных
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {
            "status": "healthy",
            "database": "connected",
            "message": "База данных доступна"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/health/ai")
async def health_check_ai():
    """
    Проверка конфигурации AI
    """
    has_api_key = bool(settings.OPENAI_API_KEY)

    return {
        "status": "configured" if has_api_key else "not_configured",
        "model": settings.AI_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "api_key_configured": has_api_key
    }
