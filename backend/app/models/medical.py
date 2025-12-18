"""
Медицинские модели
Таблицы для хранения медицинских данных и заключений врачей
"""

import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    String, Text, Date, DateTime, Integer, Boolean, Numeric,
    ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.utils.database import Base


class SpecialistExamination(Base):
    """
    Заключения врачей ВВК
    Результаты медицинского осмотра различными специалистами
    """
    __tablename__ = "specialists_examinations"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    conscript_draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    icd10_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("icd10_codes.id")
    )

    # Специальность врача
    specialty: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    med_commission_member: Mapped[Optional[str]] = mapped_column(String(255))
    doctor_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Данные осмотра
    complain: Mapped[Optional[str]] = mapped_column(Text)
    anamnesis: Mapped[Optional[str]] = mapped_column(Text)
    objective_data: Mapped[Optional[str]] = mapped_column(Text)
    special_research_results: Mapped[Optional[str]] = mapped_column(Text)

    # Заключение и диагноз
    conclusion_text: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis_accompany_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    diagnosis_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Категория
    valid_category: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    category_enum: Mapped[Optional[str]] = mapped_column(String(50))
    additional_act_comment: Mapped[Optional[str]] = mapped_column(Text)

    # Дата обследования
    examination_date: Mapped[date] = mapped_column(Date, nullable=False, default=func.current_date())

    # НОВЫЕ ПОЛЯ для соответствия внешнему API
    # Данные офтальмолога - зрение без коррекции
    os_vision_without_correction: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        comment="Острота зрения левого глаза без коррекции (для офтальмолога)"
    )
    od_vision_without_correction: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        comment="Острота зрения правого глаза без коррекции (для офтальмолога)"
    )

    # Данные стоматолога - зубная формула
    dentist_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment="Зубная формула стоматолога (JSON с ключами 11-48)"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # Векторное представление для RAG
    conclusion_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="specialist_examinations",
        foreign_keys=[conscript_draft_id]
    )
    icd10: Mapped[Optional["ICD10Code"]] = relationship(
        "ICD10Code",
        foreign_keys=[icd10_id]
    )
    ai_analysis_results: Mapped[list["AIAnalysisResult"]] = relationship(
        "AIAnalysisResult",
        back_populates="examination",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SpecialistExamination(specialty={self.specialty}, valid_category={self.valid_category})>"


# Индекс для векторного поиска заключений
Index(
    'idx_examinations_embedding',
    SpecialistExamination.conclusion_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'conclusion_embedding': 'vector_cosine_ops'}
)


class ErdbDiagnosisHistory(Base):
    """
    ЭРДБ - Амбулаторные обращения
    История диспансерного наблюдения и амбулаторных посещений
    """
    __tablename__ = "erdb_diagnoses_history"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Диагноз МКБ-10
    icd10_code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    icd10_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("icd10_codes.id")
    )
    diagnosis_name_ru: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis_name_kz: Mapped[Optional[str]] = mapped_column(Text)

    # Даты наблюдения
    begin_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, index=True)

    # Диспансерный учёт
    d_accounting_group: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    disability_group: Mapped[Optional[str]] = mapped_column(String(10))
    registration_type: Mapped[Optional[str]] = mapped_column(String(100))
    reason_for_withdrawal: Mapped[Optional[str]] = mapped_column(Text)

    # Дополнительные данные
    medical_facility: Mapped[Optional[str]] = mapped_column(String(255))
    doctor_specialty: Mapped[Optional[str]] = mapped_column(String(100))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="erdb_diagnoses"
    )
    icd10: Mapped[Optional["ICD10Code"]] = relationship(
        "ICD10Code",
        foreign_keys=[icd10_id]
    )

    def __repr__(self) -> str:
        return f"<ErdbDiagnosisHistory(icd10_code={self.icd10_code}, group={self.d_accounting_group})>"


# Составной индекс для дат
Index('idx_erdb_dates', ErdbDiagnosisHistory.begin_date, ErdbDiagnosisHistory.end_date)


class BureauHospitalization(Base):
    """
    Бюро госпитализации
    Амбулаторные визиты и оказанные медицинские услуги
    """
    __tablename__ = "bureau_hospitalization"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Данные визита
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    medical_facility: Mapped[Optional[str]] = mapped_column(String(255))
    doctor_specialty: Mapped[Optional[str]] = mapped_column(String(100))

    # Примечания и услуги
    note: Mapped[Optional[str]] = mapped_column(Text)
    used_service: Mapped[Optional[str]] = mapped_column(Text)  # Коды услуг

    # Диагноз
    diagnoses: Mapped[Optional[str]] = mapped_column(String(10))
    icd10_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("icd10_codes.id")
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="bureau_hospitalizations"
    )
    icd10: Mapped[Optional["ICD10Code"]] = relationship(
        "ICD10Code",
        foreign_keys=[icd10_id]
    )

    def __repr__(self) -> str:
        return f"<BureauHospitalization(visit_date={self.visit_date}, diagnoses={self.diagnoses})>"


class ErsbHistory(Base):
    """
    ЭРСБ - Стационарные госпитализации
    История стационарного лечения
    """
    __tablename__ = "ersb_history"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Даты госпитализации
    admission_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    discharge_date: Mapped[Optional[date]] = mapped_column(Date, index=True)

    # Место госпитализации
    hospital_name: Mapped[Optional[str]] = mapped_column(String(255))
    department: Mapped[Optional[str]] = mapped_column(String(255))

    # Диагнозы
    admission_diagnosis: Mapped[Optional[str]] = mapped_column(String(10))
    final_diagnosis: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    final_diagnosis_text: Mapped[Optional[str]] = mapped_column(Text)
    icd10_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("icd10_codes.id")
    )

    # Тип и результат госпитализации
    hospitalization_type: Mapped[Optional[str]] = mapped_column(String(50))
    treatment_outcome: Mapped[Optional[str]] = mapped_column(String(100))
    outcome: Mapped[Optional[str]] = mapped_column(String(100))
    main_surgical_procedure: Mapped[Optional[str]] = mapped_column(Text)

    # Дополнительные данные
    complications: Mapped[Optional[str]] = mapped_column(Text)
    concomitant_diseases: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="ersb_history"
    )
    icd10: Mapped[Optional["ICD10Code"]] = relationship(
        "ICD10Code",
        foreign_keys=[icd10_id]
    )

    def __repr__(self) -> str:
        return f"<ErsbHistory(admission_date={self.admission_date}, final_diagnosis={self.final_diagnosis})>"


class InstrumentalExamResult(Base):
    """
    Результаты инструментальных исследований
    ЭКГ, ЭхоКГ, Рентген, УЗИ и другие
    """
    __tablename__ = "instrumental_exam_results"

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
        nullable=False,
        index=True
    )

    # Тип исследования
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    service_code: Mapped[Optional[str]] = mapped_column(String(50))
    exam_date: Mapped[date] = mapped_column(Date, default=func.current_date())

    # Результаты
    objective_data: Mapped[Optional[str]] = mapped_column(Text)
    special_research_results: Mapped[Optional[str]] = mapped_column(Text)
    result_json: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Заключение
    icd10_code: Mapped[Optional[str]] = mapped_column(String(10))
    icd10_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("icd10_codes.id")
    )
    conclusion_text: Mapped[Optional[str]] = mapped_column(Text)

    # Метаданные
    performed_by: Mapped[Optional[str]] = mapped_column(String(255))
    medical_facility: Mapped[Optional[str]] = mapped_column(String(255))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Векторное представление для RAG
    result_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        foreign_keys=[conscript_draft_id]
    )
    icd10: Mapped[Optional["ICD10Code"]] = relationship(
        "ICD10Code",
        foreign_keys=[icd10_id]
    )

    def __repr__(self) -> str:
        return f"<InstrumentalExamResult(exam_type={self.exam_type}, date={self.exam_date})>"


# Индекс для векторного поиска
Index(
    'idx_instrumental_embedding',
    InstrumentalExamResult.result_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'result_embedding': 'vector_cosine_ops'}
)


class ErdbSpecialStatus(Base):
    """
    Специальные статусы учёта
    Наркология, психиатрия, туберкулёз и т.д.
    """
    __tablename__ = "erdb_special_statuses"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    conscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Статусы учётов
    narcology: Mapped[bool] = mapped_column(Boolean, default=False)
    psychiatry: Mapped[bool] = mapped_column(Boolean, default=False)
    tuberculosis: Mapped[bool] = mapped_column(Boolean, default=False)
    skin_veneral: Mapped[bool] = mapped_column(Boolean, default=False)

    # Детали учётов
    narcology_details: Mapped[Optional[str]] = mapped_column(Text)
    psychiatry_details: Mapped[Optional[str]] = mapped_column(Text)
    tuberculosis_details: Mapped[Optional[str]] = mapped_column(Text)
    skin_veneral_details: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="special_statuses"
    )

    def __repr__(self) -> str:
        statuses = []
        if self.narcology:
            statuses.append("narcology")
        if self.psychiatry:
            statuses.append("psychiatry")
        if self.tuberculosis:
            statuses.append("tuberculosis")
        if self.skin_veneral:
            statuses.append("skin_veneral")
        return f"<ErdbSpecialStatus(statuses={','.join(statuses)})>"


# Импорты для forward references
from app.models.conscript import Conscript
from app.models.reference import ICD10Code
from app.models.ai import AIAnalysisResult
