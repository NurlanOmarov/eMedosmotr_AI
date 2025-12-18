#!/usr/bin/env python3
"""
Тестирование векторного поиска по детальным критериям
Проверка работы RAG-системы после загрузки детальных критериев
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Добавляем путь к приложению
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.utils.database import SessionLocal
from app.services.openai_client import openai_service


# Тестовые кейсы для проверки векторного поиска
TEST_CASES = [
    {
        "name": "Невролог - критический стеноз",
        "query": "грыжа межпозвоночного диска с критическим стенозом канала, корешковый синдром, парез стопы, нарушение функции тазовых органов",
        "expected_article": 66,
        "expected_subpoint": 1,
        "keywords": ["стеноз", "парез", "сфинктер", "корешковый"]
    },
    {
        "name": "Близорукость высокой степени",
        "query": "миопия 12 диоптрий на правом глазу",
        "expected_article": 34,
        "expected_subpoint": 1,
        "keywords": ["миопия", "диоптр"]
    },
    {
        "name": "Сколиоз II степени",
        "query": "сколиоз второй степени угол Кобба 20 градусов",
        "expected_article": 66,
        "expected_subpoint": 3,
        "keywords": ["сколиоз", "градус"]
    },
    {
        "name": "Умеренная дорсопатия",
        "query": "межпозвоночный остеохондроз с умеренным болевым синдромом, ограничение движений 30 процентов",
        "expected_article": 66,
        "expected_subpoint": 2,
        "keywords": ["остеохондроз", "умеренн"]
    }
]


async def test_vector_search(test_case: dict, top_k: int = 5):
    """
    Тестирование векторного поиска для одного кейса

    Args:
        test_case: Тестовый кейс
        top_k: Количество результатов
    """
    query = test_case["query"]
    expected_article = test_case["expected_article"]
    expected_subpoint = test_case["expected_subpoint"]
    keywords = test_case.get("keywords", [])

    print(f"\n{'='*100}")
    print(f"📝 ТЕСТ: {test_case['name']}")
    print(f"{'='*100}")
    print(f"Запрос: {query}")
    print(f"Ожидается: Статья {expected_article}, подпункт {expected_subpoint}")
    print()

    # Генерируем эмбеддинг для запроса
    query_embedding = await openai_service.create_embedding(query)
    print(f"✅ Эмбеддинг запроса сгенерирован (размерность: {len(query_embedding)})")

    # Выполняем векторный поиск
    async with SessionLocal() as db:
        # Поиск по косинусному расстоянию (1 - cosine similarity)
        # Конвертируем вектор в строку для PostgreSQL
        query_embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

        search_query = text("""
            SELECT
                id,
                article,
                subpoint,
                LEFT(description, 200) as description_preview,
                1 - (criteria_embedding <=> CAST(:query_embedding AS vector)) as similarity
            FROM point_criteria
            WHERE criteria_embedding IS NOT NULL
            ORDER BY criteria_embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        result = await db.execute(search_query, {
            'query_embedding': query_embedding_str,
            'top_k': top_k
        })

        results = result.fetchall()

        print(f"\n🔍 Найдено {len(results)} наиболее похожих критериев:\n")

        for i, row in enumerate(results, 1):
            criteria_id, article, subpoint, description, similarity = row

            # Проверяем совпадение
            is_match = (article == expected_article and
                       (subpoint == str(expected_subpoint) or subpoint == expected_subpoint))

            # Проверяем наличие ключевых слов
            keywords_found = [kw for kw in keywords if kw.lower() in description.lower()]

            status = "✅ MATCH!" if is_match else ""

            print(f"{i}. Статья {article}, подпункт {subpoint} | Similarity: {similarity:.4f} {status}")
            print(f"   {description}...")
            if keywords_found:
                print(f"   🔑 Найденные ключевые слова: {', '.join(keywords_found)}")
            print()

        # Анализ результатов
        print(f"\n{'─'*100}")
        print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")

        # Проверяем, есть ли ожидаемая статья в топ-5
        top_articles = [row[1] for row in results]
        top_subpoints = [str(row[2]) for row in results]

        if expected_article in top_articles:
            rank = top_articles.index(expected_article) + 1
            print(f"✅ Ожидаемая статья {expected_article} найдена на позиции {rank}")

            # Проверяем подпункт
            if expected_article == results[rank-1][1] and str(expected_subpoint) == str(results[rank-1][2]):
                print(f"✅ Подпункт {expected_subpoint} также совпадает!")
            else:
                actual_subpoint = results[rank-1][2]
                print(f"⚠️  Подпункт не совпадает: ожидалось {expected_subpoint}, найдено {actual_subpoint}")
        else:
            print(f"❌ Ожидаемая статья {expected_article} НЕ найдена в топ-{top_k}")
            print(f"   Найденные статьи: {', '.join(map(str, top_articles))}")

        # Оценка качества поиска
        if results:
            best_similarity = results[0][4]
            if best_similarity >= 0.8:
                quality = "ОТЛИЧНО"
            elif best_similarity >= 0.6:
                quality = "ХОРОШО"
            elif best_similarity >= 0.4:
                quality = "УДОВЛЕТВОРИТЕЛЬНО"
            else:
                quality = "ПЛОХО"

            print(f"\n🎯 Качество поиска: {quality} (similarity={best_similarity:.4f})")

        return results


async def run_all_tests():
    """Запуск всех тестов"""

    print("\n" + "="*100)
    print("ТЕСТИРОВАНИЕ ВЕКТОРНОГО ПОИСКА ПО ДЕТАЛЬНЫМ КРИТЕРИЯМ")
    print("="*100)
    print(f"Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Проверяем наличие данных
    async with SessionLocal() as db:
        result = await db.execute(text("SELECT COUNT(*) FROM point_criteria WHERE criteria_embedding IS NOT NULL"))
        count = result.scalar()
        print(f"📊 Критериев с эмбеддингами в БД: {count}")

        if count == 0:
            print("\n❌ ОШИБКА: В БД нет критериев с эмбеддингами!")
            print("   Сначала запустите: python scripts/load_detailed_criteria.py")
            return

    print()

    # Запускаем все тесты
    success_count = 0
    for test_case in TEST_CASES:
        try:
            results = await test_vector_search(test_case, top_k=5)

            # Проверяем успешность
            if results and results[0][1] == test_case["expected_article"]:
                success_count += 1

        except Exception as e:
            print(f"\n❌ ОШИБКА при выполнении теста: {e}")
            import traceback
            traceback.print_exc()

    # Итоговая статистика
    print("\n" + "="*100)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("="*100)
    print(f"Всего тестов: {len(TEST_CASES)}")
    print(f"Успешных: {success_count}")
    print(f"Неудачных: {len(TEST_CASES) - success_count}")
    print(f"Процент успеха: {success_count*100//len(TEST_CASES)}%")
    print()
    print(f"Окончание: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)


async def interactive_search():
    """Интерактивный поиск"""

    print("\n" + "="*100)
    print("🔍 ИНТЕРАКТИВНЫЙ ВЕКТОРНЫЙ ПОИСК")
    print("="*100)
    print("Введите медицинское описание для поиска похожих критериев")
    print("(или 'exit' для выхода)")
    print()

    while True:
        query = input("\n📝 Запрос: ").strip()

        if query.lower() in ['exit', 'quit', 'q']:
            break

        if not query:
            continue

        try:
            # Создаем тестовый кейс
            test_case = {
                "name": "Интерактивный запрос",
                "query": query,
                "expected_article": None,
                "expected_subpoint": None
            }

            await test_vector_search(test_case, top_k=10)

        except Exception as e:
            print(f"❌ Ошибка: {e}")


async def main():
    """Основная функция"""

    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        await interactive_search()
    else:
        await run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
