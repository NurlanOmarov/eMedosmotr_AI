"""
API endpoints для AI анализа медицинских заключений
Определение подпунктов и категорий годности
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.utils.database import get_db
from app.services.ai_analyzer import ai_analyzer
from app.services.examination_checker import examination_checker
from app.services.pdf_report_service import pdf_report_service
from app.models.conscript import Conscript

router = APIRouter()


# Pydantic модели для запросов/ответов
class DetermineSubpointRequest(BaseModel):
    doctor_conclusion: str = Field(..., description="Заключение врача-специалиста")
    specialty: str = Field(..., description="Специальность врача")
    icd10_codes: Optional[List[str]] = Field(None, description="Коды МКБ-10")
    article_hint: Optional[int] = Field(None, description="Подсказка по статье (опционально)")


class SubpointAnalysisResponse(BaseModel):
    article: Optional[int]
    subpoint: Optional[str]
    confidence: float
    reasoning: str
    matched_criteria: Optional[str]
    parameters_matched: Optional[dict]
    metadata: Optional[dict]


class DetermineCategoryRequest(BaseModel):
    article: int = Field(..., description="Номер статьи")
    subpoint: str = Field(..., description="Подпункт (например, 'а', 'б', 'в')")
    graph: int = Field(1, ge=1, le=4, description="График призывника (1-4)")


class CategoryAnalysisResponse(BaseModel):
    category: Optional[str]
    graph: int
    confidence: float
    reasoning: str
    diagnoses_codes: Optional[str]
    diagnoses_decoding: Optional[str]
    alternative_categories: List[str]


class AnalyzeExaminationRequest(BaseModel):
    doctor_conclusion: str = Field(..., description="Заключение врача")
    specialty: str = Field(..., description="Специальность врача")
    doctor_category: str = Field(..., description="Категория, поставленная врачом")
    icd10_codes: Optional[List[str]] = Field(None, description="Коды МКБ-10")
    graph: int = Field(1, ge=1, le=4, description="График призывника (1-4)")
    conscript_draft_id: Optional[str] = Field(None, description="ID призыва")
    examination_id: Optional[str] = Field(None, description="ID обследования")
    anamnesis: Optional[str] = Field(None, description="Анамнез (история заболевания)")
    complaints: Optional[str] = Field(None, description="Жалобы пациента")
    special_research_results: Optional[str] = Field(None, description="Результаты специальных исследований")


class ExaminationAnalysisResponse(BaseModel):
    specialty: str
    doctor_category: str
    ai_recommended_category: Optional[str]
    status: str  # MATCH, MISMATCH, REVIEW_REQUIRED
    risk_level: str  # LOW, MEDIUM, HIGH
    article: Optional[int]
    subpoint: Optional[str]
    reasoning: str
    confidence: float
    subpoint_details: dict
    category_details: dict


@router.post("/determine-subpoint", response_model=SubpointAnalysisResponse)
async def determine_subpoint(
    request: DetermineSubpointRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Определение подпункта статьи на основе заключения врача

    Использует GPT-4o-mini + RAG для анализа заключения врача
    и определения наиболее подходящего подпункта из Приложения 2.

    **Процесс:**
    1. Векторный поиск релевантных критериев (RAG)
    2. Формирование промпта с контекстом
    3. Анализ с помощью GPT-4o-mini
    4. Возврат подпункта + уверенность + объяснение
    """
    try:
        result = await ai_analyzer.determine_subpoint(
            db=db,
            doctor_conclusion=request.doctor_conclusion,
            specialty=request.specialty,
            icd10_codes=request.icd10_codes,
            article_hint=request.article_hint
        )

        return SubpointAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при определении подпункта: {str(e)}"
        )


@router.post("/determine-category", response_model=CategoryAnalysisResponse)
async def determine_category(
    request: DetermineCategoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Определение категории годности по статье и подпункту

    Ищет в справочнике PointDiagnosis соответствующую категорию
    для данной статьи, подпункта и графы призывника.

    **Графы:**
    - 1: Обычные призывники
    - 2: Курсанты военных учебных заведений
    - 3: Офицеры запаса
    - 4: Спецназ и специальные подразделения
    """
    try:
        result = await ai_analyzer.determine_category(
            db=db,
            article=request.article,
            subpoint=request.subpoint,
            graph=request.graph
        )

        return CategoryAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при определении категории: {str(e)}"
        )


@router.post("/analyze-examination", response_model=ExaminationAnalysisResponse)
async def analyze_examination(
    request: AnalyzeExaminationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Полный анализ заключения врача-специалиста

    **Комплексный анализ включает:**
    1. Определение подпункта (AI + RAG)
    2. Определение категории (справочник)
    3. Сравнение с категорией врача
    4. Оценка риска расхождения

    **Статусы:**
    - `MATCH`: AI и врач согласны
    - `MISMATCH`: Есть расхождение в категориях
    - `REVIEW_REQUIRED`: Требуется ручная проверка

    **Уровни риска:**
    - `LOW`: Всё согласовано, высокая уверенность
    - `MEDIUM`: Пограничные случаи, средняя уверенность
    - `HIGH`: Расхождения или низкая уверенность
    """
    try:
        result = await ai_analyzer.analyze_examination(
            db=db,
            doctor_conclusion=request.doctor_conclusion,
            specialty=request.specialty,
            doctor_category=request.doctor_category,
            icd10_codes=request.icd10_codes,
            graph=request.graph,
            conscript_draft_id=request.conscript_draft_id,
            examination_id=request.examination_id,
            anamnesis=request.anamnesis,
            complaints=request.complaints,
            special_research_results=request.special_research_results
        )

        return ExaminationAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при анализе заключения: {str(e)}"
        )


@router.get("/test-prompt")
async def test_prompt():
    """
    Тестовый endpoint для проверки промптов
    Возвращает используемые промпты для отладки
    """
    return {
        "subpoint_prompt": ai_analyzer.SUBPOINT_DETERMINATION_PROMPT[:300] + "...",
        "category_prompt": ai_analyzer.CATEGORY_DETERMINATION_PROMPT[:300] + "...",
        "final_verdict_prompt": ai_analyzer.FINAL_VERDICT_PROMPT[:300] + "...",
        "model": "gpt-4o-mini",
        "temperature": 0.2
    }


@router.post("/test-analysis")
async def test_analysis(db: AsyncSession = Depends(get_db)):
    """
    Тестовый endpoint с примером анализа
    """
    test_request = AnalyzeExaminationRequest(
        doctor_conclusion="Выявлена миопия высокой степени обоих глаз. "
                          "Острота зрения правого глаза 0.1, левого глаза 0.15. "
                          "С коррекцией: OD = 0.6, OS = 0.7. Рефракция: OD -7.5D, OS -8.0D.",
        specialty="Офтальмолог",
        doctor_category="В",
        icd10_codes=["H52.1"],
        graph=1
    )

    try:
        result = await ai_analyzer.analyze_examination(
            db=db,
            doctor_conclusion=test_request.doctor_conclusion,
            specialty=test_request.specialty,
            doctor_category=test_request.doctor_category,
            icd10_codes=test_request.icd10_codes,
            graph=test_request.graph
        )

        return {
            "test_case": "Миопия высокой степени",
            "result": result
        }

    except Exception as e:
        return {
            "test_case": "Миопия высокой степени",
            "error": str(e),
            "note": "Для работы требуется загрузить критерии в БД"
        }


@router.get("/check-completeness/{conscript_draft_id}")
async def check_examination_completeness(
    conscript_draft_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Проверить полноту медицинского освидетельствования призывника

    **Проверяет:**
    - Все ли обязательные специалисты провели осмотр
    - Наличие диагноза у каждого специалиста
    - Наличие категории годности у каждого специалиста

    **Возвращает:**
    - `is_complete`: Все ли специалисты провели осмотр
    - `completed_specialists`: Список специалистов, которые провели осмотр
    - `missing_specialists`: Список специалистов, которые НЕ провели осмотр
    - `can_run_ai_analysis`: Можно ли запускать ИИ анализ (требует полноты)

    **Обязательные специалисты:**
    - Терапевт
    - Хирург
    - Офтальмолог
    - Отоларинголог
    - Невролог
    - Психиатр
    - Стоматолог
    """
    try:
        completeness = await examination_checker.check_completeness(
            db=db,
            conscript_draft_id=conscript_draft_id
        )

        return completeness.to_dict()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при проверке полноты освидетельствования: {str(e)}"
        )


@router.get("/required-specialists")
async def get_required_specialists():
    """
    Получить список обязательных специалистов для ВВК

    Возвращает список специальностей, которые обязательно должны
    провести медицинский осмотр призывника перед запуском ИИ анализа.
    """
    specialists = await examination_checker.get_required_specialists()
    return {
        "required_specialists": specialists,
        "total_count": len(specialists)
    }


@router.post("/validate-for-ai-analysis/{conscript_draft_id}")
async def validate_for_ai_analysis(
    conscript_draft_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Валидация готовности призывника к ИИ анализу

    **Проверяет все требования перед запуском ИИ анализа:**
    1. Все обязательные специалисты провели осмотр
    2. Каждый специалист указал диагноз
    3. Каждый специалист указал категорию годности

    **Если validation.can_proceed = false, ИИ анализ запускать НЕЛЬЗЯ!**
    """
    try:
        completeness = await examination_checker.check_completeness(
            db=db,
            conscript_draft_id=conscript_draft_id
        )

        can_proceed = (
            completeness.is_complete
            and len(completeness.missing_diagnoses) == 0
            and len(completeness.missing_categories) == 0
        )

        errors = []
        if not completeness.is_complete:
            errors.append({
                "type": "MISSING_SPECIALISTS",
                "message": f"Не все специалисты провели осмотр. Недостающие: {', '.join(completeness.missing_specialists)}",
                "missing": completeness.missing_specialists
            })

        if completeness.missing_diagnoses:
            errors.append({
                "type": "MISSING_DIAGNOSES",
                "message": f"Не указаны диагнозы у специалистов: {', '.join(completeness.missing_diagnoses)}",
                "missing": completeness.missing_diagnoses
            })

        if completeness.missing_categories:
            errors.append({
                "type": "MISSING_CATEGORIES",
                "message": f"Не указаны категории годности у специалистов: {', '.join(completeness.missing_categories)}",
                "missing": completeness.missing_categories
            })

        return {
            "validation": {
                "can_proceed": can_proceed,
                "is_ready_for_ai": can_proceed,
                "errors": errors
            },
            "completeness": completeness.to_dict()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при валидации: {str(e)}"
        )


class ExportAnalysisRequest(BaseModel):
    conscript_id: str = Field(..., description="ID призывника")
    analysis_data: dict = Field(..., description="Данные анализа ИИ")


@router.post("/export-analysis-report")
async def export_analysis_report(
    request: ExportAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Экспорт отчета анализа ИИ в PDF формате

    **Генерирует красиво оформленный PDF отчет, содержащий:**
    - Информацию о призывнике
    - Общую статистику анализа
    - Уровень риска
    - Детальные результаты по каждому специалисту
    - Обоснования и рекомендации ИИ

    **Возвращает:**
    PDF файл для скачивания
    """
    try:
        # Получаем данные призывника из БД
        result = await db.execute(
            select(Conscript).where(Conscript.id == request.conscript_id)
        )
        conscript = result.scalar_one_or_none()

        conscript_info = None
        if conscript:
            conscript_info = {
                'fullName': conscript.full_name,
                'iin': conscript.iin,
                'birthDate': conscript.birth_date.strftime('%d.%m.%Y') if conscript.birth_date else 'Н/Д',
                'draftNumber': conscript.draft_number or 'Н/Д',
                'medicalCommissionDate': conscript.medical_commission_date.strftime('%d.%m.%Y') if conscript.medical_commission_date else None
            }

        # Генерируем PDF
        pdf_buffer = pdf_report_service.generate_analysis_report(
            conscript_data={'id': request.conscript_id},
            analysis_data=request.analysis_data,
            conscript_info=conscript_info
        )

        # Формируем имя файла
        filename = f"AI_Analysis_Report_{request.conscript_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Возвращаем PDF как файл для скачивания
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при генерации PDF отчета: {str(e)}"
        )
