"""
Создание записей ConscriptDraft для всех призывников, у которых их нет
Исправляет проблему с сохранением результатов AI анализа
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.database import SessionLocal
from app.models.conscript import Conscript, ConscriptDraft
from datetime import datetime


async def create_missing_drafts():
    """
    Создает записи ConscriptDraft для всех призывников, у которых их нет
    """
    async with SessionLocal() as session:
        # Получаем всех призывников
        result = await session.execute(select(Conscript))
        conscripts = result.scalars().all()

        print(f"📊 Найдено призывников: {len(conscripts)}")

        created_count = 0
        skipped_count = 0

        for conscript in conscripts:
            # Проверяем, есть ли у призывника draft
            draft_result = await session.execute(
                select(ConscriptDraft).where(
                    ConscriptDraft.conscript_id == conscript.id
                )
            )
            existing_draft = draft_result.scalar_one_or_none()

            if existing_draft:
                print(f"✓ {conscript.full_name}: draft уже существует")
                skipped_count += 1
                continue

            # Создаем новый draft
            new_draft = ConscriptDraft(
                conscript_id=conscript.id,
                category_graph_id=conscript.graph or 1,  # График по умолчанию
                draft_name=f"Призыв {datetime.now().year}",
                draft_season="Весна" if datetime.now().month <= 6 else "Осень",
                draft_year=datetime.now().year,
                status="in_progress",
                created_at=datetime.now()
            )

            session.add(new_draft)
            created_count += 1
            print(f"✅ {conscript.full_name}: создан draft (ID: {new_draft.id})")

        # Сохраняем изменения
        await session.commit()

        print(f"\n{'='*60}")
        print(f"✅ Готово!")
        print(f"   Создано drafts: {created_count}")
        print(f"   Пропущено (уже существует): {skipped_count}")
        print(f"   Всего призывников: {len(conscripts)}")
        print(f"{'='*60}")


if __name__ == "__main__":
    print("🔧 Создание записей ConscriptDraft для призывников без draft...")
    print("="*60)
    asyncio.run(create_missing_drafts())
