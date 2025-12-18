"""
AI модели
Таблицы для RAG, анализа и обратной связи
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    ForeignKey, Index, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.utils.database import Base


class AIAnalysisResult(Base):
    """
    Результаты AI-анализа
    Анализ заключения врача с помощью AI
    """
    __tablename__ = "ai_analysis_results"

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
        nullable=False,
        index=True
    )
    examination_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("specialists_examinations.id")
    )

    # Результат по специальности
    specialty: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Выводы
    doctor_category: Mapped[str] = mapped_column(String(10), nullable=False)
    ai_recommended_category: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Детали анализа
    article: Mapped[Optional[int]] = mapped_column(Integer)
    subpoint: Mapped[Optional[str]] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)

    # Технические детали
    model_used: Mapped[Optional[str]] = mapped_column(String(100))
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    analysis_duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Векторное представление для RAG
    reasoning_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="ai_analysis_results",
        foreign_keys=[conscript_draft_id]
    )
    examination: Mapped[Optional["SpecialistExamination"]] = relationship(
        "SpecialistExamination",
        back_populates="ai_analysis_results"
    )
    feedbacks: Mapped[list["AIAnalysisFeedback"]] = relationship(
        "AIAnalysisFeedback",
        back_populates="ai_result",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AIAnalysisResult(specialty={self.specialty}, status={self.status})>"


# Индекс для векторного поиска
Index(
    'idx_ai_results_embedding',
    AIAnalysisResult.reasoning_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'reasoning_embedding': 'vector_cosine_ops'}
)


class AIFinalVerdict(Base):
    """
    Финальный вердикт AI
    Общий вывод по призывнику после анализа всех заключений
    """
    __tablename__ = "ai_final_verdicts"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key (UNIQUE - один вердикт на призывника)
    conscript_draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Рекомендованная категория
    recommended_category: Mapped[str] = mapped_column(String(10), nullable=False)
    recommended_category_enum: Mapped[Optional[str]] = mapped_column(String(50))

    # Статус и риск
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)

    # Сводка
    summary: Mapped[Optional[str]] = mapped_column(Text)

    # Статистика
    total_specialists: Mapped[Optional[int]] = mapped_column(Integer)
    mismatch_count: Mapped[Optional[int]] = mapped_column(Integer)
    analysis_time_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Версия модели
    model_version: Mapped[Optional[str]] = mapped_column(String(50))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Relationships
    conscript: Mapped["Conscript"] = relationship(
        "Conscript",
        back_populates="ai_final_verdict",
        foreign_keys=[conscript_draft_id]
    )

    def __repr__(self) -> str:
        return f"<AIFinalVerdict(category={self.recommended_category}, status={self.status})>"


class AIAnalysisFeedback(Base):
    """
    Обратная связь для обучения AI
    Отзывы экспертов о качестве AI-анализа
    """
    __tablename__ = "ai_analysis_feedback"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    ai_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    conscript_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id")
    )

    # Рецензент
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Решение
    reviewer_decision: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    final_category: Mapped[Optional[str]] = mapped_column(String(10))
    feedback_comment: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Relationships
    ai_result: Mapped["AIAnalysisResult"] = relationship(
        "AIAnalysisResult",
        back_populates="feedbacks"
    )
    conscript: Mapped[Optional["Conscript"]] = relationship(
        "Conscript",
        foreign_keys=[conscript_draft_id]
    )

    def __repr__(self) -> str:
        return f"<AIAnalysisFeedback(decision={self.reviewer_decision})>"


class KnowledgeBaseDocument(Base):
    """
    База знаний для RAG
    Документы Приказа 722 и медицинские руководства
    """
    __tablename__ = "knowledge_base_documents"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Тип документа
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Метаданные
    source: Mapped[Optional[str]] = mapped_column(String(255))
    section: Mapped[Optional[str]] = mapped_column(String(255))
    article: Mapped[Optional[int]] = mapped_column(Integer, index=True)

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

    # Векторное представление для RAG
    content_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Relationships
    chunks: Mapped[list["KnowledgeBaseChunk"]] = relationship(
        "KnowledgeBaseChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBaseDocument(type={self.document_type}, title={self.title[:50]})>"


# Индекс для векторного поиска
Index(
    'idx_kb_embedding',
    KnowledgeBaseDocument.content_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'content_embedding': 'vector_cosine_ops'}
)


class KnowledgeBaseChunk(Base):
    """
    Чанки документов для RAG
    Фрагменты текста для более точного поиска
    """
    __tablename__ = "knowledge_base_chunks"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Key
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_base_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Текст чанка
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_order: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Векторное представление чанка
    chunk_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    # Relationships
    document: Mapped["KnowledgeBaseDocument"] = relationship(
        "KnowledgeBaseDocument",
        back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBaseChunk(order={self.chunk_order}, text={self.chunk_text[:30]})>"


# Индекс для векторного поиска
Index(
    'idx_chunks_embedding',
    KnowledgeBaseChunk.chunk_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'chunk_embedding': 'vector_cosine_ops'}
)


class SimilarCasesCache(Base):
    """
    Кэш аналогичных случаев
    Хранит информацию о похожих призывниках
    """
    __tablename__ = "similar_cases_cache"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign Keys
    source_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id"),
        index=True
    )
    similar_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conscripts.id")
    )

    # Мера сходства
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, index=True)

    # Общие характеристики
    shared_icd10_codes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))
    shared_article: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SimilarCasesCache(similarity={self.similarity_score})>"


class AIPrompt(Base):
    """
    Промпты для AI (версионирование)
    Хранение и версионирование промптов для LLM
    """
    __tablename__ = "ai_prompts"

    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Идентификация промпта
    prompt_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Настройки модели
    model_type: Mapped[Optional[str]] = mapped_column(String(50))
    temperature: Mapped[Optional[float]] = mapped_column(Float)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer)

    # Статус
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<AIPrompt(name={self.prompt_name}, version={self.version}, active={self.is_active})>"


# Импорты для forward references
from app.models.conscript import Conscript
from app.models.medical import SpecialistExamination
