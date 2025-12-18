"""
Тест корректировки логики AI для ВСД (Случай ТЕСТОВЫЙ СЛУЧАЙ14)
"""

import asyncio
import sys
import os

# Добавляем путь к backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.utils.database import get_db
from app.models.conscript import Conscript, ConscriptDraft
from app.models.medical import SpecialistExamination
from app.services.ai_analyzer import ai_analyzer


async def test_vsd_case():
    """
    Тестирование случая ВСД - ПРИЗЫВНИК ТЕСТОВЫЙ СЛУЧАЙ14
    """

    print("=" * 80)
    print("ТЕСТ: Корректировка логики AI для ВСД")
    print("=" * 80)

    async for db in get_db():
        try:
            # Находим призывника
            result = await db.execute(
                select(Conscript, ConscriptDraft)
                .join(ConscriptDraft, Conscript.id == ConscriptDraft.conscript_id)
                .where(Conscript.full_name.ilike('%ПРИЗЫВНИК ТЕСТОВЫЙ СЛУЧАЙ14%'))
            )

            conscript, draft = result.first()

            if not conscript:
                print("❌ Призывник не найден!")
                return

            print(f"\n✅ Призывник найден:")
            print(f"   ФИО: {conscript.full_name}")
            print(f"   ИИН: {conscript.iin}")
            print(f"   Draft ID: {draft.id}")
            print(f"   График: {draft.category_graph.graph}")

            # Находим заключение невролога
            exam_result = await db.execute(
                select(SpecialistExamination)
                .where(
                    SpecialistExamination.conscript_draft_id == draft.id,
                    SpecialistExamination.specialty == 'Невролог'
                )
            )

            examination = exam_result.scalar_one_or_none()

            if not examination:
                print("❌ Заключение невролога не найдено!")
                return

            print(f"\n📋 Заключение невролога:")
            print(f"   Диагноз: {examination.icd10_code} - {examination.diagnosis_text[:100]}...")
            print(f"   Категория врача: {examination.doctor_category}")
            print(f"   Анамнез: {examination.anamnesis[:100]}...")

            # Запускаем AI анализ
            print("\n🤖 Запуск AI анализа...")

            analysis = await ai_analyzer.analyze_examination(
                db=db,
                doctor_conclusion=examination.conclusion_text,
                specialty=examination.specialty,
                doctor_category=examination.doctor_category,
                icd10_codes=[examination.icd10_code] if examination.icd10_code else None,
                graph=draft.category_graph.graph,
                conscript_draft_id=str(draft.id),
                examination_id=str(examination.id),
                anamnesis=examination.anamnesis,
                complaints=None,
                special_research_results=None
            )

            # Выводим результаты
            print("\n" + "=" * 80)
            print("РЕЗУЛЬТАТЫ AI АНАЛИЗА")
            print("=" * 80)

            print(f"\n📊 Определение подпункта:")
            print(f"   Статья: {analysis.get('article')}")
            print(f"   Подпункт: {analysis.get('subpoint')}")
            print(f"   Уверенность: {analysis.get('confidence'):.2f}")

            print(f"\n🎯 Категория:")
            print(f"   AI рекомендует: {analysis.get('ai_recommended_category')}")
            print(f"   Врач поставил: {analysis.get('doctor_category')}")
            print(f"   Статус: {analysis.get('status')}")
            print(f"   Уровень риска: {analysis.get('risk_level')}")

            print(f"\n💬 Обоснование AI:")
            reasoning = analysis.get('reasoning', '')
            # Разбиваем на части по разделителю " | "
            parts = reasoning.split(' | ')
            for i, part in enumerate(parts, 1):
                print(f"   {i}. {part[:200]}")
                if len(part) > 200:
                    print(f"      ...({len(part) - 200} символов)")

            # Проверяем корректность
            print("\n" + "=" * 80)
            print("ПРОВЕРКА КОРРЕКТНОСТИ")
            print("=" * 80)

            expected_article = None
            expected_subpoint = None
            expected_category = "А"

            is_correct = (
                analysis.get('article') == expected_article and
                analysis.get('subpoint') == expected_subpoint and
                analysis.get('ai_recommended_category') == expected_category
            )

            if is_correct:
                print("\n✅ УСПЕХ! AI правильно определила:")
                print(f"   - Статья: {expected_article} (ВСД не относится к статье 24)")
                print(f"   - Подпункт: {expected_subpoint}")
                print(f"   - Категория: {expected_category} (годен к военной службе)")
                print(f"   - Совпадение с врачом: {'ДА' if analysis.get('status') == 'MATCH' else 'НЕТ'}")
            else:
                print("\n❌ ОШИБКА! AI всё ещё ошибается:")
                print(f"   Ожидалось: статья={expected_article}, подпункт={expected_subpoint}, категория={expected_category}")
                print(f"   Получено: статья={analysis.get('article')}, подпункт={analysis.get('subpoint')}, категория={analysis.get('ai_recommended_category')}")

            # Дополнительные детали
            subpoint_details = analysis.get('subpoint_details', {})
            if subpoint_details:
                print(f"\n📝 Дополнительные детали:")
                print(f"   Здоров: {subpoint_details.get('is_healthy', 'N/A')}")
                if 'data_insufficiency' in subpoint_details:
                    print(f"   Недостаточность данных: {subpoint_details.get('data_insufficiency')}")
                if 'missing_parameters' in subpoint_details:
                    print(f"   Недостающие параметры: {subpoint_details.get('missing_parameters')}")

            print("\n" + "=" * 80)

        except Exception as e:
            print(f"\n❌ Ошибка при тестировании: {e}")
            import traceback
            traceback.print_exc()

        finally:
            break  # Выходим из цикла async for


if __name__ == "__main__":
    asyncio.run(test_vsd_case())
