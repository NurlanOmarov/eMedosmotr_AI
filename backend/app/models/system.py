"""
Системные модели
Логи, настройки и служебные таблицы
"""

import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    String, Text, Integer, Float, DateTime, Numeric,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class AIRequestLog(Base):
    """
    Логи AI-запросов
    Хранит историю всех обращений к AI для анализа и отладки
    """
    __tablename__ = "ai_request_logs"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id"),
        index=True
    )

    # Тип запроса
    request_type: Mapped[Optional[str]] = mapped_column(String(50))

    # Модель
    model_used: Mapped[Optional[str]] = mapped_column(String(100))

    # Токены
    tokens_prompt: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_completion: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_total: Mapped[Optional[int]] = mapped_column(Integer)

    # Стоимость
    cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))

    # Производительность
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Статус
    status: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        index=True
    )

    # Relationships
    conscript: Mapped[Optional["Conscript"]] = relationship(
        "Conscript",
        foreign_keys=[conscript_draft_id]
    )

    def __repr__(self) -> str:
        return f"<AIRequestLog(type={self.request_type}, model={self.model_used}, status={self.status})>"


class SystemSetting(Base):
    """
    Настройки системы
    Хранит конфигурационные параметры приложения
    """
    __tablename__ = "system_settings"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Ключ и значение
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Тип и описание
    setting_type: Mapped[Optional[str]] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.setting_key}, value={self.setting_value})>"


# Импорты для forward references
from app.models.conscript import Conscript
