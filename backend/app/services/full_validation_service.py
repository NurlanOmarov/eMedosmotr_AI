"""
Полная валидация заключения врача с проверкой противоречий
Объединяет Этап 0 + Этап 1 + Этап 2 согласно ARCHITECTURE_PRIKAS_722.md

Этап 0: Проверка противоречий (contradiction_checker)
Этап 1: Клиническая валидация (AI + Приложение 2)
Этап 2: Административная проверка (SQL + Приложение 1)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime
import logging
import uuid

from app.services.contradiction_checker import contradiction_checker, ContradictionResult
from app.services.ai_analyzer import ai_analyzer
from app.models.ai import AIAnalysisResult
from app.schemas.validation import (
    CheckDoctorConclusionResponse,
    ValidationStageResult,
    ContradictionDetail,
    RAGMatch,
    ContradictionTypeEnum,
    SeverityEnum,
    OverallStatusEnum,
    MatchStatusEnum
)

logger = logging.getLogger(__name__)


class FullValidationService:
    """
    Оркестратор полной трехэтапной валидации заключения врача

    Выполняет:
    1. Этап 0: Проверка противоречий
    2. Этап 1: Клиническая валидация (определение статьи/подпункта)
    3. Этап 2: Административная проверка (определение категории)

    Система НЕ определяет истину, а СИГНАЛИЗИРУЕТ о проблемах председателю комиссии.
    """

    async def full_validation_with_contradiction_check(
        self,
        db: AsyncSession,
        diagnosis_text: str,
        doctor_category: str,
        specialty: str,
        anamnesis: Optional[str] = None,
        complaints: Optional[str] = None,
        objective_data: Optional[str] = None,
        special_research_results: Optional[str] = None,
        conclusion_text: Optional[str] = None,
        doctor_notes: Optional[str] = None,
        icd10_codes: Optional[List[str]] = None,
        article_hint: Optional[int] = None,
        subpoint_hint: Optional[str] = None,
        graph: int = 1,
        conscript_draft_id: Optional[uuid.UUID] = None,
        examination_id: Optional[uuid.UUID] = None,
        save_to_db: bool = False
    ) -> CheckDoctorConclusionResponse:
        """
        Полная валидация заключения врача

        Args:
            db: Сессия базы данных
            diagnosis_text: Текст диагноза
            doctor_category: Категория, поставленная врачом
            specialty: Специальность врача
            anamnesis: Анамнез
            complaints: Жалобы
            objective_data: Объективные данные
            special_research_results: Результаты исследований
            conclusion_text: Полный текст заключения
            doctor_notes: Примечания врача
            icd10_codes: Коды МКБ-10
            article_hint: Статья, указанная врачом
            subpoint_hint: Подпункт, указанный врачом
            graph: График призывника (1-4)
            conscript_draft_id: ID призывника (опционально, для сохранения в БД)
            examination_id: ID осмотра (опционально)
            save_to_db: Сохранять ли результаты в БД (по умолчанию False)

        Returns:
            CheckDoctorConclusionResponse с полными результатами валидации
        """
        total_start_time = datetime.now()
        review_reasons = []
        recommendations = []

        # ====================================================================
        # ЭТАП 0: Проверка противоречий
        # ====================================================================
        stage_0_start = datetime.now()
        contradictions = await contradiction_checker.check_for_contradictions(
            db=db,
            diagnosis_text=diagnosis_text,
            doctor_category=doctor_category,
            anamnesis=anamnesis,
            complaints=complaints,
            objective_data=objective_data,
            special_research_results=special_research_results,
            doctor_notes=doctor_notes,
            icd10_codes=icd10_codes,
            graph=graph
        )
        stage_0_duration = (datetime.now() - stage_0_start).total_seconds()

        # Конвертируем противоречия в Pydantic модели
        stage_0_contradictions = self._convert_contradictions(contradictions)

        # Добавляем причины для проверки
        for contradiction in contradictions:
            if contradiction.has_contradiction:
                review_reasons.append(contradiction.description)
                if contradiction.recommendation:
                    recommendations.append(contradiction.recommendation)

        # ====================================================================
        # ЭТАП 1: Клиническая валидация (AI + RAG)
        # ====================================================================
        stage_1_start = datetime.now()

        # Используем полный текст заключения или диагноз
        analysis_text = conclusion_text if conclusion_text else diagnosis_text

        clinical_result = await ai_analyzer.determine_subpoint(
            db=db,
            doctor_conclusion=analysis_text,
            specialty=specialty,
            icd10_codes=icd10_codes,
            article_hint=article_hint,
            anamnesis=anamnesis,
            complaints=complaints,
            special_research_results=special_research_results
        )
        stage_1_duration = (datetime.now() - stage_1_start).total_seconds()

        # Формируем результат этапа 1
        is_healthy = clinical_result.get("is_healthy", False)
        ai_article = clinical_result.get("article")
        ai_subpoint = clinical_result.get("subpoint")
        ai_confidence = clinical_result.get("confidence", 0.0)
        ai_reasoning = clinical_result.get("reasoning", "")

        stage_1_passed = ai_confidence >= 0.5 or is_healthy
        stage_1_status = "SUCCESS" if stage_1_passed else "WARNING"

        if not stage_1_passed and not is_healthy:
            review_reasons.append(
                f"Низкая уверенность AI в определении подпункта ({ai_confidence:.0%})"
            )

        stage_1_clinical = ValidationStageResult(
            stage_name="Клиническая валидация (AI + Приложение 2)",
            stage_number=1,
            passed=stage_1_passed,
            status=stage_1_status,
            details={
                "article": ai_article,
                "subpoint": ai_subpoint,
                "confidence": ai_confidence,
                "is_healthy": is_healthy,
                "reasoning": ai_reasoning[:500] if ai_reasoning else None,
                "matched_criteria": clinical_result.get("matched_criteria"),
                "validation_performed": clinical_result.get("metadata", {}).get("validation_performed", False)
            },
            duration_seconds=stage_1_duration
        )

        # ====================================================================
        # ЭТАП 2: Административная проверка (SQL + Приложение 1)
        # ====================================================================
        stage_2_start = datetime.now()

        ai_category = None
        category_result = {}

        if is_healthy:
            # Здоровый призывник - категория А
            ai_category = "А"
            category_result = {
                "category": "А",
                "graph": graph,
                "confidence": 1.0,
                "reasoning": "Призывник здоров - категория А (годен к военной службе)",
                "source": "HEALTHY_RULE"
            }
            stage_2_passed = True
            stage_2_status = "SUCCESS"

        elif ai_article:
            # Получаем категорию из справочника
            # Подпункт может быть None для некоторых статей (например, статья 88 - Энурез)
            logger.info(
                f"🔍 full_validation: вызов determine_category для article={ai_article}, "
                f"subpoint={ai_subpoint}"
            )
            category_result = await ai_analyzer.determine_category(
                db=db,
                article=ai_article,
                subpoint=ai_subpoint,  # может быть None
                graph=graph
            )
            ai_category = category_result.get("category")
            logger.info(
                f"🔍 full_validation: результат determine_category: category={ai_category}"
            )
            stage_2_passed = ai_category is not None
            stage_2_status = "SUCCESS" if stage_2_passed else "ERROR"

            if not stage_2_passed:
                review_reasons.append(
                    f"Не удалось определить категорию для статьи {ai_article}, подпункт {ai_subpoint}"
                )

        else:
            # Не удалось определить статью
            stage_2_passed = False
            stage_2_status = "SKIPPED"
            category_result = {
                "category": None,
                "reasoning": "Этап пропущен: не определена статья"
            }

        stage_2_duration = (datetime.now() - stage_2_start).total_seconds()

        stage_2_administrative = ValidationStageResult(
            stage_name="Административная проверка (SQL + Приложение 1)",
            stage_number=2,
            passed=stage_2_passed,
            status=stage_2_status,
            details={
                "expected_category": ai_category,
                "doctor_category": doctor_category,
                "graph": graph,
                "source": category_result.get("source"),
                "all_categories": category_result.get("all_categories"),
                "reasoning": category_result.get("reasoning")
            },
            duration_seconds=stage_2_duration
        )

        # ====================================================================
        # Формирование итогового результата
        # ====================================================================
        total_duration = (datetime.now() - total_start_time).total_seconds()

        # Определяем статус совпадения категорий
        category_match_status = self._determine_category_match_status(
            doctor_category=doctor_category,
            ai_category=ai_category,
            is_healthy=is_healthy,
            ai_article=ai_article,
            ai_subpoint=ai_subpoint,
            diagnosis_text=diagnosis_text
        )

        if category_match_status == MatchStatusEnum.MISMATCH:
            review_reasons.append(
                f"Категория врача ({doctor_category}) не совпадает "
                f"с рекомендованной ({ai_category})"
            )
            recommendations.append(
                f"Проверить соответствие категории Приказу 722"
                + (f", статья {ai_article}" if ai_article else "")
            )
        elif category_match_status == MatchStatusEnum.PARTIAL_MISMATCH:
            review_reasons.append(
                f"Возможное несоответствие категории: врач указал ({doctor_category}), "
                f"система рекомендует ({ai_category}). Это пограничный случай, "
                f"требующий дополнительного анализа"
            )
            recommendations.append(
                f"Проверить дополнительные условия для статьи {ai_article}, подпункт {ai_subpoint}. "
                f"Данный подпункт имеет несколько сценариев с разными категориями"
            )

        # Определяем общий статус и уровень риска
        overall_status, risk_level = self._calculate_overall_status(
            contradictions=contradictions,
            category_match_status=category_match_status,
            ai_confidence=ai_confidence,
            is_healthy=is_healthy
        )

        logger.info(
            f"[RISK-CALC] {specialty}: category_match={category_match_status.value}, "
            f"ai_category={ai_category}, doctor_category={doctor_category}, "
            f"contradictions={len([c for c in contradictions if c.has_contradiction])}, "
            f"→ risk_level={risk_level.value}"
        )

        # Определяем, нужна ли ручная проверка
        should_review = (
            overall_status != OverallStatusEnum.VALID or
            len(review_reasons) > 0 or
            risk_level in [SeverityEnum.HIGH, SeverityEnum.CRITICAL]
        )

        # Формируем метаданные
        metadata = {
            "model": clinical_result.get("metadata", {}).get("model", "gpt-4o-mini"),
            "total_duration_seconds": total_duration,
            "stage_0_duration_seconds": stage_0_duration,
            "stage_1_duration_seconds": stage_1_duration,
            "stage_2_duration_seconds": stage_2_duration,
            "tokens_used": clinical_result.get("metadata", {}).get("tokens", {}).get("total", 0),
            "graph": graph,
            "specialty": specialty
        }

        # ====================================================================
        # Сохранение результатов в БД (если запрошено)
        # ====================================================================
        if save_to_db and conscript_draft_id:
            try:
                # Проверяем существование призывника в БД
                # ВАЖНО: conscript_draft_id может быть ID призывника (conscript.id) или ID draft
                # Сначала ищем по draft.id, если не найдено - ищем по conscript_id
                from app.models.conscript import Conscript
                stmt = select(Conscript).where(Conscript.id == conscript_draft_id)
                result_check = await db.execute(stmt)
                draft = result_check.scalar_one_or_none()

                # Если не найдено по draft.id, попробуем по conscript_id
                if draft is None:
                    stmt = select(Conscript).where(Conscript.conscript_id == conscript_draft_id)
                    result_check = await db.execute(stmt)
                    draft = result_check.scalar_one_or_none()

                if draft is None:
                    logger.warning(
                        f"⚠️ Conscript для conscript_draft_id={conscript_draft_id} не найден в БД. "
                        f"Пропускаем сохранение результатов (вероятно, это моковые данные из UI)"
                    )
                else:
                    # Используем реальный draft.id для сохранения
                    actual_draft_id = draft.id
                    await self._save_analysis_result(
                        db=db,
                        conscript_draft_id=actual_draft_id,  # Используем реальный ID draft
                        examination_id=examination_id,
                        specialty=specialty,
                        doctor_category=doctor_category,
                        ai_recommended_category=ai_category,
                        status=overall_status.value,
                        risk_level=risk_level.value,
                        article=ai_article,
                        subpoint=ai_subpoint,
                        reasoning=ai_reasoning,
                        confidence=ai_confidence,
                        model_used=metadata["model"],
                        tokens_used=metadata["tokens_used"],
                        analysis_duration_seconds=total_duration
                    )
                    logger.info(
                        f"✅ Результаты анализа сохранены в БД для draft_id={actual_draft_id} (conscript_id={draft.conscript_id}), "
                        f"specialty={specialty}"
                    )
            except Exception as e:
                logger.error(f"❌ Ошибка сохранения результатов в БД: {e}", exc_info=True)
                # Продолжаем выполнение, не прерывая анализ

        return CheckDoctorConclusionResponse(
            overall_status=overall_status,
            risk_level=risk_level,
            stage_0_contradictions=stage_0_contradictions,
            stage_1_clinical=stage_1_clinical,
            stage_2_administrative=stage_2_administrative,
            ai_recommended_article=ai_article,
            ai_recommended_subpoint=ai_subpoint,
            ai_recommended_category=ai_category,
            ai_confidence=ai_confidence,
            ai_reasoning=ai_reasoning,
            doctor_article=article_hint,
            doctor_subpoint=subpoint_hint,
            doctor_category=doctor_category,
            category_match_status=category_match_status,
            should_review=should_review,
            review_reasons=review_reasons,
            recommendations=recommendations,
            is_healthy=is_healthy,
            metadata=metadata
        )

    async def _save_analysis_result(
        self,
        db: AsyncSession,
        conscript_draft_id: uuid.UUID,
        specialty: str,
        doctor_category: str,
        ai_recommended_category: Optional[str],
        status: str,
        risk_level: str,
        article: Optional[int],
        subpoint: Optional[str],
        reasoning: str,
        confidence: Optional[float],
        model_used: str,
        tokens_used: int,
        analysis_duration_seconds: float,
        examination_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Сохраняет результаты AI анализа в БД с заменой старых данных

        Логика: если для данной комбинации (conscript_draft_id + specialty)
        уже есть запись, она удаляется и создается новая.
        """
        # Удаляем старые результаты для этой комбинации
        delete_stmt = delete(AIAnalysisResult).where(
            AIAnalysisResult.conscript_draft_id == conscript_draft_id,
            AIAnalysisResult.specialty == specialty
        )
        await db.execute(delete_stmt)

        logger.info(
            f"🗑️ Удалены старые результаты для conscript_draft_id={conscript_draft_id}, "
            f"specialty={specialty}"
        )

        # Создаем новую запись
        analysis_result = AIAnalysisResult(
            id=uuid.uuid4(),
            conscript_draft_id=conscript_draft_id,
            examination_id=examination_id,
            specialty=specialty,
            doctor_category=doctor_category,
            ai_recommended_category=ai_recommended_category or "UNKNOWN",
            status=status,
            risk_level=risk_level,
            article=article,
            subpoint=subpoint,
            reasoning=reasoning[:5000] if reasoning else "",  # Ограничение по длине
            confidence=confidence,
            model_used=model_used,
            tokens_used=tokens_used,
            analysis_duration_seconds=analysis_duration_seconds,
            created_at=datetime.now()
        )

        db.add(analysis_result)
        await db.commit()
        await db.refresh(analysis_result)

        logger.info(
            f"💾 Создана новая запись результата анализа: id={analysis_result.id}, "
            f"article={article}, category={ai_recommended_category}"
        )

    def _convert_contradictions(
        self,
        contradictions: List[ContradictionResult]
    ) -> List[ContradictionDetail]:
        """Конвертация внутренних результатов в Pydantic модели"""
        result = []

        for c in contradictions:
            if not c.has_contradiction:
                continue

            # Конвертируем RAG matches
            rag_matches = []
            for match in c.rag_matches:
                rag_matches.append(RAGMatch(
                    article=match.get("article", 0),
                    subpoint=str(match.get("subpoint", "")),
                    description=match.get("description", "")[:500],
                    similarity=match.get("similarity", 0.0),
                    categories=match.get("categories", {})
                ))

            result.append(ContradictionDetail(
                type=ContradictionTypeEnum(c.contradiction_type.value),
                severity=SeverityEnum(c.severity.value),
                description=c.description,
                source_field=c.source_field,
                target_field=c.target_field,
                source_value=c.source_value,
                target_value=c.target_value,
                rag_matches=rag_matches,
                recommendation=c.recommendation
            ))

        return result

    def _determine_category_match_status(
        self,
        doctor_category: str,
        ai_category: Optional[str],
        is_healthy: bool,
        ai_article: Optional[int] = None,
        ai_subpoint: Optional[str] = None,
        diagnosis_text: str = ""
    ) -> MatchStatusEnum:
        """Определение статуса совпадения категорий"""

        # СПЕЦИАЛЬНЫЙ СЛУЧАЙ: ai_category=None, но doctor_category="А" и нет статьи/подпункта
        # Это случай здорового призывника или функционального расстройства (ВСД)
        # которое не препятствует службе
        if ai_category is None:
            doctor_normalized = doctor_category.upper().strip()
            # Если врач поставил А и нет статьи/подпункта - это MATCH (здоров или ВСД без ограничений)
            if doctor_normalized in ["А", "A"] and ai_article is None and ai_subpoint is None:
                return MatchStatusEnum.MATCH
            # В остальных случаях требуется проверка
            return MatchStatusEnum.REVIEW_REQUIRED

        doctor_normalized = doctor_category.upper().strip()
        ai_normalized = ai_category.upper().strip()

        # Для здоровых: категория должна быть А
        if is_healthy:
            if doctor_normalized in ["А", "A"]:
                return MatchStatusEnum.MATCH
            else:
                return MatchStatusEnum.MISMATCH

        # Для больных: сравниваем категории
        if doctor_normalized == ai_normalized:
            return MatchStatusEnum.MATCH

        # Проверяем пограничные случаи (сложные подпункты с внутренними условиями)
        if self._is_borderline_case(ai_article, ai_subpoint, diagnosis_text):
            return MatchStatusEnum.PARTIAL_MISMATCH

        return MatchStatusEnum.MISMATCH

    def _is_borderline_case(
        self,
        article: Optional[int],
        subpoint: Optional[str],
        diagnosis_text: str
    ) -> bool:
        """
        Проверка пограничных случаев, где один подпункт содержит несколько сценариев
        с разными категориями годности
        """
        diagnosis_lower = diagnosis_text.lower()

        # Статья 2, подпункт 3: Туберкулез после лечения / Большие остаточные изменения
        # Имеет разные сценарии:
        # - После стационарного лечения (3+ месяца) - временно Д
        # - Большие остаточные изменения без дыхательной недостаточности - Б
        # - Клинически излеченный после основного курса - может быть Б или Д
        if article == 2 and subpoint == "3":
            keywords = ["туберкулез", "туберкулёз", "остаточн", "посттуберкулезн",
                       "излечен", "вылечен", "после лечения"]
            if any(kw in diagnosis_lower for kw in keywords):
                return True

        # Статья 2, подпункт 4: Малые остаточные изменения
        # Может быть Б, В или Г в зависимости от графа и конкретной ситуации
        if article == 2 and subpoint == "4":
            keywords = ["мал", "остаточн", "единичн", "очаг", "петрификат"]
            if any(kw in diagnosis_lower for kw in keywords):
                return True

        # Статья 1, подпункт 2: После острых заболеваний
        # Категория зависит от срока после лечения и наличия осложнений
        if article == 1 and subpoint == "2":
            keywords = ["после", "перенес", "гепатит", "тиф"]
            if any(kw in diagnosis_lower for kw in keywords):
                return True

        return False

    def _calculate_overall_status(
        self,
        contradictions: List[ContradictionResult],
        category_match_status: MatchStatusEnum,
        ai_confidence: float,
        is_healthy: bool
    ) -> tuple[OverallStatusEnum, SeverityEnum]:
        """Расчет общего статуса и уровня риска"""

        # ВАЖНО: Если категории совпадают (MATCH) и нет противоречий, то всегда LOW риск
        # Это предотвращает ложные HIGH риски для здоровых призывников
        has_any_contradiction = any(c.has_contradiction for c in contradictions)
        if category_match_status == MatchStatusEnum.MATCH and not has_any_contradiction:
            return OverallStatusEnum.VALID, SeverityEnum.LOW

        # Проверяем критические противоречия
        has_critical = any(
            c.has_contradiction and c.severity.value == "CRITICAL"
            for c in contradictions
        )
        has_high = any(
            c.has_contradiction and c.severity.value == "HIGH"
            for c in contradictions
        )

        # Критические случаи
        if has_critical:
            return OverallStatusEnum.INVALID, SeverityEnum.CRITICAL

        # Несовпадение категорий
        if category_match_status == MatchStatusEnum.MISMATCH:
            if has_high:
                return OverallStatusEnum.INVALID, SeverityEnum.HIGH
            else:
                return OverallStatusEnum.WARNING, SeverityEnum.HIGH

        # Возможное несоответствие (пограничный случай)
        if category_match_status == MatchStatusEnum.PARTIAL_MISMATCH:
            return OverallStatusEnum.WARNING, SeverityEnum.MEDIUM

        # Есть противоречия
        if has_any_contradiction:
            if has_high:
                return OverallStatusEnum.WARNING, SeverityEnum.HIGH
            else:
                return OverallStatusEnum.WARNING, SeverityEnum.MEDIUM

        # Низкая уверенность AI
        if ai_confidence < 0.5 and not is_healthy:
            return OverallStatusEnum.WARNING, SeverityEnum.MEDIUM

        # Требуется проверка
        if category_match_status == MatchStatusEnum.REVIEW_REQUIRED:
            return OverallStatusEnum.WARNING, SeverityEnum.MEDIUM

        # Всё хорошо
        if ai_confidence >= 0.7 or is_healthy:
            return OverallStatusEnum.VALID, SeverityEnum.LOW
        else:
            return OverallStatusEnum.VALID, SeverityEnum.MEDIUM


# Глобальный экземпляр сервиса
full_validation_service = FullValidationService()
