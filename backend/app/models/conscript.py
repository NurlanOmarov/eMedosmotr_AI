"""
Модели призывников
Основные таблицы для хранения информации о призывниках
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Text, Date, DateTime, Integer, Numeric,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.utils.database import Base


class Conscript(Base):
    """
    Призывники - главная таблица
    Хранит базовую информацию о призывнике
    """
    __tablename__ = "conscripts"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Основные данные
    iin: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=False)

    # Контактные данные
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))

    # Фото
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    specialist_examinations: Mapped[list["SpecialistExamination"]] = relationship(
        "SpecialistExamination",
        back_populates="conscript",
        cascade="all, delete-orphan"
    )
    anthropometric_data: Mapped[Optional["AnthropometricData"]] = relationship(
        "AnthropometricData",
        back_populates="conscript",
        cascade="all, delete-orphan",
        uselist=False
    )
    ai_analysis_results: Mapped[list["AIAnalysisResult"]] = relationship(
        "AIAnalysisResult",
        back_populates="conscript",
        cascade="all, delete-orphan"
    )
    ai_final_verdict: Mapped[Optional["AIFinalVerdict"]] = relationship(
        "AIFinalVerdict",
        back_populates="conscript",
        cascade="all, delete-orphan",
        uselist=False
    )
    erdb_diagnoses: Mapped[list["ErdbDiagnosisHistory"]] = relationship(
        "ErdbDiagnosisHistory",
        back_populates="conscript",
        cascade="all, delete-orphan"
    )
    bureau_hospitalizations: Mapped[list["BureauHospitalization"]] = relationship(
        "BureauHospitalization",
        back_populates="conscript",
        cascade="all, delete-orphan"
    )
    ersb_history: Mapped[list["ErsbHistory"]] = relationship(
        "ErsbHistory",
        back_populates="conscript",
        cascade="all, delete-orphan"
    )
    special_statuses: Mapped[Optional["ErdbSpecialStatus"]] = relationship(
        "ErdbSpecialStatus",
        back_populates="conscript",
        cascade="all, delete-orphan",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<Conscript(iin={self.iin}, name={self.last_name} {self.first_name})>"

class AnthropometricData(Base):
    """
    Антропометрические данные
    Физические измерения призывника
    """
    __tablename__ = "anthropometric_data"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # Физические измерения
    height: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))  # см
    weight: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))  # кг
    bmi: Mapped[Optional[float]] = mapped_column(Numeric(4, 2))     # ИМТ - рассчитывается автоматически триггером БД
    chest_circumference: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    head_circumference: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    # Зрение
    visual_acuity_left: Mapped[Optional[str]] = mapped_column(String(10))
    visual_acuity_right: Mapped[Optional[str]] = mapped_column(String(10))

    # Давление
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)

    # Метаданные
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    measured_by: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="anthropometric_data",
        foreign_keys=[conscript_draft_id]
    )

    def __repr__(self) -> str:
        return f"<AnthropometricData(height={self.height}, weight={self.weight}, bmi={self.bmi})>"


# Импорты для forward references
from app.models.medical import (
    ErdbDiagnosisHistory,
    BureauHospitalization,
    ErsbHistory,
    ErdbSpecialStatus,
    SpecialistExamination,
    InstrumentalExamResult
)
from app.models.reference import CategoryGraph, CategoryDictionary
from app.models.ai import (
    AIAnalysisResult,
    AIFinalVerdict,
    AIAnalysisFeedback
)
from app.models.system import AIRequestLog
