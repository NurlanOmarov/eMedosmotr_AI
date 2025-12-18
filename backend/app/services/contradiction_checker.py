"""
Сервис проверки противоречий в медицинских заключениях
Реализация Этапа 0 из ARCHITECTURE_PRIKAS_722.md

Типы противоречий:
- TYPE_A: "Здоров" в диагнозе -> Болезнь в дополнительных полях
- TYPE_B: Болезнь в диагнозе -> "Здоров" в дополнительных полях
- TYPE_C: Болезнь A в диагнозе -> Болезнь B в дополнительных полях
- TYPE_D: Диагноз vs Неправильная категория
- TYPE_E: "Здоров" + категория != "А" (логическая ошибка)
- TYPE_F: Тяжелый диагноз + категория "А" (явное несоответствие)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass, field
from enum import Enum
import logging

from app.services.rag_service import rag_service
from app.services.ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


class ContradictionType(str, Enum):
    """Типы противоречий согласно ARCHITECTURE_PRIKAS_722.md"""
    TYPE_A = "TYPE_A_HEALTHY_VS_DISEASE"
    TYPE_B = "TYPE_B_DISEASE_VS_HEALTHY"
    TYPE_C = "TYPE_C_DISEASE_A_VS_DISEASE_B"
    TYPE_D = "TYPE_D_CATEGORY_MISMATCH"
    TYPE_E = "TYPE_E_LOGICAL_ERROR"
    TYPE_F = "TYPE_F_OBVIOUS_CATEGORY_MISMATCH"


class Severity(str, Enum):
    """Уровни серьезности противоречий"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ContradictionResult:
    """Результат проверки на противоречия"""
    has_contradiction: bool
    contradiction_type: Optional[ContradictionType] = None
    severity: Severity = Severity.LOW
    description: str = ""
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    rag_matches: List[Dict[str, Any]] = field(default_factory=list)
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для API"""
        return {
            "has_contradiction": self.has_contradiction,
            "contradiction_type": self.contradiction_type.value if self.contradiction_type else None,
            "severity": self.severity.value,
            "description": self.description,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "source_value": self.source_value,
            "target_value": self.target_value,
            "rag_matches": self.rag_matches,
            "recommendation": self.recommendation
        }


class ContradictionChecker:
    """
    Сервис проверки противоречий в медицинском заключении (Этап 0)

    Задача: Выявить несоответствия между разными частями заключения врача.
    Система НЕ определяет истину, а СИГНАЛИЗИРУЕТ о противоречиях.
    """

    def __init__(self):
        self.healthy_keywords = AIAnalyzer.get_healthy_keywords()
        self.pathology_keywords = AIAnalyzer.get_pathology_keywords()
        self.severe_keywords = AIAnalyzer.get_severe_conditions_keywords()

    def _is_healthy_text(self, text: str) -> bool:
        """
        Проверка, указывает ли текст на здоровый статус

        Args:
            text: Текст для проверки

        Returns:
            True если текст указывает на здоровье
        """
        if not text:
            return False

        text_lower = text.lower()

        # Проверяем наличие ключевых слов здоровья
        has_healthy_keyword = any(
            keyword in text_lower
            for keyword in self.healthy_keywords
        )

        if not has_healthy_keyword:
            return False

        # Проверяем, нет ли патологий БЕЗ отрицания
        for keyword in self.pathology_keywords:
            if keyword in text_lower:
                keyword_pos = text_lower.find(keyword)
                context_before = text_lower[max(0, keyword_pos - 20):keyword_pos]
                negation_words = ["не ", "нет ", "без ", "отсутств"]
                has_negation = any(neg in context_before for neg in negation_words)
                if not has_negation:
                    return False

        return True

    def _contains_severe_condition(self, text: str) -> tuple[bool, Optional[str]]:
        """
        Проверка на наличие тяжелых заболеваний в тексте

        ВАЖНО: Учитывает контекст отрицания (например: "туберкулез не выявлен")
        Проверяет отрицание как ДО, так и ПОСЛЕ ключевого слова

        Args:
            text: Текст для проверки

        Returns:
            (True/False, найденное ключевое слово)
        """
        if not text:
            return False, None

        text_lower = text.lower()
        for keyword in self.severe_keywords:
            if keyword in text_lower:
                keyword_pos = text_lower.find(keyword)
                keyword_end = keyword_pos + len(keyword)

                # Контекст ДО ключевого слова (25 символов)
                context_before = text_lower[max(0, keyword_pos - 25):keyword_pos]

                # Контекст ПОСЛЕ ключевого слова (30 символов)
                context_after = text_lower[keyword_end:min(len(text_lower), keyword_end + 30)]

                # Слова отрицания ДО (например: "нет туберкулеза", "без туберкулеза")
                negation_before = ["не ", "нет ", "без ", "отсутств", "исключ"]
                has_negation_before = any(neg in context_before for neg in negation_before)

                # Слова отрицания ПОСЛЕ (например: "туберкулез не выявлен", "туберкулез исключен")
                negation_after = [" не ", " нет", " отсутств", " исключ", " не обнаруж", " не выявл"]
                has_negation_after = any(neg in context_after for neg in negation_after)

                # Если есть отрицание до ИЛИ после - пропускаем
                if has_negation_before or has_negation_after:
                    continue

                # Если отрицания нет - это действительно тяжелое заболевание
                return True, keyword

        return False, None

    async def check_for_contradictions(
        self,
        db: AsyncSession,
        diagnosis_text: str,
        doctor_category: str,
        anamnesis: Optional[str] = None,
        complaints: Optional[str] = None,
        objective_data: Optional[str] = None,
        special_research_results: Optional[str] = None,
        doctor_notes: Optional[str] = None,
        icd10_codes: Optional[List[str]] = None,
        graph: int = 1
    ) -> List[ContradictionResult]:
        """
        Главный метод проверки всех типов противоречий

        Args:
            db: Сессия базы данных
            diagnosis_text: Текст диагноза
            doctor_category: Категория, поставленная врачом
            anamnesis: Анамнез
            complaints: Жалобы
            objective_data: Объективные данные
            special_research_results: Результаты исследований
            doctor_notes: Примечания врача
            icd10_codes: Коды МКБ-10
            graph: График призывника (1-4)

        Returns:
            Список найденных противоречий
        """
        contradictions = []

        # Собираем все дополнительные поля
        additional_fields = {
            "anamnesis": anamnesis,
            "complaints": complaints,
            "objective_data": objective_data,
            "special_research_results": special_research_results,
            "doctor_notes": doctor_notes
        }

        # Фильтруем пустые поля
        non_empty_fields = {
            k: v for k, v in additional_fields.items()
            if v and len(v.strip()) >= 10
        }

        # TYPE_E: "Здоров" + категория != "А" (проверяем первым - быстрая проверка)
        type_e = self._check_type_e(diagnosis_text, doctor_category)
        if type_e.has_contradiction:
            contradictions.append(type_e)

        # TYPE_F: Тяжелый диагноз + категория "А"
        type_f = self._check_type_f(diagnosis_text, doctor_category)
        if type_f.has_contradiction:
            contradictions.append(type_f)

        # TYPE_A: "Здоров" в диагнозе -> Болезнь в доп. полях
        type_a = await self._check_type_a(db, diagnosis_text, non_empty_fields)
        if type_a.has_contradiction:
            contradictions.append(type_a)

        # TYPE_B: Болезнь в диагнозе -> "Здоров" в доп. полях
        type_b = self._check_type_b(diagnosis_text, non_empty_fields)
        if type_b.has_contradiction:
            contradictions.append(type_b)

        # TYPE_C: Разные болезни в диагнозе и доп. полях
        type_c = await self._check_type_c(db, diagnosis_text, non_empty_fields)
        if type_c.has_contradiction:
            contradictions.append(type_c)

        # TYPE_D: Диагноз vs Неправильная категория (через RAG)
        type_d = await self._check_type_d(db, diagnosis_text, doctor_category, graph)
        if type_d.has_contradiction:
            contradictions.append(type_d)

        logger.info(
            f"Проверка противоречий завершена: найдено {len(contradictions)} противоречий"
        )

        return contradictions

    def _check_type_e(
        self,
        diagnosis_text: str,
        doctor_category: str
    ) -> ContradictionResult:
        """
        TYPE_E: Логическая ошибка - "Здоров" + категория != "А"

        Если врач указал "здоров", но поставил категорию отличную от "А"
        """
        is_healthy = self._is_healthy_text(diagnosis_text)
        category_upper = doctor_category.upper().strip()

        # Здоров, но категория не А
        if is_healthy and category_upper not in ["А", "A"]:
            return ContradictionResult(
                has_contradiction=True,
                contradiction_type=ContradictionType.TYPE_E,
                severity=Severity.HIGH,
                description=(
                    f"ЛОГИЧЕСКАЯ ОШИБКА: Диагноз указывает 'Здоров', "
                    f"но категория годности '{doctor_category}' вместо 'А'. "
                    f"Если призывник здоров, категория должна быть только 'А'."
                ),
                source_field="diagnosis_text",
                target_field="doctor_category",
                source_value=diagnosis_text[:200],
                target_value=doctor_category,
                recommendation="Уточнить диагноз или исправить категорию годности"
            )

        return ContradictionResult(has_contradiction=False)

    def _check_type_f(
        self,
        diagnosis_text: str,
        doctor_category: str
    ) -> ContradictionResult:
        """
        TYPE_F: Явное несоответствие - Тяжелый диагноз + категория "А"

        Если в диагнозе указано тяжелое заболевание, но категория "А"
        """
        category_upper = doctor_category.upper().strip()

        # Проверяем только если категория "А"
        if category_upper not in ["А", "A"]:
            return ContradictionResult(has_contradiction=False)

        # Ищем тяжелые заболевания в диагнозе
        has_severe, found_keyword = self._contains_severe_condition(diagnosis_text)

        if has_severe:
            return ContradictionResult(
                has_contradiction=True,
                contradiction_type=ContradictionType.TYPE_F,
                severity=Severity.CRITICAL,
                description=(
                    f"КРИТИЧЕСКАЯ ОШИБКА: Диагноз содержит признаки тяжелого заболевания "
                    f"('{found_keyword}'), но категория годности 'А' (полностью годен). "
                    f"Тяжелые заболевания несовместимы с категорией 'А'."
                ),
                source_field="diagnosis_text",
                target_field="doctor_category",
                source_value=diagnosis_text[:300],
                target_value=doctor_category,
                recommendation=(
                    "СРОЧНО: Пересмотреть категорию годности. "
                    "Вероятна механическая ошибка при заполнении."
                )
            )

        return ContradictionResult(has_contradiction=False)

    async def _check_type_a(
        self,
        db: AsyncSession,
        diagnosis_text: str,
        additional_fields: Dict[str, str]
    ) -> ContradictionResult:
        """
        TYPE_A: "Здоров" в диагнозе -> Болезнь в дополнительных полях

        Используем RAG для поиска заболеваний в дополнительных полях
        """
        # Проверяем, что диагноз = "здоров"
        if not self._is_healthy_text(diagnosis_text):
            return ContradictionResult(has_contradiction=False)

        # Ищем болезни в дополнительных полях через RAG
        for field_name, field_value in additional_fields.items():
            # Пропускаем если поле тоже указывает на здоровье
            if self._is_healthy_text(field_value):
                continue

            diseases = await rag_service.search_diseases_in_text(
                db=db,
                text=field_value,
                top_k=3,
                similarity_threshold=0.70  # Высокий порог для точности
            )

            if diseases:
                # Определяем серьезность по найденным категориям
                severity = Severity.HIGH
                for disease in diseases:
                    categories = disease.get("categories", {})
                    if categories.get(1) in ["Д", "Е", "НГ"]:
                        severity = Severity.CRITICAL
                        break

                return ContradictionResult(
                    has_contradiction=True,
                    contradiction_type=ContradictionType.TYPE_A,
                    severity=severity,
                    description=(
                        f"ПРОТИВОРЕЧИЕ: Диагноз указывает 'Здоров', "
                        f"но в поле '{field_name}' обнаружены признаки заболеваний. "
                        f"Найдено {len(diseases)} совпадений с критериями Приказа 722."
                    ),
                    source_field="diagnosis_text",
                    target_field=field_name,
                    source_value=diagnosis_text[:200],
                    target_value=field_value[:200],
                    rag_matches=diseases,
                    recommendation=(
                        "Требуется уточнение: актуально ли заболевание "
                        "или это история болезни (вылечен)."
                    )
                )

        return ContradictionResult(has_contradiction=False)

    def _check_type_b(
        self,
        diagnosis_text: str,
        additional_fields: Dict[str, str]
    ) -> ContradictionResult:
        """
        TYPE_B: Болезнь в диагнозе -> "Здоров" в дополнительных полях

        Врач поставил диагноз, но в примечаниях пишет "здоров"
        """
        # Проверяем, что диагноз НЕ здоров (есть болезнь)
        if self._is_healthy_text(diagnosis_text):
            return ContradictionResult(has_contradiction=False)

        # Ищем "здоров" в дополнительных полях
        for field_name, field_value in additional_fields.items():
            if self._is_healthy_text(field_value):
                return ContradictionResult(
                    has_contradiction=True,
                    contradiction_type=ContradictionType.TYPE_B,
                    severity=Severity.MEDIUM,
                    description=(
                        f"ПРОТИВОРЕЧИЕ: В диагнозе указано заболевание, "
                        f"но в поле '{field_name}' указано, что призывник здоров. "
                        f"Возможно, это контекст 'общее состояние удовлетворительное' "
                        f"или ошибка в диагнозе."
                    ),
                    source_field="diagnosis_text",
                    target_field=field_name,
                    source_value=diagnosis_text[:200],
                    target_value=field_value[:200],
                    recommendation=(
                        "Уточнить: относится ли 'здоров' к общему состоянию "
                        "или врач ошибся в диагнозе."
                    )
                )

        return ContradictionResult(has_contradiction=False)

    async def _check_type_c(
        self,
        db: AsyncSession,
        diagnosis_text: str,
        additional_fields: Dict[str, str]
    ) -> ContradictionResult:
        """
        TYPE_C: Разные болезни - Болезнь A в диагнозе -> Болезнь B в доп. полях

        Врач ставит одно заболевание, но в анамнезе упоминается другое (более серьезное)
        """
        # Проверяем, что диагноз НЕ здоров
        if self._is_healthy_text(diagnosis_text):
            return ContradictionResult(has_contradiction=False)

        # Ищем заболевания в диагнозе
        diagnosis_diseases = await rag_service.search_diseases_in_text(
            db=db,
            text=diagnosis_text,
            top_k=2,
            similarity_threshold=0.65
        )

        if not diagnosis_diseases:
            return ContradictionResult(has_contradiction=False)

        diagnosis_article = diagnosis_diseases[0].get("article") if diagnosis_diseases else None

        # Ищем заболевания в дополнительных полях
        for field_name, field_value in additional_fields.items():
            # Пропускаем если поле указывает на здоровье
            if self._is_healthy_text(field_value):
                continue

            field_diseases = await rag_service.search_diseases_in_text(
                db=db,
                text=field_value,
                top_k=3,
                similarity_threshold=0.70
            )

            if not field_diseases:
                continue

            # Проверяем, есть ли другие статьи (отличные от диагноза)
            for disease in field_diseases:
                disease_article = disease.get("article")
                disease_categories = disease.get("categories", {})

                # Если это другая статья
                if disease_article and disease_article != diagnosis_article:
                    # Определяем серьезность по категории
                    diagnosis_category = diagnosis_diseases[0].get("categories", {}).get(1, "")
                    disease_category = disease_categories.get(1, "")

                    # Иерархия категорий (чем выше, тем хуже)
                    category_severity = {
                        "А": 1, "Б": 2, "В": 3, "В-ИНД": 3,
                        "Г": 4, "Д": 5, "Е": 6, "НГ": 7
                    }

                    diagnosis_sev = category_severity.get(diagnosis_category, 0)
                    disease_sev = category_severity.get(disease_category, 0)

                    # Если заболевание в доп. полях серьезнее
                    if disease_sev > diagnosis_sev:
                        severity = Severity.CRITICAL if disease_sev >= 5 else Severity.HIGH

                        return ContradictionResult(
                            has_contradiction=True,
                            contradiction_type=ContradictionType.TYPE_C,
                            severity=severity,
                            description=(
                                f"ПРОТИВОРЕЧИЕ: В диагнозе указана статья {diagnosis_article} "
                                f"(категория {diagnosis_category}), но в поле '{field_name}' "
                                f"обнаружены признаки статьи {disease_article} "
                                f"(категория {disease_category}), которая серьезнее."
                            ),
                            source_field="diagnosis_text",
                            target_field=field_name,
                            source_value=diagnosis_text[:200],
                            target_value=field_value[:200],
                            rag_matches=[diagnosis_diseases[0], disease],
                            recommendation=(
                                f"Необходимо определить основной диагноз. "
                                f"Возможно, статья {disease_article} должна быть приоритетной."
                            )
                        )

        return ContradictionResult(has_contradiction=False)

    async def _check_type_d(
        self,
        db: AsyncSession,
        diagnosis_text: str,
        doctor_category: str,
        graph: int
    ) -> ContradictionResult:
        """
        TYPE_D: Диагноз vs Неправильная категория

        Используем RAG для определения ожидаемой категории и сравниваем с врачебной
        """
        # Не проверяем для здоровых
        if self._is_healthy_text(diagnosis_text):
            return ContradictionResult(has_contradiction=False)

        # Ищем заболевание в диагнозе через RAG
        diseases = await rag_service.search_diseases_in_text(
            db=db,
            text=diagnosis_text,
            top_k=1,
            similarity_threshold=0.70
        )

        if not diseases:
            return ContradictionResult(has_contradiction=False)

        best_match = diseases[0]
        expected_category = best_match.get("categories", {}).get(graph)

        if not expected_category:
            return ContradictionResult(has_contradiction=False)

        # Нормализуем категории для сравнения
        doctor_cat_normalized = doctor_category.upper().strip()
        expected_cat_normalized = expected_category.upper().strip()

        # Сравниваем категории
        if doctor_cat_normalized != expected_cat_normalized:
            # Определяем серьезность расхождения
            category_severity = {
                "А": 1, "Б": 2, "В": 3, "В-ИНД": 3,
                "Г": 4, "Д": 5, "Е": 6, "НГ": 7
            }

            doctor_sev = category_severity.get(doctor_cat_normalized, 0)
            expected_sev = category_severity.get(expected_cat_normalized, 0)

            # Критическое расхождение если разница >= 2 уровней
            if abs(doctor_sev - expected_sev) >= 2:
                severity = Severity.CRITICAL
            else:
                severity = Severity.HIGH

            return ContradictionResult(
                has_contradiction=True,
                contradiction_type=ContradictionType.TYPE_D,
                severity=severity,
                description=(
                    f"НЕСООТВЕТСТВИЕ КАТЕГОРИИ: Врач поставил категорию '{doctor_category}', "
                    f"но по статье {best_match['article']}, подпункт {best_match['subpoint']} "
                    f"для графа {graph} ожидается категория '{expected_category}'."
                ),
                source_field="doctor_category",
                target_field="handbook_category",
                source_value=doctor_category,
                target_value=expected_category,
                rag_matches=[best_match],
                recommendation=(
                    f"Проверить соответствие категории Приказу 722, "
                    f"статья {best_match['article']}, подпункт {best_match['subpoint']}."
                )
            )

        return ContradictionResult(has_contradiction=False)


# Глобальный экземпляр сервиса
contradiction_checker = ContradictionChecker()
