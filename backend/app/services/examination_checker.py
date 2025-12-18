"""
Сервис проверки полноты медицинского освидетельствования
Проверяет, что все обязательные специалисты провели осмотр
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.models.medical import SpecialistExamination
from app.models.conscript import Conscript


# Обязательные специалисты для ВВК (согласно законодательству РК)
REQUIRED_SPECIALISTS = [
    "Терапевт",
    "Хирург",
    "Офтальмолог",
    "Невролог",
    "Отоларинголог",
    "Дерматолог",
    "Психиатр",
    "Стоматолог",
    "Фтизиатр",
]


class ExaminationCompleteness:
    """Результат проверки полноты освидетельствования"""

    def __init__(
        self,
        is_complete: bool,
        completed_specialists: List[str],
        missing_specialists: List[str],
        total_required: int,
        total_completed: int,
        missing_diagnoses: List[str] = None,
        missing_categories: List[str] = None
    ):
        self.is_complete = is_complete
        self.completed_specialists = completed_specialists
        self.missing_specialists = missing_specialists
        self.total_required = total_required
        self.total_completed = total_completed
        self.missing_diagnoses = missing_diagnoses or []
        self.missing_categories = missing_categories or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_complete": self.is_complete,
            "completed_specialists": self.completed_specialists,
            "missing_specialists": self.missing_specialists,
            "total_required": self.total_required,
            "total_completed": self.total_completed,
            "missing_diagnoses": self.missing_diagnoses,
            "missing_categories": self.missing_categories,
            "can_run_ai_analysis": self.is_complete and not self.missing_diagnoses and not self.missing_categories
        }


class ExaminationChecker:
    """Проверка полноты медицинского освидетельствования"""

    @staticmethod
    async def check_completeness(
        db: AsyncSession,
        conscript_draft_id: UUID
    ) -> ExaminationCompleteness:
        """
        Проверить полноту освидетельствования призывника

        Args:
            db: Сессия БД
            conscript_draft_id: ID призывника

        Returns:
            ExaminationCompleteness: Результат проверки
        """
        # Получаем все заключения специалистов для данного призывника
        query = select(SpecialistExamination).where(
            SpecialistExamination.conscript_draft_id == conscript_draft_id
        )
        result = await db.execute(query)
        examinations = result.scalars().all()

        # Проверяем валидность каждого обследования
        # Обследование считается завершенным, если:
        # 1. Есть med_commission_member (русское название специальности)
        # 2. Есть doctor_name (имя врача)
        # 3. Есть diagnosis_accompany_id (код МКБ-10)
        # 4. Есть diagnosis_text (текст диагноза)
        # 5. Есть conclusion_text (заключение)
        # 6. Есть valid_category (категория годности)

        valid_examinations = []
        invalid_examinations = []

        for exam in examinations:
            is_valid = (
                exam.med_commission_member and exam.med_commission_member.strip() != '' and
                exam.doctor_name and exam.doctor_name.strip() != '' and
                exam.diagnosis_accompany_id and exam.diagnosis_accompany_id.strip() != '' and
                exam.diagnosis_text and exam.diagnosis_text.strip() != '' and
                exam.conclusion_text and exam.conclusion_text.strip() != '' and
                exam.valid_category and exam.valid_category.strip() != ''
            )

            if is_valid:
                valid_examinations.append(exam)
            else:
                invalid_examinations.append(exam)

        # Получаем список специальностей, которые провели ВАЛИДНЫЙ осмотр
        completed_specialists = [exam.med_commission_member for exam in valid_examinations]

        # Определяем недостающих специалистов
        missing_specialists = [
            spec for spec in REQUIRED_SPECIALISTS
            if spec not in completed_specialists
        ]

        # Проверяем наличие диагноза и категории годности у невалидных обследований
        missing_diagnoses = []
        missing_categories = []

        for exam in invalid_examinations:
            specialty_name = exam.med_commission_member or exam.specialty

            # Проверяем отсутствие обязательных полей
            if not exam.diagnosis_accompany_id or not exam.diagnosis_accompany_id.strip():
                if specialty_name not in missing_diagnoses:
                    missing_diagnoses.append(specialty_name)

            if not exam.diagnosis_text or not exam.diagnosis_text.strip():
                if specialty_name not in missing_diagnoses:
                    missing_diagnoses.append(specialty_name)

            if not exam.conclusion_text or not exam.conclusion_text.strip():
                if specialty_name not in missing_diagnoses:
                    missing_diagnoses.append(specialty_name)

            if not exam.valid_category or not exam.valid_category.strip():
                if specialty_name not in missing_categories:
                    missing_categories.append(specialty_name)

            if not exam.doctor_name or not exam.doctor_name.strip():
                if specialty_name not in missing_categories:
                    missing_categories.append(specialty_name)

        # Определяем полноту
        is_complete = len(missing_specialists) == 0 and len(invalid_examinations) == 0

        return ExaminationCompleteness(
            is_complete=is_complete,
            completed_specialists=completed_specialists,
            missing_specialists=missing_specialists,
            total_required=len(REQUIRED_SPECIALISTS),
            total_completed=len(completed_specialists),
            missing_diagnoses=missing_diagnoses,
            missing_categories=missing_categories
        )

    @staticmethod
    async def check_batch_completeness(
        db: AsyncSession,
        conscript_draft_ids: List[UUID]
    ) -> Dict[UUID, ExaminationCompleteness]:
        """
        Проверить полноту освидетельствования для нескольких призывников

        Args:
            db: Сессия БД
            conscript_draft_ids: Список ID призывников

        Returns:
            Словарь {conscript_draft_id: ExaminationCompleteness}
        """
        results = {}

        for draft_id in conscript_draft_ids:
            completeness = await ExaminationChecker.check_completeness(db, draft_id)
            results[draft_id] = completeness

        return results

    @staticmethod
    async def get_required_specialists() -> List[str]:
        """
        Получить список обязательных специалистов

        Returns:
            Список специальностей
        """
        return REQUIRED_SPECIALISTS.copy()


# Глобальный экземпляр
examination_checker = ExaminationChecker()
