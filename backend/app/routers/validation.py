"""
API endpoints для валидации заключений врача
Реализация полной трехэтапной валидации согласно ARCHITECTURE_PRIKAS_722.md

Этап 0: Проверка противоречий
Этап 1: Клиническая валидация (AI + RAG + Приложение 2)
Этап 2: Административная проверка (SQL + Приложение 1)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

from app.utils.database import get_db
from app.models.ai import AIAnalysisResult
from app.schemas.validation import (
    CheckDoctorConclusionRequest,
    CheckDoctorConclusionResponse,
    SavedAnalysisResultResponse,
    GetSavedAnalysisResponse
)
from app.services.full_validation_service import full_validation_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/check-doctor-conclusion",
    response_model=CheckDoctorConclusionResponse,
    summary="Полная проверка заключения врача",
    description="""
## Полная трехэтапная валидация заключения врача

Выполняет комплексную проверку заключения врача-специалиста на соответствие
Приказу МО РК №722 "Требования к здоровью призывников".

### Этап 0: Проверка противоречий

Выявляет несоответствия между разными частями заключения:

| Тип | Описание | Серьёзность |
|-----|----------|-------------|
| **TYPE_A** | "Здоров" в диагнозе, но болезнь в анамнезе/жалобах | HIGH/CRITICAL |
| **TYPE_B** | Болезнь в диагнозе, но "здоров" в анамнезе | MEDIUM |
| **TYPE_C** | Разные болезни в диагнозе и анамнезе | HIGH |
| **TYPE_D** | Диагноз не соответствует категории по справочнику | CRITICAL |
| **TYPE_E** | "Здоров" с категорией != А (логическая ошибка) | HIGH |
| **TYPE_F** | Тяжёлый диагноз с категорией "А" | CRITICAL |

### Этап 1: Клиническая валидация (AI + RAG)

- Использует RAG для поиска релевантных критериев из Приложения 2
- AI определяет номер статьи и подпункта
- Валидирует существование комбинации в справочнике

### Этап 2: Административная проверка (SQL)

- Получает категорию годности из таблицы `point_criteria`
- Сравнивает с категорией, поставленной врачом
- Учитывает график призывника (1-4)

### Результат

Система НЕ определяет истину, а СИГНАЛИЗИРУЕТ о проблемах председателю комиссии:
- `overall_status`: VALID / WARNING / INVALID
- `risk_level`: LOW / MEDIUM / HIGH / CRITICAL
- `should_review`: требуется ли ручная проверка
- `review_reasons`: список причин для проверки
- `recommendations`: рекомендации системы
""",
    responses={
        200: {
            "description": "Успешная валидация",
            "content": {
                "application/json": {
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
                            "details": {
                                "expected_category": "Д",
                                "doctor_category": "Б"
                            },
                            "duration_seconds": 0.05
                        },
                        "ai_recommended_article": 43,
                        "ai_recommended_subpoint": "3",
                        "ai_recommended_category": "Д",
                        "ai_confidence": 0.85,
                        "doctor_category": "Б",
                        "category_match_status": "MISMATCH",
                        "should_review": True,
                        "review_reasons": [
                            "Категория врача (Б) не совпадает с рекомендованной (Д)"
                        ],
                        "is_healthy": False
                    }
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера"
        }
    },
    tags=["Validation"]
)
async def check_doctor_conclusion(
    request: CheckDoctorConclusionRequest,
    db: AsyncSession = Depends(get_db)
) -> CheckDoctorConclusionResponse:
    """
    Полная проверка заключения врача на соответствие Приказу 722

    Принимает диагноз, категорию врача и дополнительные данные.
    Возвращает результат трехэтапной валидации.
    """
    try:
        logger.info(
            f"Запрос на валидацию: specialty={request.specialty}, "
            f"category={request.doctor_category}, "
            f"icd10={request.icd10_codes}"
        )

        result = await full_validation_service.full_validation_with_contradiction_check(
            db=db,
            diagnosis_text=request.diagnosis_text,
            doctor_category=request.doctor_category,
            specialty=request.specialty,
            anamnesis=request.anamnesis,
            complaints=request.complaints,
            objective_data=request.objective_data,
            special_research_results=request.special_research_results,
            conclusion_text=request.conclusion_text,
            doctor_notes=request.doctor_notes,
            icd10_codes=request.icd10_codes,
            article_hint=request.article_hint,
            subpoint_hint=request.subpoint_hint,
            graph=request.graph,
            conscript_draft_id=request.conscript_draft_id,
            examination_id=request.examination_id,
            save_to_db=request.save_to_db
        )

        logger.info(
            f"Валидация завершена: status={result.overall_status}, "
            f"risk_level={result.risk_level}, "
            f"contradictions={len(result.stage_0_contradictions)}"
        )

        return result

    except Exception as e:
        logger.error(f"Ошибка при валидации заключения: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при валидации заключения: {str(e)}"
        )


@router.post(
    "/check-contradictions-only",
    summary="Проверка только противоречий (Этап 0)",
    description="""
Выполняет только проверку противоречий (Этап 0) без AI анализа.
Быстрая проверка на логические ошибки и несоответствия в данных.

Полезно для:
- Быстрой предварительной проверки
- Валидации перед отправкой на полный анализ
- Отладки конкретных типов противоречий
""",
    tags=["Validation"]
)
async def check_contradictions_only(
    request: CheckDoctorConclusionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Проверка только противоречий без полного AI анализа
    """
    from app.services.contradiction_checker import contradiction_checker

    try:
        contradictions = await contradiction_checker.check_for_contradictions(
            db=db,
            diagnosis_text=request.diagnosis_text,
            doctor_category=request.doctor_category,
            anamnesis=request.anamnesis,
            complaints=request.complaints,
            objective_data=request.objective_data,
            special_research_results=request.special_research_results,
            doctor_notes=request.doctor_notes,
            icd10_codes=request.icd10_codes,
            graph=request.graph
        )

        # Конвертируем в словари
        result = [c.to_dict() for c in contradictions if c.has_contradiction]

        return {
            "total_contradictions": len(result),
            "has_critical": any(c["severity"] == "CRITICAL" for c in result),
            "contradictions": result
        }

    except Exception as e:
        logger.error(f"Ошибка при проверке противоречий: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при проверке противоречий: {str(e)}"
        )


@router.post(
    "/search-diseases-in-text",
    summary="Поиск заболеваний в тексте через RAG",
    description="""
Ищет упоминания заболеваний в произвольном тексте через семантический поиск.

Использует:
- OpenAI embeddings (text-embedding-3-small)
- pgvector для косинусного поиска
- Таблицу point_criteria (критерии Приказа 722)

Полезно для:
- Анализа анамнеза
- Поиска скрытых заболеваний в тексте
- Отладки RAG поиска
""",
    tags=["Validation"]
)
async def search_diseases_in_text(
    text: str,
    top_k: int = 5,
    similarity_threshold: float = 0.65,
    db: AsyncSession = Depends(get_db)
):
    """
    RAG поиск заболеваний в тексте
    """
    from app.services.rag_service import rag_service

    try:
        diseases = await rag_service.search_diseases_in_text(
            db=db,
            text=text,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        return {
            "query_text": text[:200],
            "total_found": len(diseases),
            "threshold": similarity_threshold,
            "diseases": diseases
        }

    except Exception as e:
        logger.error(f"Ошибка при поиске заболеваний: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при поиске заболеваний: {str(e)}"
        )


@router.get(
    "/saved-analysis/{conscript_draft_id}",
    response_model=GetSavedAnalysisResponse,
    summary="Получить сохраненные результаты AI анализа",
    description="""
Возвращает все сохраненные результаты AI анализа для указанного призывника.

Можно фильтровать по специальности через query параметр `specialty`.

Результаты отсортированы по дате создания (новые первые).
""",
    tags=["Validation"]
)
async def get_saved_analysis(
    conscript_draft_id: uuid.UUID,
    specialty: str = None,
    db: AsyncSession = Depends(get_db)
) -> GetSavedAnalysisResponse:
    """
    Получить сохраненные результаты AI анализа для призывника
    """
    try:
        # ВАЖНО: conscript_draft_id может быть ID призывника (conscript.id) или ID draft
        # Сначала пробуем найти по draft_id, если не найдено - ищем draft по conscript_id
        from app.models.conscript import Conscript

        # Сначала проверяем, это draft.id или conscript.id
        stmt = select(Conscript).where(Conscript.id == conscript_draft_id)
        draft_result = await db.execute(stmt)
        draft = draft_result.scalar_one_or_none()

        # Если не найдено по draft.id, ищем по conscript_id
        if draft is None:
            stmt = select(Conscript).where(Conscript.conscript_id == conscript_draft_id)
            draft_result = await db.execute(stmt)
            draft = draft_result.scalar_one_or_none()

        # Если draft найден, используем его ID для поиска результатов
        actual_draft_id = draft.id if draft else conscript_draft_id

        # Формируем запрос
        query = select(AIAnalysisResult).where(
            AIAnalysisResult.conscript_draft_id == actual_draft_id
        )

        # Фильтр по специальности (опционально)
        if specialty:
            query = query.where(AIAnalysisResult.specialty == specialty)

        # Сортировка по дате создания (новые первые)
        query = query.order_by(AIAnalysisResult.created_at.desc())

        # Выполняем запрос
        result = await db.execute(query)
        analysis_results = result.scalars().all()

        # Конвертируем в Pydantic модели
        saved_results = [
            SavedAnalysisResultResponse.from_orm(ar)
            for ar in analysis_results
        ]

        logger.info(
            f"Получены сохраненные результаты: conscript_draft_id={conscript_draft_id}, "
            f"specialty={specialty}, count={len(saved_results)}"
        )

        return GetSavedAnalysisResponse(
            results=saved_results,
            total_count=len(saved_results)
        )

    except Exception as e:
        logger.error(f"Ошибка получения сохраненных результатов: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения сохраненных результатов: {str(e)}"
        )
