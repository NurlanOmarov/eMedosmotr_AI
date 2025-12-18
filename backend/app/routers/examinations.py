"""
API endpoints для работы с осмотрами специалистов
Создание, обновление и получение данных освидетельствования
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date

from app.utils.database import get_db
from app.models.medical import SpecialistExamination
from app.models.conscript import Conscript
from app.services.examination_checker import examination_checker

router = APIRouter()


async def update_draft_status(db: AsyncSession, draft_id: UUID) -> None:
    """
    Автоматически обновляет статус призывной кампании на основе полноты освидетельствования

    Логика:
    - pending: нет ни одного завершенного освидетельствования
    - in_progress: есть хотя бы одно освидетельствование, но не все 9 обязательных
    - completed: все 9 обязательных врачей завершили освидетельствование
    """
    # Проверяем полноту освидетельствования
    completeness = await examination_checker.check_completeness(db, draft_id)

    # Получаем призывную кампанию
    draft_query = select(Conscript).where(Conscript.id == draft_id)
    draft_result = await db.execute(draft_query)
    draft = draft_result.scalar_one_or_none()

    if not draft:
        return

    # Определяем новый статус
    if completeness.is_complete:
        new_status = 'completed'
    elif completeness.total_completed > 0:
        new_status = 'in_progress'
    else:
        new_status = 'pending'

    # Обновляем статус, если он изменился
    if draft.status != new_status:
        draft.status = new_status
        await db.commit()


# Pydantic модели для запросов/ответов
class ExaminationCreateRequest(BaseModel):
    conscript_draft_id: UUID = Field(..., description="ID призыва")
    specialty: str = Field(..., description="Специальность врача")
    specialty_ru: Optional[str] = Field(None, description="Специальность на русском")
    doctor_name: Optional[str] = Field(None, description="ФИО врача")

    # Медицинское заключение
    complaints: Optional[str] = Field(None, description="Жалобы")
    anamnesis: Optional[str] = Field(None, description="Анамнез")
    objective_data: Optional[str] = Field(None, description="Объективные данные")
    special_research_results: Optional[str] = Field(None, description="Результаты спец. исследований")
    conclusion_text: str = Field(..., description="Текст заключения")

    # Диагноз
    icd10_code: str = Field(..., description="Код МКБ-10")
    diagnosis_text: str = Field(..., description="Текст диагноза")

    # Категория годности
    doctor_category: str = Field(..., description="Категория годности (А, Б, В, Г, Д, Е)")
    category_enum: Optional[str] = Field(None, description="Категория enum")

    # Дополнительно
    additional_comment: Optional[str] = Field(None, description="Дополнительный комментарий")
    examination_date: Optional[date] = Field(None, description="Дата осмотра")

    # Специфичные поля для офтальмолога
    od_vision_without_correction: Optional[float] = Field(None, description="Зрение OD без коррекции")
    os_vision_without_correction: Optional[float] = Field(None, description="Зрение OS без коррекции")

    # Специфичное поле для стоматолога (зубная формула)
    dentist_json: Optional[dict] = Field(None, description="Зубная формула (JSON)")


class ExaminationUpdateRequest(BaseModel):
    specialty_ru: Optional[str] = None
    doctor_name: Optional[str] = None
    complaints: Optional[str] = None
    anamnesis: Optional[str] = None
    objective_data: Optional[str] = None
    special_research_results: Optional[str] = None
    conclusion_text: Optional[str] = None
    icd10_code: Optional[str] = None
    diagnosis_text: Optional[str] = None
    doctor_category: Optional[str] = None
    category_enum: Optional[str] = None
    additional_comment: Optional[str] = None
    examination_date: Optional[date] = None
    # Специфичные поля для офтальмолога
    od_vision_without_correction: Optional[float] = None
    os_vision_without_correction: Optional[float] = None
    # Специфичное поле для стоматолога
    dentist_json: Optional[dict] = None


class ExaminationResponse(BaseModel):
    id: UUID
    conscript_draft_id: UUID
    specialty: str
    specialty_ru: Optional[str]
    doctor_name: Optional[str]
    complaints: Optional[str]
    anamnesis: Optional[str]
    objective_data: Optional[str]
    special_research_results: Optional[str]
    conclusion_text: str
    icd10_code: str
    diagnosis_text: str
    doctor_category: str
    category_enum: Optional[str]
    additional_comment: Optional[str]
    examination_date: date
    # Специфичные поля для офтальмолога
    od_vision_without_correction: Optional[float] = None
    os_vision_without_correction: Optional[float] = None
    # Специфичное поле для стоматолога
    dentist_json: Optional[dict] = None

    class Config:
        from_attributes = True


@router.post("/examinations", response_model=ExaminationResponse)
async def create_examination(
    request: ExaminationCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать новый осмотр специалиста

    **Обязательные поля:**
    - conscript_draft_id: ID призыва
    - specialty: Специальность врача
    - conclusion_text: Заключение врача
    - icd10_code: Код диагноза по МКБ-10
    - diagnosis_text: Текст диагноза
    - doctor_category: Категория годности (А, Б, В, Г, Д, Е)
    """
    try:
        # Проверяем существование призыва
        draft_query = select(Conscript).where(
            Conscript.id == request.conscript_draft_id
        )
        draft_result = await db.execute(draft_query)
        draft = draft_result.scalar_one_or_none()

        if not draft:
            raise HTTPException(
                status_code=404,
                detail=f"Призыв с ID {request.conscript_draft_id} не найден"
            )

        # Проверяем, нет ли уже осмотра этого специалиста
        existing_query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == request.conscript_draft_id,
            SpecialistExamination.specialty == request.specialty
        )
        existing_result = await db.execute(existing_query)
        existing_exam = existing_result.scalar_one_or_none()

        if existing_exam:
            raise HTTPException(
                status_code=400,
                detail=f"Осмотр специалиста '{request.specialty}' уже существует. Используйте PUT для обновления."
            )

        # Создаем новый осмотр
        new_examination = SpecialistExamination(
            conscript_draft_id=request.conscript_draft_id,
            specialty=request.specialty,
            specialty_ru=request.specialty_ru,
            doctor_name=request.doctor_name,
            complaints=request.complaints,
            anamnesis=request.anamnesis,
            objective_data=request.objective_data,
            special_research_results=request.special_research_results,
            conclusion_text=request.conclusion_text,
            icd10_code=request.icd10_code,
            diagnosis_text=request.diagnosis_text,
            doctor_category=request.doctor_category,
            category_enum=request.category_enum,
            additional_comment=request.additional_comment,
            examination_date=request.examination_date,
            # Специфичные поля для офтальмолога
            od_vision_without_correction=request.od_vision_without_correction,
            os_vision_without_correction=request.os_vision_without_correction,
            # Специфичное поле для стоматолога
            dentist_json=request.dentist_json
        )

        db.add(new_examination)

        # NOTE: Embeddings для осмотров НЕ генерируются автоматически,
        # так как они не используются в текущем функционале AI-анализа.
        # RAG использует только embeddings критериев (point_criteria).
        #
        # Если в будущем понадобится функционал "Найти похожие случаи",
        # embeddings можно генерировать:
        # 1. Фоновой задачей (Celery/Background Tasks)
        # 2. При первом запросе поиска похожих осмотров
        # 3. Batch-скриптом для исторических данных

        await db.commit()
        await db.refresh(new_examination)

        # Автоматически обновляем статус призывной кампании
        await update_draft_status(db, draft.id)

        return new_examination

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании осмотра: {str(e)}"
        )


@router.put("/examinations/{conscript_draft_id}/{specialty}", response_model=ExaminationResponse)
async def update_examination(
    conscript_draft_id: UUID,
    specialty: str,
    request: ExaminationUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить существующий осмотр специалиста

    **Параметры:**
    - conscript_draft_id: ID призыва
    - specialty: Специальность врача

    Обновляются только переданные поля (partial update)
    """
    try:
        # Находим существующий осмотр
        query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript_draft_id,
            SpecialistExamination.specialty == specialty
        )
        result = await db.execute(query)
        examination = result.scalar_one_or_none()

        if not examination:
            raise HTTPException(
                status_code=404,
                detail=f"Осмотр специалиста '{specialty}' для призыва {conscript_draft_id} не найден"
            )

        # Обновляем только переданные поля
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(examination, field, value)

        # NOTE: Embeddings НЕ обновляются автоматически (см. комментарий в create_examination)

        await db.commit()
        await db.refresh(examination)

        # Автоматически обновляем статус призывной кампании
        # Преобразуем UUID в int (получаем draft_id из examination)
        await update_draft_status(db, examination.draft_id)

        return examination

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении осмотра: {str(e)}"
        )


@router.get("/examinations/{conscript_draft_id}", response_model=List[ExaminationResponse])
async def get_examinations_by_conscript(
    conscript_draft_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить все осмотры для конкретного призыва
    """
    try:
        query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript_draft_id
        )
        result = await db.execute(query)
        examinations = result.scalars().all()

        return examinations

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении осмотров: {str(e)}"
        )


@router.get("/examinations/{conscript_draft_id}/{specialty}", response_model=ExaminationResponse)
async def get_examination_by_specialty(
    conscript_draft_id: UUID,
    specialty: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить осмотр конкретного специалиста для призыва
    """
    try:
        query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript_draft_id,
            SpecialistExamination.specialty == specialty
        )
        result = await db.execute(query)
        examination = result.scalar_one_or_none()

        if not examination:
            raise HTTPException(
                status_code=404,
                detail=f"Осмотр специалиста '{specialty}' для призыва {conscript_draft_id} не найден"
            )

        return examination

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении осмотра: {str(e)}"
        )


@router.delete("/examinations/{conscript_draft_id}/{specialty}")
async def delete_examination(
    conscript_draft_id: UUID,
    specialty: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Удалить осмотр специалиста
    """
    try:
        query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript_draft_id,
            SpecialistExamination.specialty == specialty
        )
        result = await db.execute(query)
        examination = result.scalar_one_or_none()

        if not examination:
            raise HTTPException(
                status_code=404,
                detail=f"Осмотр специалиста '{specialty}' для призыва {conscript_draft_id} не найден"
            )

        await db.delete(examination)
        await db.commit()

        return {"message": f"Осмотр специалиста '{specialty}' успешно удален"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при удалении осмотра: {str(e)}"
        )
