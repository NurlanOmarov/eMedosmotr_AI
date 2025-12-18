"""
Конфигурация приложения eMedosmotr AI
Загрузка настроек из .env файла
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional, List, Union


class Settings(BaseSettings):
    """Настройки приложения"""

    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://admin:secure_password@localhost:5432/emedosmotr"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "secure_password"
    POSTGRES_DB: str = "emedosmotr"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # OpenAI API
    OPENAI_API_KEY: Optional[str] = None

    # Настройки AI
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.0  # Детерминированность - всегда одинаковый результат
    AI_MAX_TOKENS: int = 4000

    # RAG настройки
    RAG_CHUNK_SIZE: int = 1024
    RAG_TOP_K: int = 5
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536

    # Приложение
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "eMedosmotr AI"
    APP_VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]

    # Кэширование
    ENABLE_CACHE: bool = True
    CACHE_TTL_HOURS: int = 24

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Парсинг CORS_ORIGINS из строки с запятыми или списка"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra='ignore'  # Игнорировать неизвестные поля из .env
    )


# Глобальный экземпляр настроек
settings = Settings()
