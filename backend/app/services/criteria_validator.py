"""
Сервис строгой валидации по справочникам Приказа №722
Проверяет существование статей, подпунктов и соответствие критериям
"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.reference import PointDiagnosis, PointCriterion, CategoryDictionary

logger = logging.getLogger(__name__)


class CriteriaValidationResult:
    """Результат валидации критерия"""

    def __init__(
        self,
        is_valid: bool,
        article: Optional[int] = None,
        subpoint: Optional[str] = None,
        error_message: Optional[str] = None,
        matched_criteria: Optional[List[Dict[str, Any]]] = None,
        categories: Optional[Dict[int, str]] = None
    ):
        self.is_valid = is_valid
        self.article = article
        self.subpoint = subpoint
        self.error_message = error_message
        self.matched_criteria = matched_criteria or []
        self.categories = categories or {}  # {graph: category}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "article": self.article,
            "subpoint": self.subpoint,
            "error_message": self.error_message,
            "matched_criteria": self.matched_criteria,
            "categories": self.categories
        }


class CriteriaValidator:
    """
    Универсальный валидатор критериев по справочникам
    Приоритет: Справочники > AI анализ
    """

    @staticmethod
    async def validate_article_subpoint(
        db: AsyncSession,
        article: int,
        subpoint: str
    ) -> CriteriaValidationResult:
        """
        Проверка существования статьи и подпункта в справочнике

        ВАЖНО: Категории берутся из points_diagnoses (Приложение 1),
        а критерии из point_criteria (Приложение 2)

        Args:
            db: Сессия БД
            article: Номер статьи
            subpoint: Подпункт

        Returns:
            CriteriaValidationResult с результатом проверки
        """
        try:
            subpoint_str = str(subpoint) if subpoint is not None else None

            # СПЕЦИАЛЬНАЯ ОБРАБОТКА: для статей БЕЗ подпунктов (subpoint is None или пустая строка)
            # Некоторые статьи (например, статья 88 - Энурез) не имеют подпунктов
            # В БД их subpoint может быть NULL или пустой строкой
            if subpoint is None or subpoint == "" or subpoint == "null" or subpoint == "None":
                # Ищем запись без подпункта (subpoint IS NULL или subpoint = '')
                query_criteria = select(PointCriterion).where(
                    PointCriterion.article == article,
                    (PointCriterion.subpoint.is_(None)) | (PointCriterion.subpoint == '') | (PointCriterion.subpoint == 'null')
                ).limit(1)
                result_criteria = await db.execute(query_criteria)
                point_criterion = result_criteria.scalar_one_or_none()

                query_diagnoses = select(PointDiagnosis).where(
                    PointDiagnosis.article == article,
                    (PointDiagnosis.subpoint.is_(None)) | (PointDiagnosis.subpoint == '') | (PointDiagnosis.subpoint == 'null')
                ).limit(1)
                result_diagnoses = await db.execute(query_diagnoses)
                point_diagnosis = result_diagnoses.scalar_one_or_none()
            else:
                # Обычный поиск с конкретным подпунктом
                query_criteria = select(PointCriterion).where(
                    PointCriterion.article == article,
                    PointCriterion.subpoint == subpoint_str
                ).limit(1)
                result_criteria = await db.execute(query_criteria)
                point_criterion = result_criteria.scalar_one_or_none()

                query_diagnoses = select(PointDiagnosis).where(
                    PointDiagnosis.article == article,
                    PointDiagnosis.subpoint == subpoint_str
                ).limit(1)
                result_diagnoses = await db.execute(query_diagnoses)
                point_diagnosis = result_diagnoses.scalar_one_or_none()

            if not point_criterion and not point_diagnosis:
                return CriteriaValidationResult(
                    is_valid=False,
                    article=article,
                    subpoint=subpoint,
                    error_message=f"Подпункт {subpoint} статьи {article} НЕ СУЩЕСТВУЕТ в справочнике Приказа №722"
                )

            # Получаем категории для всех 4 графов из points_diagnoses (Приложение 1)
            categories = {}
            if point_diagnosis:
                categories = {
                    1: point_diagnosis.graph_1,
                    2: point_diagnosis.graph_2,
                    3: point_diagnosis.graph_3,
                    4: point_diagnosis.graph_4
                }
                logger.info(
                    f"🔍 ОТЛАДКА СТАТЬЯ 88: article={article}, subpoint={subpoint}, "
                    f"found_diagnosis={bool(point_diagnosis)}, categories={categories}"
                )
            else:
                logger.warning(
                    f"⚠️ ОТЛАДКА СТАТЬЯ 88: article={article}, subpoint={subpoint}, "
                    f"point_diagnosis=None (не найдено в points_diagnoses)"
                )

            return CriteriaValidationResult(
                is_valid=True,
                article=article,
                subpoint=subpoint,
                categories=categories
            )

        except Exception as e:
            logger.error(f"Ошибка при валидации статьи {article} подпункт {subpoint}: {e}")
            return CriteriaValidationResult(
                is_valid=False,
                article=article,
                subpoint=subpoint,
                error_message=f"Ошибка валидации: {str(e)}"
            )

    @staticmethod
    async def find_matching_criteria(
        db: AsyncSession,
        article: int,
        diagnosis_text: str,
        icd10_codes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск подходящих критериев для заданной статьи и диагноза

        Args:
            db: Сессия БД
            article: Номер статьи
            diagnosis_text: Текст диагноза
            icd10_codes: Коды МКБ-10

        Returns:
            Список подходящих критериев с подпунктами
        """
        try:
            # Получаем все критерии для данной статьи
            query = select(PointCriterion).where(
                PointCriterion.article == article
            ).order_by(PointCriterion.subpoint)

            result = await db.execute(query)
            criteria = result.scalars().all()

            matched = []
            diagnosis_lower = diagnosis_text.lower()

            for criterion in criteria:
                # Проверяем совпадение по ключевым словам
                keywords = criterion.keywords.split(", ") if criterion.keywords else []
                criteria_text_lower = criterion.description.lower()

                # Подсчитываем совпадения
                keyword_matches = sum(1 for kw in keywords if kw in diagnosis_lower)
                text_overlap = any(word in criteria_text_lower for word in diagnosis_lower.split() if len(word) > 3)

                if keyword_matches > 0 or text_overlap:
                    matched.append({
                        "article": criterion.article,
                        "subpoint": criterion.subpoint,
                        "criteria_text": criterion.description,
                        "keywords": keywords,
                        "quantitative_params": criterion.quantitative_params,
                        "match_score": keyword_matches
                    })

            # Сортируем по релевантности
            matched.sort(key=lambda x: x["match_score"], reverse=True)

            return matched

        except Exception as e:
            logger.error(f"Ошибка при поиске критериев для статьи {article}: {e}")
            return []

    @staticmethod
    async def validate_and_suggest(
        db: AsyncSession,
        article: int,
        subpoint: str,
        diagnosis_text: str,
        icd10_codes: Optional[List[str]] = None
    ) -> CriteriaValidationResult:
        """
        Валидация предложенного подпункта и предложение альтернатив

        Args:
            db: Сессия БД
            article: Номер статьи
            subpoint: Предложенный подпункт
            diagnosis_text: Текст диагноза
            icd10_codes: Коды МКБ-10

        Returns:
            CriteriaValidationResult с результатом и альтернативами
        """
        # Сначала валидируем предложенный подпункт
        validation_result = await CriteriaValidator.validate_article_subpoint(
            db, article, subpoint
        )

        if not validation_result.is_valid:
            # Ищем подходящие критерии
            matched_criteria = await CriteriaValidator.find_matching_criteria(
                db, article, diagnosis_text, icd10_codes
            )

            validation_result.matched_criteria = matched_criteria

            if matched_criteria:
                # Предлагаем наиболее релевантный подпункт
                best_match = matched_criteria[0]
                validation_result.error_message += (
                    f"\n\nВозможные подходящие подпункты:\n"
                    f"- Подпункт {best_match['subpoint']}: {best_match['criteria_text'][:100]}..."
                )

        return validation_result

    @staticmethod
    async def get_all_subpoints_for_article(
        db: AsyncSession,
        article: int
    ) -> List[str]:
        """
        Получение всех существующих подпунктов для статьи

        Args:
            db: Сессия БД
            article: Номер статьи

        Returns:
            Список подпунктов
        """
        try:
            query = select(PointCriterion.subpoint).where(
                PointCriterion.article == article
            ).distinct()

            result = await db.execute(query)
            subpoints = [row[0] for row in result.all()]

            return subpoints

        except Exception as e:
            logger.error(f"Ошибка при получении подпунктов для статьи {article}: {e}")
            return []

    @staticmethod
    async def get_category_for_article_subpoint(
        db: AsyncSession,
        article: int,
        subpoint: str,
        graph: int = 1
    ) -> Optional[str]:
        """
        Получение категории годности из справочника (НЕ от AI!)

        ВАЖНО: Категории берутся из points_diagnoses (Приложение 1)

        Args:
            db: Сессия БД
            article: Номер статьи
            subpoint: Подпункт
            graph: График (1-4)

        Returns:
            Категория годности или None
        """
        try:
            subpoint_str = str(subpoint) if subpoint is not None else None

            # Категории берём из points_diagnoses (Приложение 1)
            query = select(PointDiagnosis).where(
                PointDiagnosis.article == article,
                PointDiagnosis.subpoint == subpoint_str
            )
            result = await db.execute(query)
            point_diagnosis = result.scalar_one_or_none()

            if not point_diagnosis:
                return None

            category_map = {
                1: point_diagnosis.graph_1,
                2: point_diagnosis.graph_2,
                3: point_diagnosis.graph_3,
                4: point_diagnosis.graph_4
            }

            return category_map.get(graph)

        except Exception as e:
            logger.error(f"Ошибка при получении категории: {e}")
            return None

    @staticmethod
    async def get_category_description(
        db: AsyncSession,
        category_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Получение описания категории из справочника category_dictionary

        Args:
            db: Сессия БД
            category_code: Код категории (А, Б, В, Г, Д, Е, НГ, ИНД, В-ИНД)

        Returns:
            Словарь с описанием категории или None
        """
        if not category_code:
            return None

        try:
            # Нормализуем код (убираем пробелы)
            code = category_code.strip().upper()

            # Ищем по display_code
            query = select(CategoryDictionary).where(
                CategoryDictionary.display_code == code
            )
            result = await db.execute(query)
            category = result.scalar_one_or_none()

            if category:
                return {
                    "code": category.display_code,
                    "name": category.name_ru,
                    "description": category.description_ru,
                    "hierarchy_level": category.hierarchy_level
                }

            # Попробуем найти частичное совпадение (для НГ_ и т.п.)
            query = select(CategoryDictionary).where(
                CategoryDictionary.display_code.ilike(f"{code}%")
            )
            result = await db.execute(query)
            category = result.scalar_one_or_none()

            if category:
                return {
                    "code": category.display_code,
                    "name": category.name_ru,
                    "description": category.description_ru,
                    "hierarchy_level": category.hierarchy_level
                }

            return None

        except Exception as e:
            logger.error(f"Ошибка при получении описания категории '{category_code}': {e}")
            return None

    @staticmethod
    async def get_all_valid_categories(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Получение списка всех допустимых категорий

        Returns:
            Список категорий с описаниями
        """
        try:
            query = select(CategoryDictionary).order_by(CategoryDictionary.hierarchy_level)
            result = await db.execute(query)
            categories = result.scalars().all()

            return [
                {
                    "code": cat.display_code,
                    "name": cat.name_ru,
                    "description": cat.description_ru,
                    "hierarchy_level": cat.hierarchy_level
                }
                for cat in categories
            ]

        except Exception as e:
            logger.error(f"Ошибка при получении списка категорий: {e}")
            return []

    @staticmethod
    async def is_valid_category(db: AsyncSession, category_code: str) -> bool:
        """
        Проверка, является ли категория допустимой

        Args:
            category_code: Код категории

        Returns:
            True если категория существует в справочнике
        """
        if not category_code:
            return False

        description = await CriteriaValidator.get_category_description(db, category_code)
        return description is not None


# Глобальный экземпляр
criteria_validator = CriteriaValidator()
