"""
Справочные модели
МКБ-10, Приказ 722, категории годности
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, DateTime, Index, JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.utils.database import Base


class ICD10Code(Base):
    """
    Справочник МКБ-10 (ICD-10)
    Международная классификация болезней
    """
    __tablename__ = "icd10_codes"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Коды МКБ-10
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    code_f1: Mapped[Optional[str]] = mapped_column(String(5))  # Для иерархии
    code_f2: Mapped[Optional[str]] = mapped_column(String(5))
    code_f3: Mapped[Optional[str]] = mapped_column(String(5))

    # Названия
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    name_kz: Mapped[Optional[str]] = mapped_column(Text)

    # Иерархия
    parent_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    # Векторное представление для RAG
    name_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536))

    def __repr__(self) -> str:
        return f"<ICD10Code(code={self.code}, name_ru={self.name_ru[:50]})>"


# Индекс для векторного поиска
Index(
    'idx_icd10_name_embedding',
    ICD10Code.name_embedding,
    postgresql_using='ivfflat',
    postgresql_with={'lists': 100},
    postgresql_ops={'name_embedding': 'vector_cosine_ops'}
)


class PointDiagnosis(Base):
    """
    Приказ 722 - Приложение 1: Таблица категорий годности
    Статьи с диагнозами и категориями для разных граф
    """
    __tablename__ = "points_diagnoses"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Идентификация статьи и подпункта
    article: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    subpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Номер подпункта (1, 2, 3...)
    point_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icd10_chapter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Категории годности для 4 граф (из Приложения 1)
    graph_1: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Призывники
    graph_2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Контрактники
    graph_3: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Курсанты
    graph_4: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Спецподразделения

    # Timestamp
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<PointDiagnosis(article={self.article}, subpoint={self.subpoint})>"


# Индексы отключены - колонки не существуют
# Index(
#     'idx_points_codes',
#     PointDiagnosis.diagnoses_codes,
#     postgresql_using='gin',
#     postgresql_ops={'diagnoses_codes': 'gin_trgm_ops'}
# )
#
# Index(
#     'idx_points_unique',
#     PointDiagnosis.article,
#     PointDiagnosis.point_name,
#     unique=True
# )


class PointCriterion(Base):
    """
    Критерии подпунктов (Приложение 2)
    Детальные критерии для определения подпункта
    """
    __tablename__ = "point_criteria"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Связь с PointDiagnosis
    point_diagnosis_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    article: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    subpoint: Mapped[str] = mapped_column(String(50), nullable=False)

    # Критерии
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Не используется в БД
    # quantitative_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Не используется в БД

    # Категории для разных граф
    graph_1: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    graph_2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    graph_3: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    graph_4: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamp
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Векторное представление для RAG
    criteria_embedding: Mapped[Optional[Vector]] = mapped_column(Vector(1536), nullable=True)

    def __repr__(self) -> str:
        return f"<PointCriterion(article={self.article}, subpoint={self.subpoint})>"


class CategoryDictionary(Base):
    """
    Словарь категорий годности
    А, Б, В, Г, Д, Е, НГ
    """
    __tablename__ = "category_dictionary"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Коды категорий
    code_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    display_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)

    # Описания
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)

    # Иерархия (1 - лучшая, 7 - худшая)
    hierarchy_level: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<CategoryDictionary(code={self.display_code}, name={self.name_ru})>"


class CategoryGraph(Base):
    """
    Словарь граф (категории призывников)
    1 - Обычные призывники
    2 - Курсанты
    3 - Офицеры
    4 - Спецназ
    """
    __tablename__ = "category_graph"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # График
    graph: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)

    # Описания
    name_ru: Mapped[str] = mapped_column(Text, nullable=False)
    description_ru: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<CategoryGraph(graph={self.graph}, name={self.name_ru})>"


class ChapterSpecialtyMapping(Base):
    """
    Маппинг глав Приказа 722 на специальности врачей
    Например: Глава 7 -> Офтальмолог
    """
    __tablename__ = "chapter_specialty_mapping"

    # Primary Key (SERIAL)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Глава и специальность
    chapter: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    specialty_ru: Mapped[Optional[str]] = mapped_column(String(255))

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<ChapterSpecialtyMapping(chapter={self.chapter}, specialty={self.specialty})>"
