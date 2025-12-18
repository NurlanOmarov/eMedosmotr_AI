#!/usr/bin/env python3
"""
Обновление заключений врачей с разными категориями годности
Использует примеры из doctor_conclusions_examples.json
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.utils.database import SessionLocal
from app.models.conscript import Conscript, ConscriptDraft
from app.models.medical import SpecialistExamination


# Маппинг специальностей из примеров в специальности БД
SPECIALTY_MAPPING = {
    "Терапевт": "Терапевт",
    "Хирург": "Хирург",
    "Офтальмолог": "Офтальмолог",
    "Невролог": "Невролог",
    "Кардиолог": "Терапевт",  # Кардиолог -> Терапевт (так как нет отдельного кардиолога)
}


async def load_examples():
    """Загружаем примеры из JSON файла"""
    examples_file = Path(__file__).parent.parent / "test_data" / "doctor_conclusions_examples.json"
    with open(examples_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['test_cases']


async def update_examinations():
    """Обновляем заключения врачей"""
    print("=" * 70)
    print("🔄 ОБНОВЛЕНИЕ ЗАКЛЮЧЕНИЙ С РАЗНЫМИ КАТЕГОРИЯМИ")
    print("=" * 70)

    async with SessionLocal() as db:
        try:
            # Загружаем примеры
            examples = await load_examples()
            print(f"\n📚 Загружено примеров: {len(examples)}")

            # Получаем всех призывников
            conscripts_query = select(Conscript).order_by(Conscript.last_name, Conscript.first_name)
            result = await db.execute(conscripts_query)
            conscripts = result.scalars().all()

            print(f"👥 Призывников в БД: {len(conscripts)}")

            # Распределяем примеры по призывникам
            # Используем разные случаи для разных призывников
            case_assignments = [
                1,   # СЛУЧАЙ5 - Здоровый (А)
                2,   # СЛУЧАЙ1 - Миопия слабой степени (А)
                3,   # СЛУЧАЙ2 - Миопия средней степени (Б)
                4,   # СЛУЧАЙ3 - Миопия высокой степени (Д)
                5,   # СЛУЧАЙ4 - Плоскостопие 2 степени (Б)
                1,   # СЛУЧАЙ7 - Здоровый (А)
                8,   # СЛУЧАЙ8 - Грыжа с осложнениями (Д)
                1,   # СЛУЧАЙ9 - Здоровый (А)
                9,   # СЛУЧАЙ10 - Гипертензия (Б)
                10,  # СЛУЧАЙ11 - Сколиоз 2 степени (А)
            ]

            updated_count = 0

            for conscript_idx, conscript in enumerate(conscripts):
                if conscript_idx >= len(case_assignments):
                    break

                case_id = case_assignments[conscript_idx]
                example = next((e for e in examples if e['case_id'] == case_id), None)

                if not example:
                    continue

                # Получаем draft для призывника
                draft_query = select(ConscriptDraft).where(
                    ConscriptDraft.conscript_id == conscript.id
                )
                draft_result = await db.execute(draft_query)
                draft = draft_result.scalar_one_or_none()

                if not draft:
                    continue

                print(f"\n👤 {conscript.full_name} → Случай {case_id} ({example['name']})")

                # Получаем осмотры призывника
                exams_query = select(SpecialistExamination).where(
                    SpecialistExamination.conscript_draft_id == draft.id
                )
                exams_result = await db.execute(exams_query)
                examinations = exams_result.scalars().all()

                # Находим нужную специальность
                target_specialty = SPECIALTY_MAPPING.get(example['specialty'])
                if not target_specialty:
                    continue

                # Обновляем осмотр нужной специальности
                for exam in examinations:
                    if exam.specialty_ru == target_specialty:
                        # Обновляем данные из примера
                        exam.complaints = f"Жалоб нет" if case_id == 1 else example.get('anamnesis', '').split('.')[0] + '.'
                        exam.anamnesis = example['anamnesis'][:500] if len(example['anamnesis']) > 500 else example['anamnesis']
                        exam.objective_data = example['conclusion'][:1000] if len(example['conclusion']) > 1000 else example['conclusion']
                        exam.diagnosis_text = example['diagnosis_text']
                        exam.conclusion_text = example['conclusion'][:500] if len(example['conclusion']) > 500 else example['conclusion']
                        exam.icd10_code = example['icd10_codes'][0] if example['icd10_codes'] else 'Z00.0'
                        exam.doctor_category = example['doctor_category']

                        print(f"   ✅ {exam.specialty_ru}: {exam.icd10_code} → Категория {exam.doctor_category}")
                        updated_count += 1
                        break

            # Сохраняем изменения
            await db.commit()

            print(f"\n✅ Успешно обновлено: {updated_count} осмотров")
            print("=" * 70)

            # Статистика по категориям
            stats_query = select(SpecialistExamination)
            stats_result = await db.execute(stats_query)
            all_exams = stats_result.scalars().all()

            categories = {}
            for exam in all_exams:
                cat = exam.doctor_category or 'Не указано'
                categories[cat] = categories.get(cat, 0) + 1

            print("\n📊 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
            for cat, count in sorted(categories.items()):
                print(f"   {cat}: {count} осмотров")

        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_examinations())
