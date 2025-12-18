#!/usr/bin/env python3
"""
Скрипт для обновления категорий (graph_1-4) в таблице point_criteria
через docker exec psql.

Читает данные из points_diagnoses_rows.csv и генерирует SQL команды.
"""

import csv
import re
import subprocess
from pathlib import Path

# Путь к справочникам
REFERENCES_DIR = Path(__file__).parent.parent.parent / "справочник приказ 722"


def normalize_subpoint(subpoint_raw: str) -> str:
    """Нормализация подпункта"""
    if not subpoint_raw:
        return ""
    subpoint = subpoint_raw.strip()
    match = re.match(r'^(\d+)[)\.]?\s*', subpoint)
    if match:
        return match.group(1)
    return subpoint.rstrip(')').strip()


def escape_sql(value):
    """Экранирование для SQL"""
    if value is None or value == '':
        return 'NULL'
    return "'" + value.replace("'", "''") + "'"


def load_and_generate_sql():
    """Загрузка данных и генерация SQL"""
    csv_path = REFERENCES_DIR / "points_diagnoses_rows.csv"

    print(f"Чтение файла: {csv_path}")

    sql_commands = []
    categories_map = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            point = row.get('point', '').strip()
            if not point or not point.isdigit():
                continue

            article = int(point)
            subpoint_raw = row.get('subpoint', '').strip()
            subpoint = normalize_subpoint(subpoint_raw)

            if not subpoint:
                continue

            graph_1 = row.get('graph_1', '').strip() or None
            graph_2 = row.get('graph_2', '').strip() or None
            graph_3 = row.get('graph_3', '').strip() or None
            graph_4 = row.get('graph_4', '').strip() or None

            if not any([graph_1, graph_2, graph_3, graph_4]):
                continue

            key = (article, subpoint)
            if key in categories_map:
                continue  # Уже обработали

            categories_map[key] = True

            # Генерируем SQL
            sql = f"""UPDATE point_criteria SET graph_1={escape_sql(graph_1)}, graph_2={escape_sql(graph_2)}, graph_3={escape_sql(graph_3)}, graph_4={escape_sql(graph_4)} WHERE article={article} AND subpoint='{subpoint}';"""
            sql_commands.append(sql)

    print(f"Сгенерировано {len(sql_commands)} SQL команд")
    return sql_commands


def execute_via_docker(sql_commands):
    """Выполнение SQL через docker exec"""
    print("\nВыполнение через docker exec psql...")

    # Объединяем все команды
    all_sql = "\n".join(sql_commands)

    # Записываем во временный файл
    sql_file = "/tmp/update_categories.sql"
    with open(sql_file, 'w') as f:
        f.write(all_sql)

    # Копируем в контейнер
    subprocess.run([
        "docker", "cp", sql_file, "emedosmotr_db:/tmp/update_categories.sql"
    ], check=True)

    # Выполняем
    result = subprocess.run([
        "docker", "exec", "emedosmotr_db",
        "psql", "-U", "admin", "-d", "emedosmotr",
        "-f", "/tmp/update_categories.sql"
    ], capture_output=True, text=True)

    print("STDOUT:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)

    return result.returncode == 0


def verify_update():
    """Проверка результатов"""
    print("\n" + "="*60)
    print("ПРОВЕРКА РЕЗУЛЬТАТОВ")
    print("="*60)

    # Проверяем количество обновленных записей
    result = subprocess.run([
        "docker", "exec", "emedosmotr_db",
        "psql", "-U", "admin", "-d", "emedosmotr", "-c",
        "SELECT COUNT(*) as total, COUNT(NULLIF(graph_1, '')) as with_categories FROM point_criteria;"
    ], capture_output=True, text=True)
    print(result.stdout)

    # Примеры с категориями
    result = subprocess.run([
        "docker", "exec", "emedosmotr_db",
        "psql", "-U", "admin", "-d", "emedosmotr", "-c",
        "SELECT article, subpoint, graph_1, graph_2, graph_3, graph_4 FROM point_criteria WHERE graph_1 IS NOT NULL AND graph_1 != '' ORDER BY article, subpoint LIMIT 15;"
    ], capture_output=True, text=True)
    print(result.stdout)


def main():
    print("="*60)
    print("ОБНОВЛЕНИЕ КАТЕГОРИЙ В POINT_CRITERIA (через Docker)")
    print("="*60)

    try:
        # Генерируем SQL
        sql_commands = load_and_generate_sql()

        if not sql_commands:
            print("❌ Не найдено команд для выполнения")
            return 1

        # Выполняем через Docker
        success = execute_via_docker(sql_commands)

        if success:
            print("\n✅ SQL выполнен успешно")
        else:
            print("\n⚠️ Были ошибки при выполнении")

        # Проверяем
        verify_update()

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
