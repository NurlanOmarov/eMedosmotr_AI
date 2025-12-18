"""
Демонстрация связи: врачи → призывная кампания → призывник
"""

import asyncio
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.utils.database import get_db
from app.services.external_ai_mapper import get_conscript_info_by_draft
from app.models.conscript import ConscriptDraft
from app.models.medical import SpecialistExamination


async def demonstrate_connections():
    """Показать как установлена связь между врачами и призывниками"""

    print("🔍 ДЕМОНСТРАЦИЯ СВЯЗЕЙ В БД")
    print("=" * 80)

    async for db in get_db():
        try:
            # 1. Получить первую призывную кампанию
            result = await db.execute(
                select(ConscriptDraft)
                .options(
                    selectinload(ConscriptDraft.conscript),
                    selectinload(ConscriptDraft.specialist_examinations)
                )
                .limit(1)
            )
            draft = result.scalar_one_or_none()

            if not draft:
                print("❌ Нет данных в БД")
                return

            print("\n📋 ПРИЗЫВНАЯ КАМПАНИЯ:")
            print(f"   ID: {draft.id}")
            print(f"   Название: {draft.draft_name}")
            print(f"   Год: {draft.draft_year}")
            print(f"   Статус: {draft.status}")

            print("\n👤 ПРИЗЫВНИК:")
            if draft.conscript:
                print(f"   ID (UUID): {draft.conscript.id}")
                print(f"   ИИН: {draft.conscript.iin}")
                print(f"   ФИО: {draft.conscript.full_name}")
                print(f"   Дата рождения: {draft.conscript.date_of_birth}")
            else:
                print("   ⚠️ Призывник не найден")

            print("\n👨‍⚕️ ЗАКЛЮЧЕНИЯ ВРАЧЕЙ:")
            print(f"   Всего осмотров: {len(draft.specialist_examinations)}")
            print()

            for i, exam in enumerate(draft.specialist_examinations[:5], 1):
                print(f"   {i}. {exam.specialty_ru or exam.specialty}")
                print(f"      Категория: {exam.doctor_category}")
                print(f"      Диагноз: {exam.icd10_code}")
                print(f"      Дата: {exam.examination_date}")

                # Показать как получить призывника из заключения
                print(f"      ↓ Связь через draft:")
                print(f"      Призывник: {draft.conscript.full_name if draft.conscript else 'N/A'}")
                print(f"      ИИН: {draft.conscript.iin if draft.conscript else 'N/A'}")
                print()

            print("=" * 80)
            print("\n🔗 КАК РАБОТАЕТ СВЯЗЬ:")
            print()
            print("   SpecialistExamination.conscript_draft_id")
            print("   ↓")
            print("   ConscriptDraft.id")
            print("   ↓")
            print("   ConscriptDraft.conscript_id")
            print("   ↓")
            print("   Conscript.id")
            print("   ↓")
            print("   Conscript.iin (ИИН призывника)")
            print()

            print("=" * 80)
            print("\n📊 ИСПОЛЬЗОВАНИЕ В КОДЕ:")
            print()
            print("```python")
            print("# Способ 1: Через relationship")
            print("exam = await db.get(SpecialistExamination, exam_id)")
            print("conscript_iin = exam.draft.conscript.iin")
            print()
            print("# Способ 2: Через вспомогательную функцию")
            print("info = await get_conscript_info_by_draft(draft_id, db)")
            print("conscript_iin = info['conscript_iin']")
            print("```")
            print()

            print("=" * 80)
            print("\n🧪 ТЕСТ ВСПОМОГАТЕЛЬНОЙ ФУНКЦИИ:")
            print()

            info = await get_conscript_info_by_draft(draft.id, db)
            print(f"   Draft ID: {info['draft_id']}")
            print(f"   Draft Name: {info['draft_name']}")
            print(f"   Conscript ID: {info['conscript_id']}")
            print(f"   Conscript IIN: {info['conscript_iin']}")
            print(f"   Conscript Name: {info['conscript_name']}")
            print(f"   Examinations: {info['examinations_count']}")
            print()

            print("=" * 80)
            print("✅ СВЯЗЬ РАБОТАЕТ КОРРЕКТНО!")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

        break


if __name__ == "__main__":
    asyncio.run(demonstrate_connections())
