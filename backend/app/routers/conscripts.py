"""
API роутер для работы с призывниками
Получение списка призывников и их медицинских данных
"""

from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
import uuid as uuid_lib
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.utils.database import get_db
from app.models.conscript import Conscript
from app.models.medical import SpecialistExamination
from app.models.reference import CategoryGraph
from app.services.examination_checker import examination_checker

router = APIRouter(prefix="/api/v1/conscripts", tags=["conscripts"])


# ========== PYDANTIC MODELS ==========

class ExaminationSimple(BaseModel):
    """Упрощенная модель заключения врача"""
    id: str
    specialty: str
    med_commission_member: Optional[str] = None  # specialty_ru → med_commission_member
    doctor_name: Optional[str] = None
    conclusion: Optional[str] = None
    diagnosis_text: Optional[str] = None
    diagnosis_accompany_id: Optional[str] = None  # icd10_code → diagnosis_accompany_id
    valid_category: Optional[str] = None  # category → valid_category
    examination_date: Optional[datetime] = None
    is_saved: bool = True
    # Детальные поля осмотра
    complain: Optional[str] = None  # complaints → complain
    anamnesis: Optional[str] = None
    objective_data: Optional[str] = None
    special_research_results: Optional[str] = None
    # Специфичные поля для офтальмолога
    od_vision_without_correction: Optional[float] = None
    os_vision_without_correction: Optional[float] = None
    # Специфичное поле для стоматолога
    dentist_json: Optional[dict] = None

    class Config:
        from_attributes = True


class ConscriptResponse(BaseModel):
    """Модель ответа с данными призывника"""
    id: str
    iin: str
    full_name: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    birth_date: str
    phone: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    draft_number: Optional[str] = None
    draft_date: Optional[str] = None
    graph: Optional[int] = None  # Основной граф (1-4) для API валидации
    category_graph_id: Optional[int] = None  # ID подгруппы (1-19) для UI селекта
    recruitment_center: Optional[str] = None
    status: str
    medical_commission_date: Optional[str] = None
    examinations: List[ExaminationSimple] = []
    examination_complete: bool = False
    missing_specialists: List[str] = []

    class Config:
        from_attributes = True


class ConscriptsListResponse(BaseModel):
    """Модель ответа со списком призывников"""
    total: int
    conscripts: List[ConscriptResponse]


class SpecialistStatsResponse(BaseModel):
    """Статистика по специалисту"""
    specialty: str
    total_examinations: int
    completed: int
    in_progress: int
    pending: int


# ========== ENDPOINTS ==========

@router.get("/", response_model=ConscriptsListResponse)
async def get_all_conscripts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Фильтр по статусу: in_progress, completed, pending"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список всех призывников с их освидетельствованиями

    Args:
        skip: Количество записей для пропуска (для пагинации)
        limit: Максимальное количество записей
        status: Фильтр по статусу (не используется после удаления conscript_drafts)
        db: Сессия БД

    Returns:
        Список призывников с полными данными
    """
    # Базовый запрос - теперь без join к conscript_drafts
    query = select(Conscript)

    # Подсчет общего количества
    count_query = select(func.count()).select_from(Conscript)
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Получение записей с пагинацией
    query = (
        query
        .offset(skip)
        .limit(limit)
        .order_by(Conscript.last_name, Conscript.first_name)
        .options(selectinload(Conscript.specialist_examinations))
    )
    result = await db.execute(query)
    conscripts = result.scalars().unique().all()

    # Формирование ответа
    conscripts_data = []
    for conscript in conscripts:
        # Получаем заключения специалистов напрямую
        exam_query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript.id
        ).order_by(SpecialistExamination.specialty)
        exam_result = await db.execute(exam_query)
        examinations = exam_result.scalars().all()

        # Проверка полноты освидетельствования
        completeness = await examination_checker.check_completeness(db, conscript.id)

        # Определяем статус на основе completeness
        if completeness.is_complete:
            conscript_status = "completed"
        elif completeness.total_completed > 0:
            conscript_status = "in_progress"
        else:
            conscript_status = "pending"

        # Формируем полное имя
        full_name_parts = [conscript.last_name, conscript.first_name]
        if conscript.middle_name:
            full_name_parts.append(conscript.middle_name)
        full_name = " ".join(full_name_parts).upper()

        # Формируем список заключений
        examinations_data = []
        for exam in examinations:
            examinations_data.append(ExaminationSimple(
                id=str(exam.id),
                specialty=exam.specialty,
                med_commission_member=exam.med_commission_member,
                doctor_name=exam.doctor_name,
                conclusion=exam.diagnosis_text,
                diagnosis_text=exam.diagnosis_text,
                diagnosis_accompany_id=exam.diagnosis_accompany_id,
                valid_category=exam.valid_category,
                examination_date=exam.examination_date,
                is_saved=True,
                # Детальные поля осмотра
                complain=exam.complain,
                anamnesis=exam.anamnesis,
                objective_data=exam.objective_data,
                special_research_results=exam.special_research_results,
                # Специфичные поля для офтальмолога
                od_vision_without_correction=exam.od_vision_without_correction,
                os_vision_without_correction=exam.os_vision_without_correction,
                # Специфичное поле для стоматолога
                dentist_json=exam.dentist_json
            ))

        conscripts_data.append(ConscriptResponse(
            id=str(conscript.id),
            iin=conscript.iin,
            full_name=full_name,
            first_name=conscript.first_name,
            last_name=conscript.last_name,
            middle_name=conscript.middle_name,
            birth_date=str(conscript.date_of_birth),
            phone=conscript.phone,
            address=conscript.address,
            photo_url=conscript.photo_url,
            draft_number=None,  # Нет больше draft_name
            draft_date=None,  # Нет больше draft info
            graph=None,  # Граф теперь не используется
            category_graph_id=None,  # Без conscript_drafts
            recruitment_center=None,  # Нет commission_location
            status=conscript_status,  # Вычисляется на основе completeness
            medical_commission_date=None,  # Нет commission_date
            examinations=examinations_data,
            examination_complete=completeness.is_complete,
            missing_specialists=completeness.missing_specialists
        ))

    return ConscriptsListResponse(
        total=total,
        conscripts=conscripts_data
    )


@router.get("/{conscript_id}", response_model=ConscriptResponse)
async def get_conscript_by_id(
    conscript_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить данные конкретного призывника по ID

    Args:
        conscript_id: UUID призывника
        db: Сессия БД

    Returns:
        Данные призывника с заключениями
    """
    # Получаем призывника напрямую
    query = select(Conscript).where(Conscript.id == conscript_id)
    result = await db.execute(query)
    conscript = result.scalar_one_or_none()

    if not conscript:
        raise HTTPException(status_code=404, detail="Призывник не найден")

    # Получаем заключения специалистов напрямую
    exam_query = select(SpecialistExamination).where(
        SpecialistExamination.conscript_draft_id == conscript.id
    ).order_by(SpecialistExamination.specialty)
    exam_result = await db.execute(exam_query)
    examinations = exam_result.scalars().all()

    # Проверка полноты освидетельствования
    completeness = await examination_checker.check_completeness(db, conscript.id)

    # Определяем статус на основе completeness
    if completeness.is_complete:
        conscript_status = "completed"
    elif completeness.total_completed > 0:
        conscript_status = "in_progress"
    else:
        conscript_status = "pending"

    # Формируем полное имя
    full_name_parts = [conscript.last_name, conscript.first_name]
    if conscript.middle_name:
        full_name_parts.append(conscript.middle_name)
    full_name = " ".join(full_name_parts).upper()

    # Формируем список заключений
    examinations_data = []
    for exam in examinations:
        examinations_data.append(ExaminationSimple(
            id=str(exam.id),
            specialty=exam.specialty,
            med_commission_member=exam.med_commission_member,
            doctor_name=exam.doctor_name,
            conclusion=exam.diagnosis_text,
            diagnosis_text=exam.diagnosis_text,
            diagnosis_accompany_id=exam.diagnosis_accompany_id,
            valid_category=exam.valid_category,
            examination_date=exam.examination_date,
            is_saved=True,
            # Детальные поля осмотра
            complain=exam.complain,
            anamnesis=exam.anamnesis,
            objective_data=exam.objective_data,
            special_research_results=exam.special_research_results,
            # Специфичные поля для офтальмолога
            od_vision_without_correction=exam.od_vision_without_correction,
            os_vision_without_correction=exam.os_vision_without_correction,
            # Специфичное поле для стоматолога
            dentist_json=exam.dentist_json
        ))

    return ConscriptResponse(
        id=str(conscript.id),
        iin=conscript.iin,
        full_name=full_name,
        first_name=conscript.first_name,
        last_name=conscript.last_name,
        middle_name=conscript.middle_name,
        birth_date=str(conscript.date_of_birth),
        phone=conscript.phone,
        address=conscript.address,
        draft_number=None,
        draft_date=None,
        graph=None,
        category_graph_id=None,
        recruitment_center=None,
        status=conscript_status,  # Вычисляется на основе completeness
        medical_commission_date=None,
        examinations=examinations_data,
        examination_complete=completeness.is_complete,
        missing_specialists=completeness.missing_specialists
    )


@router.get("/specialists/{specialty}/stats", response_model=SpecialistStatsResponse)
async def get_specialist_stats(
    specialty: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить статистику по конкретному специалисту

    Args:
        specialty: Название специальности
        db: Сессия БД

    Returns:
        Статистика: всего осмотров, завершено, в процессе, ожидает
    """
    # Получаем всех призывников
    conscripts_query = select(Conscript)
    conscripts_result = await db.execute(conscripts_query)
    conscripts = conscripts_result.scalars().all()

    total_examinations = len(conscripts)
    completed = 0
    pending = 0
    in_progress = 0

    for conscript in conscripts:
        # Проверяем наличие заключения от данного специалиста
        exam_query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript.id,
            SpecialistExamination.specialty == specialty
        )
        exam_result = await db.execute(exam_query)
        exam = exam_result.scalar_one_or_none()

        if exam:
            # Если заключение есть и сохранено
            if exam.diagnosis_accompany_id and exam.diagnosis_text and exam.valid_category:
                completed += 1
            else:
                in_progress += 1
        else:
            # Заключения нет
            pending += 1

    return SpecialistStatsResponse(
        specialty=specialty,
        total_examinations=total_examinations,
        completed=completed,
        in_progress=in_progress,
        pending=pending
    )


@router.get("/specialists/{specialty}/examinations")
async def get_examinations_by_specialist(
    specialty: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить все освидетельствования конкретного специалиста

    Args:
        specialty: Название специальности
        db: Сессия БД

    Returns:
        Список освидетельствований с данными призывников
    """
    # Получаем все заключения данного специалиста
    query = select(SpecialistExamination).where(
        SpecialistExamination.specialty == specialty
    ).order_by(SpecialistExamination.examination_date.desc())

    result = await db.execute(query)
    examinations = result.scalars().all()

    examinations_data = []
    for exam in examinations:
        # Получаем призывника напрямую
        conscript_query = select(Conscript).where(Conscript.id == exam.conscript_draft_id)
        conscript_result = await db.execute(conscript_query)
        conscript = conscript_result.scalar_one_or_none()

        if not conscript:
            continue

        # Формируем полное имя
        full_name_parts = [conscript.last_name, conscript.first_name]
        if conscript.middle_name:
            full_name_parts.append(conscript.middle_name)
        full_name = " ".join(full_name_parts).upper()

        # Определяем статус
        status = "completed" if (exam.diagnosis_accompany_id and exam.diagnosis_text and exam.valid_category) else "in_progress"

        examinations_data.append({
            "conscript_id": str(conscript.id),
            "conscript_name": full_name,
            "conscript_iin": conscript.iin,
            "examination_date": exam.examination_date.isoformat() if exam.examination_date else None,
            "diagnosis": exam.diagnosis_text or "Ожидает осмотра",
            "category": exam.valid_category or "-",
            "status": status
        })

    return examinations_data


@router.post("/{conscript_id}/upload-photo")
async def upload_conscript_photo(
    conscript_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Загрузить фото призывника
    """
    try:
        # Проверка существования призывника
        query = select(Conscript).where(Conscript.id == conscript_id)
        result = await db.execute(query)
        conscript = result.scalar_one_or_none()

        if not conscript:
            raise HTTPException(status_code=404, detail=f"Призывник с ID {conscript_id} не найден")

        # Проверка типа файла
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        file_extension = Path(file.filename).suffix.lower()

        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Недопустимый формат файла. Разрешены: {', '.join(allowed_extensions)}"
            )

        # Создание директории для загрузок
        upload_dir = Path("/app/uploads/photos")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Генерация уникального имени файла
        unique_filename = f"{conscript_id}_{uuid_lib.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename

        # Сохранение файла
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Обновление URL фото в БД
        photo_url = f"/uploads/photos/{unique_filename}"
        stmt = (
            update(Conscript)
            .where(Conscript.id == conscript_id)
            .values(photo_url=photo_url)
        )
        await db.execute(stmt)
        await db.commit()

        return {
            "status": "success",
            "message": "Фото успешно загружено",
            "photo_url": photo_url,
            "conscript_id": conscript_id
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки фото: {str(e)}"
        )


@router.get("/{conscript_id}/photo")
async def get_conscript_photo(
    conscript_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить URL фото призывника
    """
    try:
        query = select(Conscript.photo_url).where(Conscript.id == conscript_id)
        result = await db.execute(query)
        photo_url = result.scalar_one_or_none()

        if photo_url is None:
            raise HTTPException(status_code=404, detail="Фото не найдено")

        return {
            "conscript_id": conscript_id,
            "photo_url": photo_url
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения фото: {str(e)}"
        )
