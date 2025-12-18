#!/usr/bin/env python3
"""
Скрипт для обновления категорий (graph_1-4) в таблице point_criteria
из файла points_diagnoses_rows.csv (Приложение 1 Приказа 722)

Приложение 1 содержит таблицу с категориями годности по графам.
Приложение 2 (point_criteria_full.csv) содержит пояснения к критериям.

Этот скрипт связывает данные по article + subpoint.
"""

import csv
import re
from pathlib import Path
import psycopg2

# Параметры подключения к БД
DB_PARAMS = {
    'dbname': 'emedosmotr',
    'user': 'admin',
    'password': 'secure_password',
    'host': 'localhost',
    'port': 5432
}

# Путь к справочникам
REFERENCES_DIR = Path(__file__).parent.parent.parent / "справочник приказ 722"


def normalize_subpoint(subpoint_raw: str) -> str:
    """
    Нормализация подпункта из CSV для сопоставления с БД

    Примеры:
    "1) не поддающиеся..." -> "1"
    "2) временные функциональные..." -> "2"
    "3)" -> "3"
    """
    if not subpoint_raw:
        return ""

    # Убираем пробелы
    subpoint = subpoint_raw.strip()

    # Ищем числа в начале строки (1), 2), 1., и т.д.)
    match = re.match(r'^(\d+)[)\.]?\s*', subpoint)
    if match:
        return match.group(1)

    # Если не нашли число, возвращаем как есть (без скобок)
    return subpoint.rstrip(')').strip()


def load_categories_from_csv():
    """Загрузка категорий из points_diagnoses_rows.csv"""
    csv_path = REFERENCES_DIR / "points_diagnoses_rows.csv"

    print(f"Чтение файла: {csv_path}")

    categories_map = {}  # {(article, subpoint): {1: cat, 2: cat, 3: cat, 4: cat}}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Получаем номер статьи
            point = row.get('point', '').strip()
            if not point or not point.isdigit():
                continue

            article = int(point)

            # Получаем подпункт (нормализуем)
            subpoint_raw = row.get('subpoint', '').strip()
            subpoint = normalize_subpoint(subpoint_raw)

            if not subpoint:
                continue

            # Получаем категории
            graph_1 = row.get('graph_1', '').strip() or None
            graph_2 = row.get('graph_2', '').strip() or None
            graph_3 = row.get('graph_3', '').strip() or None
            graph_4 = row.get('graph_4', '').strip() or None

            # Пропускаем если нет категорий
            if not any([graph_1, graph_2, graph_3, graph_4]):
                continue

            key = (article, subpoint)

            # Сохраняем (может быть несколько записей для одного подпункта)
            if key not in categories_map:
                categories_map[key] = {
                    1: graph_1,
                    2: graph_2,
                    3: graph_3,
                    4: graph_4
                }

    print(f"Загружено {len(categories_map)} уникальных комбинаций статья+подпункт с категориями")
    return categories_map


def update_point_criteria(conn, categories_map):
    """Обновление категорий в таблице point_criteria"""
    print("\nОбновление категорий в point_criteria...")

    updated_count = 0
    not_found_count = 0
    not_found_list = []

    with conn.cursor() as cur:
        for (article, subpoint), categories in categories_map.items():
            # Обновляем все записи с этим article+subpoint
            # Используем LIKE для подпунктов с возможным разным форматом
            cur.execute(
                """
                UPDATE point_criteria
                SET graph_1 = COALESCE(%s, graph_1),
                    graph_2 = COALESCE(%s, graph_2),
                    graph_3 = COALESCE(%s, graph_3),
                    graph_4 = COALESCE(%s, graph_4)
                WHERE article = %s AND (
                    subpoint = %s OR
                    subpoint = %s OR
                    subpoint LIKE %s
                )
                RETURNING id
                """,
                (
                    categories[1],
                    categories[2],
                    categories[3],
                    categories[4],
                    article,
                    subpoint,          # точное совпадение "1"
                    subpoint + ")",    # формат "1)"
                    subpoint + "%"     # формат "1..." (начинается с)
                )
            )

            rows = cur.fetchall()
            if rows:
                updated_count += len(rows)
            else:
                not_found_count += 1
                not_found_list.append((article, subpoint))

    conn.commit()

    print(f"\n✅ Обновлено записей: {updated_count}")
    print(f"⚠️ Не найдено в БД: {not_found_count}")

    # Выводим первые 15 не найденных
    if not_found_list:
        print("\nНе найденные записи (первые 15):")
        for article, subpoint in not_found_list[:15]:
            print(f"  - Статья {article}, подпункт '{subpoint}'")

    return updated_count


def verify_update(conn):
    """Проверка результатов обновления"""
    print("\n" + "="*60)
    print("ПРОВЕРКА РЕЗУЛЬТАТОВ")
    print("="*60)

    with conn.cursor() as cur:
        # Общая статистика
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(graph_1) as with_g1,
                COUNT(NULLIF(graph_1, '')) as non_empty_g1
            FROM point_criteria
        """)
        total, with_g1, non_empty_g1 = cur.fetchone()

        print(f"\nОбщая статистика point_criteria:")
        print(f"  - Всего записей: {total}")
        print(f"  - С graph_1 (не NULL): {with_g1}")
        print(f"  - С непустым graph_1: {non_empty_g1}")

        # Примеры с категориями
        print(f"\nПримеры записей с категориями:")
        cur.execute("""
            SELECT article, subpoint, graph_1, graph_2, graph_3, graph_4
            FROM point_criteria
            WHERE graph_1 IS NOT NULL AND graph_1 != ''
            ORDER BY article, subpoint
            LIMIT 10
        """)

        for row in cur.fetchall():
            article, subpoint, g1, g2, g3, g4 = row
            print(f"  Ст.{article} пп.{subpoint}: Г1={g1}, Г2={g2}, Г3={g3}, Г4={g4}")

        # Проверка важных статей
        print(f"\nПроверка важных статей (43, 66):")
        for article in [43, 66]:
            cur.execute("""
                SELECT subpoint, graph_1, graph_2
                FROM point_criteria
                WHERE article = %s AND graph_1 IS NOT NULL AND graph_1 != ''
                ORDER BY subpoint
                LIMIT 5
            """, (article,))

            rows = cur.fetchall()
            print(f"  Статья {article}: {len(rows)} подпунктов с категориями")
            for sp, g1, g2 in rows[:3]:
                print(f"    пп.{sp}: Г1={g1}, Г2={g2}")


def main():
    print("="*60)
    print("ОБНОВЛЕНИЕ КАТЕГОРИЙ В POINT_CRITERIA")
    print("="*60)

    try:
        # Загружаем категории из CSV
        categories_map = load_categories_from_csv()

        if not categories_map:
            print("❌ Не найдено категорий для обновления")
            return

        # Подключаемся к БД
        print("\nПодключение к PostgreSQL...")
        conn = psycopg2.connect(**DB_PARAMS)
        print("✅ Подключение установлено")

        # Обновляем
        update_point_criteria(conn, categories_map)

        # Проверяем
        verify_update(conn)

        conn.close()

        print("\n" + "="*60)
        print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
