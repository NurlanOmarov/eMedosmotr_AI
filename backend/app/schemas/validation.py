"""
Pydantic схемы для API валидации заключений врача
Согласно ARCHITECTURE_PRIKAS_722.md
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class ContradictionTypeEnum(str, Enum):
    """
    Типы противоречий согласно ARCHITECTURE_PRIKAS_722.md

    TYPE_A: "Здоров" в диагнозе -> Болезнь в дополнительных полях
    TYPE_B: Болезнь в диагнозе -> "Здоров" в дополнительных полях
    TYPE_C: Болезнь A в диагнозе -> Болезнь B в дополнительных полях
    TYPE_D: Диагноз vs Неправильная категория
    TYPE_E: "Здоров" + категория != "А" (логическая ошибка)
    TYPE_F: Тяжелый диагноз + категория "А" (явное несоответствие)
    """
    TYPE_A = "TYPE_A_HEALTHY_VS_DISEASE"
    TYPE_B = "TYPE_B_DISEASE_VS_HEALTHY"
    TYPE_C = "TYPE_C_DISEASE_A_VS_DISEASE_B"
    TYPE_D = "TYPE_D_CATEGORY_MISMATCH"
    TYPE_E = "TYPE_E_LOGICAL_ERROR"
    TYPE_F = "TYPE_F_OBVIOUS_CATEGORY_MISMATCH"


class SeverityEnum(str, Enum):
    """Уровни серьёзности противоречий"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class OverallStatusEnum(str, Enum):
    """Общий статус валидации"""
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


class MatchStatusEnum(str, Enum):
    """Статус совпадения категорий"""
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    PARTIAL_MISMATCH = "PARTIAL_MISMATCH"  # Возможное несоответствие (пограничные случаи)
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RAGMatch(BaseModel):
    """Результат RAG поиска заболевания"""
    article: int = Field(..., description="Номер статьи Приказа 722")
    subpoint: str = Field(..., description="Подпункт статьи")
    description: str = Field(..., description="Описание критерия")
    similarity: float = Field(..., ge=0, le=1, description="Коэффициент похожести (0-1)")
    categories: Dict[int, Optional[str]] = Field(
        default_factory=dict,
        description="Категории для граф 1-4"
    )


class ContradictionDetail(BaseModel):
    """Детали найденного противоречия"""
    type: ContradictionTypeEnum = Field(..., description="Тип противоречия")
    severity: SeverityEnum = Field(..., description="Уровень серьёзности")
    description: str = Field(..., description="Описание противоречия на русском языке")
    source_field: Optional[str] = Field(None, description="Поле-источник (например, diagnosis_text)")
    target_field: Optional[str] = Field(None, description="Поле-цель (например, anamnesis)")
    source_value: Optional[str] = Field(None, description="Значение в поле-источнике")
    target_value: Optional[str] = Field(None, description="Значение в поле-цели")
    rag_matches: List[RAGMatch] = Field(
        default_factory=list,
        description="Найденные заболевания через RAG"
    )
    recommendation: Optional[str] = Field(None, description="Рекомендация по устранению противоречия")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "TYPE_A_HEALTHY_VS_DISEASE",
                "severity": "CRITICAL",
                "description": "Диагноз указывает 'Здоров', но в анамнезе обнаружен активный туберкулез",
                "source_field": "diagnosis_text",
                "target_field": "anamnesis",
                "source_value": "Здоров, патологии не выявлены",
                "target_value": "Туберкулез легких, активная форма с 2023 года",
                "rag_matches": [
                    {
                        "article": 2,
                        "subpoint": "1",
                        "description": "Активный туберкулез с бактериовыделением",
                        "similarity": 0.89,
                        "categories": {1: "Е", 2: "Е", 3: "Е", 4: "НГ"}
                    }
                ],
                "recommendation": "Требуется уточнение диагноза у фтизиатра"
            }
        }


class ValidationStageResult(BaseModel):
    """Результат одного этапа валидации"""
    stage_name: str = Field(..., description="Название этапа")
    stage_number: int = Field(..., ge=0, le=2, description="Номер этапа (0, 1, 2)")
    passed: bool = Field(..., description="Прошёл ли этап успешно")
    status: str = Field(..., description="Статус: SUCCESS, WARNING, ERROR, SKIPPED")
    details: Dict[str, Any] = Field(default_factory=dict, description="Детали результата")
    duration_seconds: Optional[float] = Field(None, description="Время выполнения в секундах")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке (если есть)")


class CheckDoctorConclusionRequest(BaseModel):
    """
    Запрос на полную проверку заключения врача

    Включает обязательные поля диагноза и категории,
    а также опциональные поля для проверки противоречий (Этап 0)
    """
    # Обязательные поля
    diagnosis_text: str = Field(
        ...,
        min_length=1,
        description="Текст диагноза врача"
    )
    doctor_category: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Категория годности, поставленная врачом (А, Б, В, Г, Д, Е, НГ)"
    )
    specialty: str = Field(
        ...,
        min_length=1,
        description="Специальность врача (Терапевт, Хирург, Офтальмолог и т.д.)"
    )

    # Опциональные поля для проверки противоречий (Этап 0)
    anamnesis: Optional[str] = Field(
        None,
        description="Анамнез заболевания"
    )
    complaints: Optional[str] = Field(
        None,
        description="Жалобы пациента"
    )
    objective_data: Optional[str] = Field(
        None,
        description="Объективные данные осмотра"
    )
    special_research_results: Optional[str] = Field(
        None,
        description="Результаты специальных исследований"
    )
    conclusion_text: Optional[str] = Field(
        None,
        description="Полный текст заключения врача"
    )
    doctor_notes: Optional[str] = Field(
        None,
        description="Дополнительные примечания врача"
    )

    # Коды МКБ-10 и граф призывника
    icd10_codes: Optional[List[str]] = Field(
        None,
        description="Коды МКБ-10 диагнозов"
    )
    article_hint: Optional[int] = Field(
        None,
        ge=1,
        le=89,
        description="Подсказка по номеру статьи (если врач указал)"
    )
    subpoint_hint: Optional[str] = Field(
        None,
        description="Подсказка по подпункту (если врач указал)"
    )
    graph: int = Field(
        1,
        ge=1,
        le=4,
        description="График призывника: 1-обычные, 2-курсанты, 3-офицеры, 4-спецназ"
    )

    # Поля для сохранения результатов в БД
    conscript_draft_id: Optional[uuid.UUID] = Field(
        None,
        description="ID призывника для сохранения результатов анализа в БД"
    )
    examination_id: Optional[uuid.UUID] = Field(
        None,
        description="ID осмотра специалиста"
    )
    save_to_db: bool = Field(
        False,
        description="Сохранять ли результаты анализа в БД (по умолчанию False)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "diagnosis_text": "Гипертоническая болезнь 2 степени, риск 3",
                "doctor_category": "Б",
                "specialty": "Терапевт",
                "anamnesis": "На диспансерном учёте с 2020 года. АД до 170/100 мм рт.ст.",
                "complaints": "Периодические головные боли, головокружение",
                "objective_data": "АД 160/100 мм рт.ст., ЧСС 78 уд/мин",
                "icd10_codes": ["I11.9"],
                "graph": 1
            }
        }


class CheckDoctorConclusionResponse(BaseModel):
    """
    Ответ полной проверки заключения врача

    Включает результаты всех трёх этапов валидации:
    - Этап 0: Проверка противоречий
    - Этап 1: Клиническая валидация (AI + RAG)
    - Этап 2: Административная проверка (SQL)
    """
    # Общий результат
    overall_status: OverallStatusEnum = Field(
        ...,
        description="Общий статус валидации: VALID, WARNING, INVALID"
    )
    risk_level: SeverityEnum = Field(
        ...,
        description="Уровень риска: LOW, MEDIUM, HIGH, CRITICAL"
    )

    # Результаты по этапам
    stage_0_contradictions: List[ContradictionDetail] = Field(
        default_factory=list,
        description="Этап 0: Найденные противоречия в данных"
    )
    stage_1_clinical: ValidationStageResult = Field(
        ...,
        description="Этап 1: Результат клинической валидации (AI + Приложение 2)"
    )
    stage_2_administrative: ValidationStageResult = Field(
        ...,
        description="Этап 2: Результат административной проверки (SQL + Приложение 1)"
    )

    # AI рекомендации
    ai_recommended_article: Optional[int] = Field(
        None,
        description="Рекомендованная статья Приказа 722"
    )
    ai_recommended_subpoint: Optional[str] = Field(
        None,
        description="Рекомендованный подпункт"
    )
    ai_recommended_category: Optional[str] = Field(
        None,
        description="Рекомендованная категория годности"
    )
    ai_confidence: float = Field(
        0.0,
        ge=0,
        le=1,
        description="Уверенность AI в рекомендации (0-1)"
    )
    ai_reasoning: str = Field(
        "",
        description="Обоснование рекомендации AI"
    )

    # Сравнение с врачом
    doctor_article: Optional[int] = Field(
        None,
        description="Статья, указанная врачом"
    )
    doctor_subpoint: Optional[str] = Field(
        None,
        description="Подпункт, указанный врачом"
    )
    doctor_category: str = Field(
        ...,
        description="Категория, поставленная врачом"
    )
    category_match_status: MatchStatusEnum = Field(
        ...,
        description="Статус совпадения категорий: MATCH, MISMATCH, REVIEW_REQUIRED"
    )

    # Флаги для председателя комиссии
    should_review: bool = Field(
        ...,
        description="Требуется ли ручная проверка председателем"
    )
    review_reasons: List[str] = Field(
        default_factory=list,
        description="Причины для ручной проверки"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Рекомендации системы"
    )

    # Для здорового призывника
    is_healthy: bool = Field(
        False,
        description="Признан ли призывник здоровым (без патологий)"
    )

    # Метаданные
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Дополнительные метаданные (модель AI, время, токены)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_status": "WARNING",
                "risk_level": "MEDIUM",
                "stage_0_contradictions": [],
                "stage_1_clinical": {
                    "stage_name": "Клиническая валидация",
                    "stage_number": 1,
                    "passed": True,
                    "status": "SUCCESS",
                    "details": {"article": 43, "subpoint": "3"},
                    "duration_seconds": 1.25
                },
                "stage_2_administrative": {
                    "stage_name": "Административная проверка",
                    "stage_number": 2,
                    "passed": False,
                    "status": "WARNING",
                    "details": {"expected_category": "Д", "doctor_category": "Б"},
                    "duration_seconds": 0.05
                },
                "ai_recommended_article": 43,
                "ai_recommended_subpoint": "3",
                "ai_recommended_category": "Д",
                "ai_confidence": 0.85,
                "ai_reasoning": "АД 170/100 соответствует критериям статьи 43, подпункт 3",
                "doctor_category": "Б",
                "category_match_status": "MISMATCH",
                "should_review": True,
                "review_reasons": [
                    "Категория врача (Б) не совпадает с рекомендованной (Д)"
                ],
                "recommendations": [
                    "Проверить соответствие категории Приказу 722, статья 43"
                ],
                "is_healthy": False,
                "metadata": {
                    "model": "gpt-4o-mini",
                    "total_duration_seconds": 1.3,
                    "tokens_used": 1250
                }
            }
        }


class SavedAnalysisResultResponse(BaseModel):
    """Сохраненный результат AI анализа из БД"""
    id: uuid.UUID
    conscript_draft_id: uuid.UUID
    examination_id: Optional[uuid.UUID] = None
    specialty: str
    doctor_category: str
    ai_recommended_category: str
    status: str
    risk_level: str
    article: Optional[int] = None
    subpoint: Optional[str] = None
    reasoning: str
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    analysis_duration_seconds: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GetSavedAnalysisRequest(BaseModel):
    """Запрос на получение сохраненных результатов анализа"""
    conscript_draft_id: uuid.UUID = Field(..., description="ID призывника")
    specialty: Optional[str] = Field(None, description="Специальность (опционально, для фильтрации)")


class GetSavedAnalysisResponse(BaseModel):
    """Ответ с сохраненными результатами анализа"""
    results: List[SavedAnalysisResultResponse] = Field(
        default_factory=list,
        description="Список сохраненных результатов анализа"
    )
    total_count: int = Field(..., description="Общее количество результатов")
