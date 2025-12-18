#!/usr/bin/env python3
"""
Скрипт для загрузки детальных критериев из point_criteria_full_VALIDATED.csv в БД
С генерацией векторных эмбеддингов для RAG-поиска
"""

import sys
import csv
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.utils.database import SessionLocal
from app.services.openai_client import openai_service


async def clear_existing_criteria():
    """Очистка существующих критериев"""
    async with SessionLocal() as db:
        print("\n🗑️  Удаление существующих критериев...")
        result = await db.execute(text("DELETE FROM point_criteria"))
        await db.commit()
        print(f"   Удалено записей: {result.rowcount}")


async def load_detailed_criteria():
    """Загрузка детальных критериев из CSV в БД"""

    csv_path = Path(__file__).parent.parent / "point_criteria_full_VALIDATED.csv"

    if not csv_path.exists():
        print(f"❌ Файл не найден: {csv_path}")
        return

    print("=" * 100)
    print("ЗАГРУЗКА ДЕТАЛЬНЫХ КРИТЕРИЕВ В БД")
    print("=" * 100)
    print(f"Файл: {csv_path}")
    print()

    # Читаем CSV
    criteria_list = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            criteria_list.append({
                'article': int(row['article']),
                'subpoint': row['subpoint'] if row['subpoint'] else '',
                'criteria_text': row['criteria_text'],
                'keywords': row.get('keywords', ''),
                'quantitative_params': row.get('quantitative_params', '{}')
            })

    print(f"📊 Прочитано критериев из CSV: {len(criteria_list)}")

    # Группируем по статьям для статистики
    articles_stats = {}
    for criteria in criteria_list:
        article = criteria['article']
        if article not in articles_stats:
            articles_stats[article] = 0
        articles_stats[article] += 1

    print(f"📋 Уникальных статей: {len(articles_stats)}")
    print(f"📈 Статьи с наибольшим количеством критериев:")
    top_articles = sorted(articles_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    for article, count in top_articles:
        print(f"   Статья {article}: {count} критериев")

    # Загружаем в БД
    async with SessionLocal() as db:
        print("\n💾 Загрузка критериев в БД...")
        loaded_count = 0
        batch_size = 50

        for i in range(0, len(criteria_list), batch_size):
            batch = criteria_list[i:i+batch_size]

            for criteria in batch:
                # Вставляем без эмбеддингов (их сгенерируем отдельно)
                query = text("""
                    INSERT INTO point_criteria
                    (article, subpoint, description, created_at)
                    VALUES (:article, :subpoint, :description, :created_at)
                """)

                await db.execute(query, {
                    'article': criteria['article'],
                    'subpoint': criteria['subpoint'],
                    'description': criteria['criteria_text'],
                    'created_at': datetime.now()
                })
                loaded_count += 1

            await db.commit()
            print(f"   Загружено: {loaded_count}/{len(criteria_list)}", end='\r')

        print(f"\n✅ Загружено критериев: {loaded_count}")

    return loaded_count


async def generate_embeddings():
    """Генерация векторных эмбеддингов для всех критериев"""

    print("\n" + "=" * 100)
    print("ГЕНЕРАЦИЯ ВЕКТОРНЫХ ЭМБЕДДИНГОВ")
    print("=" * 100)

    async with SessionLocal() as db:
        # Получаем все критерии без эмбеддингов
        result = await db.execute(text("""
            SELECT id, article, subpoint, description
            FROM point_criteria
            WHERE criteria_embedding IS NULL
            ORDER BY article, subpoint, id
        """))
        criteria_without_embeddings = result.fetchall()

        total = len(criteria_without_embeddings)
        print(f"📊 Критериев без эмбеддингов: {total}")

        if total == 0:
            print("✅ Все критерии уже имеют эмбеддинги!")
            return

        print(f"⚙️  Генерация эмбеддингов...")

        generated = 0
        batch_size = 10  # Небольшие батчи для API

        for i in range(0, total, batch_size):
            batch = criteria_without_embeddings[i:i+batch_size]

            for row in batch:
                criteria_id, article, subpoint, description = row

                try:
                    # Формируем текст для эмбеддинга
                    text_for_embedding = f"Статья {article}"
                    if subpoint:
                        text_for_embedding += f", подпункт {subpoint}"
                    text_for_embedding += f": {description}"

                    # Генерируем эмбеддинг через OpenAI
                    embedding = await openai_service.create_embedding(text_for_embedding)

                    # Конвертируем вектор в строку формата '[1.0,2.0,3.0]' для PostgreSQL
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                    # Сохраняем в БД
                    # Используем CAST вместо ::vector для избежания проблем с синтаксисом
                    await db.execute(text("""
                        UPDATE point_criteria
                        SET criteria_embedding = CAST(:embedding AS vector)
                        WHERE id = :id
                    """), {
                        'id': criteria_id,
                        'embedding': embedding_str
                    })

                    generated += 1

                    # Коммитим каждые 10 записей
                    if generated % 10 == 0:
                        await db.commit()
                        print(f"   Сгенерировано: {generated}/{total} ({generated*100//total}%)", end='\r')

                except Exception as e:
                    print(f"\n⚠️  Ошибка при генерации эмбеддинга для критерия {criteria_id}: {e}")
                    continue

            # Коммитим батч
            await db.commit()

        print(f"\n✅ Сгенерировано эмбеддингов: {generated}/{total}")


async def verify_data():
    """Проверка загруженных данных"""

    print("\n" + "=" * 100)
    print("ПРОВЕРКА ЗАГРУЖЕННЫХ ДАННЫХ")
    print("=" * 100)

    async with SessionLocal() as db:
        # Общая статистика
        result = await db.execute(text("SELECT COUNT(*) as total FROM point_criteria"))
        total = result.scalar()
        print(f"📊 Всего критериев в БД: {total}")

        # Критерии с эмбеддингами
        result = await db.execute(text("""
            SELECT COUNT(*) as with_embeddings
            FROM point_criteria
            WHERE criteria_embedding IS NOT NULL
        """))
        with_embeddings = result.scalar()
        print(f"✅ С эмбеддингами: {with_embeddings} ({with_embeddings*100//total}%)")

        # Статистика по статье 66
        result = await db.execute(text("""
            SELECT COUNT(*) as count
            FROM point_criteria
            WHERE article = 66
        """))
        article_66_count = result.scalar()
        print(f"\n📋 Статья 66: {article_66_count} критериев")

        # Примеры критериев для статьи 66, подпункт 1
        result = await db.execute(text("""
            SELECT id, LEFT(description, 100) as desc_preview,
                   CASE WHEN criteria_embedding IS NULL THEN 'НЕТ' ELSE 'ЕСТЬ' END as embedding
            FROM point_criteria
            WHERE article = 66 AND subpoint = '1'
            LIMIT 5
        """))
        examples = result.fetchall()

        print(f"\n🔍 Примеры критериев для статьи 66, подпункт 1:")
        for row in examples:
            print(f"   ID {row[0]}: {row[1]}... | Эмбеддинг: {row[2]}")


async def main():
    """Основная функция"""

    print("\n" + "=" * 100)
    print("ЗАГРУЗКА ДЕТАЛЬНЫХ КРИТЕРИЕВ С ВЕКТОРНЫМИ ЭМБЕДДИНГАМИ")
    print("=" * 100)
    print(f"Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Шаг 1: Удаляем старые данные
        choice = input("⚠️  Удалить существующие критерии? (y/N): ").strip().lower()
        if choice == 'y':
            await clear_existing_criteria()

        # Шаг 2: Загружаем детальные критерии
        loaded = await load_detailed_criteria()

        if loaded > 0:
            # Шаг 3: Генерируем эмбеддинги
            choice = input("\n⚙️  Сгенерировать векторные эмбеддинги? (Y/n): ").strip().lower()
            if choice != 'n':
                await generate_embeddings()

        # Шаг 4: Проверяем результат
        await verify_data()

        print("\n" + "=" * 100)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 100)
        print(f"Окончание: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
