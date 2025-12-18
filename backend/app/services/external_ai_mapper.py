"""
Сервис для подготовки данных для отправки во внешний AI сервер
Маппинг структуры БД → формат API внешнего сервиса
"""

from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conscript import AnthropometricData, Conscript
from app.models.medical import SpecialistExamination


async def prepare_external_ai_request(
    conscript_draft_id: UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Подготовка полного пакета данных для отправки во внешний AI сервер

    Args:
        conscript_draft_id: UUID призывника
        db: Async сессия БД

    Returns:
        dict: Данные в формате API внешнего сервиса

    Raises:
        ValueError: Если призывник не найден

    Example:
        >>> data = await prepare_external_ai_request(conscript_id, db)
        >>> # Отправить на внешний сервер
        >>> response = await httpx.post("http://ai-server/analyze", json=data)
    """

    # 1. Загрузить призывника
    conscript_result = await db.execute(
        select(Conscript)
        .where(Conscript.id == conscript_draft_id)
    )
    conscript = conscript_result.scalar_one_or_none()

    if not conscript:
        raise ValueError(f"Призывник с ID {conscript_draft_id} не найден")

    # 2. Загрузить антропометрические данные
    anthro_result = await db.execute(
        select(AnthropometricData)
        .where(AnthropometricData.conscript_draft_id == conscript_draft_id)
    )
    anthro = anthro_result.scalar_one_or_none()

    # 3. Загрузить все заключения специалистов
    exams_result = await db.execute(
        select(SpecialistExamination)
        .where(SpecialistExamination.conscript_draft_id == conscript_draft_id)
        .order_by(SpecialistExamination.created_at)
    )
    examinations = exams_result.scalars().all()

    # 4. Сформировать JSON для внешнего API
    return {
        "conscript_draft": {
            "id": str(conscript.id),
            "conscript_id": conscript.iin,  # ИИН призывника
            "draft": "Текущий призыв",  # Без истории призывов
            "conscript_status": "pending",  # Статус по умолчанию
            "category_graph": {
                "graph": 1,
                "id": 1
            }
        },

        "anthropometic_data": _map_anthropometric_data(anthro),  # Опечатка в API: "anthropometic"

        "specialists_examinations": [
            _map_examination_to_api(exam) for exam in examinations
        ]
    }


def _map_anthropometric_data(anthro: AnthropometricData | None) -> Dict[str, Any]:
    """
    Маппинг антропометрических данных

    Args:
        anthro: Объект AnthropometricData из БД или None

    Returns:
        dict: Данные в формате API
    """
    if not anthro:
        return {
            "height": None,
            "weight": None,
            "bmi": None
        }

    return {
        "height": float(anthro.height) if anthro.height else None,
        "weight": float(anthro.weight) if anthro.weight else None,
        "bmi": float(anthro.bmi) if anthro.bmi else None
    }


def _map_examination_to_api(exam: SpecialistExamination) -> Dict[str, Any]:
    """
    Маппинг заключения одного специалиста в формат API

    Поля БД теперь соответствуют названиям API:
    - med_commission_member
    - valid_category
    - diagnosis_accompany_id
    - additional_act_comment
    - complain

    Args:
        exam: Объект SpecialistExamination из БД

    Returns:
        dict: Данные заключения в формате API
    """
    return {
        # Поля БД соответствуют API напрямую
        "med_commission_member": exam.med_commission_member or exam.specialty,
        "conscript_draft_id": str(exam.conscript_draft_id),
        "valid_category": exam.valid_category,
        "diagnosis_accompany_id": exam.diagnosis_accompany_id,

        # Прямые поля
        "objective_data": exam.objective_data,
        "special_research_results": exam.special_research_results,
        "additional_act_comment": exam.additional_act_comment,
        "complain": exam.complain,
        "anamnesis": exam.anamnesis,

        # Новые поля для офтальмолога
        "os_vision_without_correction": (
            str(exam.os_vision_without_correction)
            if exam.os_vision_without_correction is not None
            else None
        ),
        "od_vision_without_correction": (
            str(exam.od_vision_without_correction)
            if exam.od_vision_without_correction is not None
            else None
        ),

        # Новое поле для стоматолога
        "dentist_json": exam.dentist_json
    }


async def get_conscript_info(
    conscript_draft_id: UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Получить информацию о призывнике

    Args:
        conscript_draft_id: UUID призывника
        db: Async сессия БД

    Returns:
        dict: Информация о призывнике

    Example:
        >>> info = await get_conscript_info(conscript_id, db)
        >>> print(info)
        {
            'conscript_id': 'uuid...',
            'conscript_iin': '990101300001',
            'conscript_name': 'Иванов Иван',
            'examinations_count': 9
        }
    """
    # Загрузить призывника с заключениями
    result = await db.execute(
        select(Conscript)
        .options(
            selectinload(Conscript.specialist_examinations)
        )
        .where(Conscript.id == conscript_draft_id)
    )
    conscript = result.scalar_one_or_none()

    if not conscript:
        raise ValueError(f"Призывник {conscript_draft_id} не найден")

    return {
        'conscript_id': str(conscript.id),
        'conscript_iin': conscript.iin,
        'conscript_name': conscript.full_name,
        'examinations_count': len(conscript.specialist_examinations) if conscript.specialist_examinations else 0
    }


async def get_conscripts_ready_for_external_ai(
    db: AsyncSession,
    limit: int = 100
) -> List[UUID]:
    """
    Получить список призывников, готовых к отправке на внешний AI

    Критерии готовности:
    - Все обязательные специалисты провели осмотр
    - Есть антропометрические данные

    Args:
        db: Async сессия БД
        limit: Максимальное количество записей

    Returns:
        list[UUID]: Список ID призывников
    """
    # TODO: Реализовать логику проверки полноты данных
    # Можно использовать examination_checker.check_completeness()

    result = await db.execute(
        select(Conscript.id)
        .limit(limit)
    )

    return list(result.scalars().all())


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def validate_api_request(data: Dict[str, Any]) -> bool:
    """
    Валидация данных перед отправкой на внешний API

    Args:
        data: Подготовленные данные для API

    Returns:
        bool: True если данные валидны

    Raises:
        ValueError: Если обязательные поля отсутствуют
    """
    # Проверка обязательных полей
    if "conscript_draft" not in data:
        raise ValueError("Отсутствует поле 'conscript_draft'")

    if "anthropometic_data" not in data:
        raise ValueError("Отсутствует поле 'anthropometic_data'")

    if "specialists_examinations" not in data:
        raise ValueError("Отсутствует поле 'specialists_examinations'")

    if not data["specialists_examinations"]:
        raise ValueError("Список specialists_examinations пуст")

    # Проверка антропометрии
    anthro = data["anthropometic_data"]
    if not all(k in anthro for k in ["height", "weight", "bmi"]):
        raise ValueError("Неполные антропометрические данные")

    return True


def serialize_for_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Подготовка данных для JSON сериализации
    Конвертирует UUID, Decimal и другие типы в JSON-совместимые

    Args:
        data: Данные для сериализации

    Returns:
        dict: JSON-совместимые данные
    """
    import json
    from decimal import Decimal

    def default_serializer(obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError(f"Тип {type(obj)} не поддерживается")

    # Конвертируем через JSON для обработки всех типов
    json_str = json.dumps(data, default=default_serializer, ensure_ascii=False)
    return json.loads(json_str)
