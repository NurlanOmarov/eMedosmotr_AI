"""
Тест функции подготовки данных для внешнего AI API
"""

import asyncio
import json
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.database import get_db
from app.services.external_ai_mapper import (
    prepare_external_ai_request,
    validate_api_request,
    serialize_for_json
)
from app.models.conscript import ConscriptDraft


async def test_mapper():
    """Тест маппера данных для внешнего API"""

    print("🧪 ТЕСТ: Подготовка данных для внешнего AI API")
    print("=" * 60)

    async for db in get_db():
        try:
            # 1. Получить первый доступный draft
            result = await db.execute(
                select(ConscriptDraft).limit(1)
            )
            draft = result.scalar_one_or_none()

            if not draft:
                print("❌ Нет данных в таблице conscript_drafts")
                print("\n💡 Сначала загрузите тестовые данные:")
                print("   docker exec emedosmotr_backend python scripts/load_test_data.py")
                return

            draft_id = draft.id
            print(f"✅ Найден draft: {draft_id}")
            print(f"   Призыв: {draft.draft_name}")
            print()

            # 2. Подготовить данные для API
            print("📦 Подготовка данных...")
            api_data = await prepare_external_ai_request(
                conscript_draft_id=draft_id,
                db=db
            )

            # 3. Валидация
            print("✔️  Валидация данных...")
            validate_api_request(api_data)
            print("✅ Данные валидны!")
            print()

            # 4. Сериализация
            print("🔄 Сериализация для JSON...")
            json_data = serialize_for_json(api_data)

            # 5. Вывод результата
            print("=" * 60)
            print("📊 РЕЗУЛЬТАТ:")
            print("=" * 60)
            print()

            # Краткая информация
            print(f"Призывник ID: {json_data['conscript_draft']['conscript_id']}")
            print(f"Призыв: {json_data['conscript_draft']['draft']}")
            print()

            # Антропометрия
            anthro = json_data['anthropometic_data']
            print("📏 Антропометрия:")
            print(f"   Рост: {anthro['height']} см")
            print(f"   Вес: {anthro['weight']} кг")
            print(f"   ИМТ: {anthro['bmi']}")
            print()

            # Специалисты
            exams = json_data['specialists_examinations']
            print(f"👨‍⚕️ Заключения специалистов: {len(exams)}")
            for i, exam in enumerate(exams, 1):
                print(f"\n   {i}. {exam['med_commission_member']}")
                print(f"      Категория: {exam['valid_category']}")
                print(f"      Диагноз: {exam['diagnosis_accompany_id']}")

                # Данные офтальмолога
                if exam['os_vision_without_correction']:
                    print(f"      Зрение: OD={exam['od_vision_without_correction']}, OS={exam['os_vision_without_correction']}")

                # Данные стоматолога
                if exam['dentist_json']:
                    print(f"      Зубная формула: {len(exam['dentist_json'])} зубов")

            print()
            print("=" * 60)
            print("📄 Полный JSON (первые 1000 символов):")
            print("=" * 60)
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
            print(json_str[:1000])
            if len(json_str) > 1000:
                print(f"\n... (всего {len(json_str)} символов)")

            print()
            print("=" * 60)
            print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
            print("=" * 60)
            print()
            print("💡 Данные готовы к отправке на внешний AI сервер:")
            print("   response = await httpx.post(external_ai_url, json=json_data)")

        except Exception as e:
            print(f"\n❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

        break  # Выйти из генератора get_db


if __name__ == "__main__":
    asyncio.run(test_mapper())
