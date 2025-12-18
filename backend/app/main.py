"""
Главное FastAPI приложение для eMedosmotr AI
Точка входа для REST API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.database import engine, Base
from app.routers import criteria, ai_analysis, references, health, examinations, conscripts, validation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle события приложения
    """
    # Startup
    print("🚀 Запуск eMedosmotr AI...")
    print(f"📊 База данных: {settings.POSTGRES_DB}")
    print(f"🤖 AI модель: {settings.AI_MODEL}")

    # Создание таблиц при старте приложения
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы базы данных созданы")

    yield

    # Shutdown
    print("👋 Остановка eMedosmotr AI...")
    await engine.dispose()


# Создание FastAPI приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI система для анализа медицинских заключений призывников",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение роутеров
app.include_router(health.router, tags=["Health"])
app.include_router(criteria.router, prefix="/api/v1/criteria", tags=["Criteria"])
app.include_router(ai_analysis.router, prefix="/api/v1/ai", tags=["AI Analysis"])
app.include_router(references.router, prefix="/api/v1/references", tags=["References"])
app.include_router(examinations.router, prefix="/api/v1", tags=["Examinations"])
app.include_router(conscripts.router, tags=["Conscripts"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["Validation"])


@app.get("/")
async def root():
    """
    Корневой endpoint
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "ai_model": settings.AI_MODEL
    }


@app.get("/api/v1/info")
async def api_info():
    """
    Информация об API
    """
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_model": settings.AI_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "rag_enabled": True,
        "endpoints": {
            "criteria": "/api/v1/criteria",
            "ai_analysis": "/api/v1/ai",
            "references": "/api/v1/references",
            "validation": "/api/v1/validation",
            "health": "/health"
        }
    }
