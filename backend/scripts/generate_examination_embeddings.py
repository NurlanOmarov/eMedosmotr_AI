#!/usr/bin/env python3
"""
Генерация embeddings для specialists_examinations
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from app.utils.database import SessionLocal
from app.services.openai_client import openai_service
from app.models.medical import SpecialistExamination


async def generate_examination_embeddings():
    """Генерация embeddings для осмотров специалистов"""

    print("="*80)
    print("🧮 ГЕНЕРАЦИЯ EMBEDDINGS ДЛЯ ОСМОТРОВ СПЕЦИАЛИСТОВ")
    print("="*80)

    async with SessionLocal() as session:
        # Подсчет
        print("\n1. Подсчет осмотров...")
        result = await session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(conclusion_embedding) as with_emb,
                COUNT(*) - COUNT(conclusion_embedding) as without_emb
            FROM specialists_examinations
        """))
        row = result.fetchone()
        total, with_emb, without_emb = row[0], row[1], row[2]

        print(f"   Всего осмотров: {total}")
        print(f"   С embeddings: {with_emb}")
        print(f"   Без embeddings: {without_emb}")

        if without_emb == 0:
            print("\n✅ Все осмотры уже имеют embeddings!")
            return

        # Получаем осмотры без embeddings через ORM
        print(f"\n2. Получение данных для {without_emb} осмотров...")
        result = await session.execute(
            select(SpecialistExamination)
            .where(SpecialistExamination.conclusion_embedding.is_(None))
            .order_by(SpecialistExamination.id)
        )

        examinations = result.scalars().all()
        print(f"   ✓ Загружено {len(examinations)} записей")

        # Генерация
        print(f"\n3. Генерация embeddings (займет ~{len(examinations) * 0.5:.0f} секунд)...")

        success = 0
        errors = 0

        for idx, exam in enumerate(examinations, 1):
            try:
                # Подготовка текста
                text_content = exam.conclusion_text or exam.diagnosis_text or "Здоров"
                text_for_embedding = text_content[:8000]

                # Генерируем embedding
                embedding = await openai_service.create_embedding(text_for_embedding)

                # Обновляем через ORM
                exam.conclusion_embedding = embedding
                success += 1

                # Коммитим каждые 10 записей
                if idx % 10 == 0:
                    await session.commit()
                    print(f"   ... {idx}/{len(examinations)} ({idx*100//len(examinations)}%)")

            except Exception as e:
                print(f"   ✗ Ошибка для осмотра {exam.id}: {e}")
                errors += 1

        # Финальный коммит
        await session.commit()

        print(f"\n   ✅ Успешно: {success}")
        if errors > 0:
            print(f"   ⚠️  Ошибок: {errors}")

        # Финальная проверка
        print("\n4. Финальная проверка...")
        result = await session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(conclusion_embedding) as with_emb
            FROM specialists_examinations
        """))
        row = result.fetchone()
        final_total, final_with_emb = row[0], row[1]

        print(f"   Осмотров с embeddings: {final_with_emb}/{final_total}")

        if final_with_emb == final_total:
            print("   ✅ ВСЕ осмотры имеют embeddings!")
        else:
            print(f"   ⚠️  Осталось {final_total - final_with_emb} без embeddings")

    print("\n" + "="*80)
    print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
    print("="*80)


async def main():
    try:
        await generate_examination_embeddings()
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
