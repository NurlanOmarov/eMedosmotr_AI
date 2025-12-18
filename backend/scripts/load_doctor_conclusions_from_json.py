"""
Скрипт для загрузки заключений врачей из JSON файла с примерами
Создает тестовых призывников и сохраняет для них записи врачей
ОБНОВЛЕН: Поддержка всех 3 секций test_cases
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import date, datetime
import uuid

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

from app.config import settings


# Маппинг специальностей на русские названия
SPECIALTY_MAP = {
    'Терапевт': 'Терапевт',
    'Хирург': 'Хирург',
    'Офтальмолог': 'Офтальмолог',
    'Невролог': 'Невролог',
    'Кардиолог': 'Кардиолог',
    'Отоларинголог': 'Отоларинголог',
    'Дерматолог': 'Дерматолог',
    'Психиатр': 'Психиатр',
    'Стоматолог': 'Стоматолог',
    'Фтизиатр': 'Фтизиатр',
}


async def load_doctor_conclusions():
    """Загрузить заключения врачей из JSON файла"""

    # Путь к JSON файлу
    json_path = Path(__file__).parent.parent / "test_data" / "doctor_conclusions_examples.json"

    if not json_path.exists():
        print(f"❌ Файл не найден: {json_path}")
        return

    # Загружаем JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Собираем все тестовые случаи из 3 секций
    all_cases = []

    # 1. Основные тестовые случаи
    test_cases = data.get('test_cases', [])
    print(f"📋 Найдено {len(test_cases)} основных тестовых случаев")
    all_cases.extend(test_cases)

    # 2. Случаи с противоречиями
    contradiction_cases = data.get('contradiction_test_cases', [])
    print(f"📋 Найдено {len(contradiction_cases)} случаев с противоречиями")
    all_cases.extend(contradiction_cases)

    # 3. Случаи для недостающих специалистов
    missing_specialists_cases = data.get('missing_specialists_test_cases', [])
    print(f"📋 Найдено {len(missing_specialists_cases)} случаев для дополнительных специалистов")
    all_cases.extend(missing_specialists_cases)

    # 4. Полные случаи обследования (все 9 специалистов для одного призывника)
    complete_examination_cases = data.get('complete_examination_cases', [])
    print(f"📋 Найдено {len(complete_examination_cases)} полных случаев обследования (все 9 специалистов)")

    print(f"\n📊 ВСЕГО: {len(all_cases)} обычных случаев + {len(complete_examination_cases)} полных обследований")

    # Создаем движок БД
    database_url = settings.DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True
    )

    # Создаем сессию
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Группируем тестовые случаи по case_id (каждый case_id = 1 призывник)
            conscripts_data = {}

            for case in all_cases:
                case_id = case.get('case_id')
                name = case.get('name', f'Тестовый случай {case_id}')

                # Каждый case_id = отдельный призывник с одним заключением
                if case_id not in conscripts_data:
                    conscripts_data[case_id] = {
                        'name': name,
                        'case_type': case.get('contradiction_type', 'NORMAL'),
                        'examinations': []
                    }

                conscripts_data[case_id]['examinations'].append(case)

            print(f"\n📊 Будет создано/обновлено {len(conscripts_data)} призывников")

            created_conscripts = 0
            created_drafts = 0
            created_examinations = 0

            # Создаем призывников и записи врачей
            for case_id, conscript_data in conscripts_data.items():
                print(f"\n{'='*80}")
                print(f"📝 Обработка случая #{case_id}: {conscript_data['name']}")
                case_type = conscript_data['case_type']
                if case_type != 'NORMAL':
                    print(f"   🔴 Тип противоречия: {case_type}")
                print(f"{'='*80}")

                # Генерируем уникальный ИИН на основе case_id
                iin = f"99010130{case_id:04d}"

                # Проверяем существование призывника
                check_query = text("SELECT id, iin, first_name, last_name FROM conscripts WHERE iin = :iin")
                result = await session.execute(check_query, {'iin': iin})
                existing_conscript = result.fetchone()

                if existing_conscript:
                    print(f"✅ Призывник уже существует: {existing_conscript.last_name} {existing_conscript.first_name} (IIN: {iin})")
                    conscript_id = existing_conscript.id
                else:
                    # Создаем нового призывника
                    new_id = uuid.uuid4()
                    insert_conscript = text("""
                        INSERT INTO conscripts (id, iin, full_name, first_name, last_name, middle_name, date_of_birth, gender, address, phone, created_at, updated_at)
                        VALUES (:id, :iin, :full_name, :first_name, :last_name, :middle_name, :birth_date, :gender, :address, :phone, :created_at, :updated_at)
                        RETURNING id, iin, first_name, last_name
                    """)

                    # Формируем имя на основе case_id и типа случая
                    first_name = 'ТЕСТОВЫЙ'
                    if case_id >= 100 and case_id < 200:
                        last_name = 'ПРОТИВОРЕЧИЕ'
                    elif case_id >= 200:
                        last_name = 'СПЕЦИАЛИСТ'
                    else:
                        last_name = 'ПРИЗЫВНИК'
                    middle_name = f'СЛУЧАЙ{case_id}'

                    full_name = f'{last_name} {first_name} {middle_name}'
                    now = datetime.now()
                    result = await session.execute(
                        insert_conscript,
                        {
                            'id': new_id,
                            'iin': iin,
                            'full_name': full_name,
                            'first_name': first_name,
                            'last_name': last_name,
                            'middle_name': middle_name,
                            'birth_date': date(1999, 1, 1),
                            'gender': 'М',
                            'address': f'г. Тестовый, ул. Тестовая {case_id}',
                            'phone': f'+7700{case_id:07d}',
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    conscript_row = result.fetchone()
                    conscript_id = conscript_row.id
                    created_conscripts += 1
                    await session.flush()
                    print(f"✅ Создан призывник: {conscript_row.last_name} {conscript_row.first_name} (IIN: {iin})")

                # Проверяем существование призывной кампании (conscript_drafts)
                check_draft = text("SELECT id FROM conscript_drafts WHERE conscript_id = :conscript_id")
                draft_result = await session.execute(check_draft, {'conscript_id': conscript_id})
                existing_draft = draft_result.fetchone()

                if existing_draft:
                    print(f"✅ Призывная кампания уже существует (ID: {existing_draft.id})")
                    draft_id = existing_draft.id
                else:
                    # Создаем призывную кампанию
                    new_draft_id = uuid.uuid4()
                    insert_draft = text("""
                        INSERT INTO conscript_drafts (id, conscript_id, draft_name, draft_season, draft_year,
                                                       category_graph_id, status, commission_location, commission_date, created_at, updated_at)
                        VALUES (:id, :conscript_id, :draft_name, :draft_season, :draft_year,
                                :category_graph_id, :status, :commission_location, :commission_date, :created_at, :updated_at)
                        RETURNING id
                    """)
                    now = datetime.now()
                    draft_result = await session.execute(
                        insert_draft,
                        {
                            'id': new_draft_id,
                            'conscript_id': conscript_id,
                            'draft_name': f'ВЕСНА-2025-{case_id:04d}',
                            'draft_season': 'Весна',
                            'draft_year': 2025,
                            'category_graph_id': 1,  # График 1 - призывники
                            'status': 'in_progress',
                            'commission_location': 'Тестовый военкомат',
                            'commission_date': date.today(),
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    draft_row = draft_result.fetchone()
                    draft_id = draft_row.id
                    created_drafts += 1
                    await session.flush()
                    print(f"✅ Создана призывная кампания (ID: {draft_id})")

                # Создаем записи врачей (specialist_examinations)
                examinations_added = 0
                for exam_data in conscript_data['examinations']:
                    specialty = exam_data.get('specialty', 'Терапевт')
                    specialty_ru = SPECIALTY_MAP.get(specialty, specialty)
                    doctor_name = exam_data.get('doctor_name', 'Тестовый врач')

                    # Проверяем, существует ли уже запись этого врача
                    check_exam = text("""
                        SELECT id FROM specialists_examinations
                        WHERE conscript_draft_id = :draft_id AND specialty = :specialty
                    """)
                    exam_result = await session.execute(
                        check_exam,
                        {
                            'draft_id': draft_id,
                            'specialty': specialty
                        }
                    )
                    existing_exam = exam_result.fetchone()

                    if existing_exam:
                        print(f"   ⚠️  Запись {specialty} уже существует, пропускаем")
                        continue

                    # Получаем первый ICD10 код из списка
                    icd10_codes = exam_data.get('icd10_codes', [])
                    icd10_code = icd10_codes[0] if icd10_codes else 'Z00.0'

                    # Получаем статью и подпункт
                    article = exam_data.get('expected_article')
                    subpoint = exam_data.get('expected_subpoint')
                    category = exam_data.get('doctor_category', 'А')

                    # Создаем запись врача
                    new_exam_id = uuid.uuid4()
                    insert_exam = text("""
                        INSERT INTO specialists_examinations
                        (id, conscript_draft_id, specialty, specialty_ru, diagnosis_text, icd10_code,
                         doctor_category, doctor_name, conclusion_text,
                         complaints, anamnesis, objective_data, special_research_results,
                         examination_date, created_at, updated_at)
                        VALUES
                        (:id, :draft_id, :specialty, :specialty_ru, :diagnosis_text, :icd10_code,
                         :doctor_category, :doctor_name, :conclusion_text,
                         :complaints, :anamnesis, :objective_data, :special_research_results,
                         :examination_date, :created_at, :updated_at)
                        RETURNING id
                    """)

                    # Формируем текст диагноза
                    diagnosis_text = exam_data.get('diagnosis_text', '') or exam_data.get('conclusion', '')
                    anamnesis = exam_data.get('anamnesis', '')
                    conclusion = exam_data.get('conclusion', '')

                    # Если есть и анамнез и заключение, формируем полный текст
                    if anamnesis and conclusion:
                        diagnosis_full = f"АНАМНЕЗ:\n{anamnesis}\n\nЗАКЛЮЧЕНИЕ:\n{conclusion}"
                    else:
                        diagnosis_full = diagnosis_text or conclusion or anamnesis or ''

                    now = datetime.now()
                    exam_result = await session.execute(
                        insert_exam,
                        {
                            'id': new_exam_id,
                            'draft_id': draft_id,
                            'specialty': specialty,
                            'specialty_ru': specialty_ru,
                            'diagnosis_text': diagnosis_full or 'Без диагноза',
                            'icd10_code': icd10_code,
                            'doctor_category': category,
                            'doctor_name': doctor_name,
                            'conclusion_text': conclusion or diagnosis_full or 'Без заключения',
                            'complaints': exam_data.get('complaints', ''),
                            'anamnesis': anamnesis,
                            'objective_data': exam_data.get('objective_data', conclusion),
                            'special_research_results': exam_data.get('special_research_results', ''),
                            'examination_date': now.date(),
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    exam_row = exam_result.fetchone()
                    examinations_added += 1
                    created_examinations += 1

                    article_info = f"ст.{article}, п.{subpoint}" if article and subpoint else "без статьи"
                    print(f"   ✅ {specialty_ru}: категория {category} ({article_info})")

                await session.flush()
                if examinations_added > 0:
                    print(f"\n📊 Для случая #{case_id} добавлено {examinations_added} записей врачей")

            # =============================================
            # ОБРАБОТКА ПОЛНЫХ СЛУЧАЕВ ОБСЛЕДОВАНИЯ
            # (все 9 специалистов для одного призывника)
            # =============================================
            print(f"\n{'='*80}")
            print("📋 ЗАГРУЗКА ПОЛНЫХ СЛУЧАЕВ ОБСЛЕДОВАНИЯ (все 9 специалистов)")
            print(f"{'='*80}")

            for complete_case in complete_examination_cases:
                case_id = complete_case.get('case_id')
                name = complete_case.get('name', f'Полный случай {case_id}')
                description = complete_case.get('description', '')
                expected_category = complete_case.get('expected_final_category', 'А')

                print(f"\n{'='*80}")
                print(f"📝 Обработка полного случая #{case_id}: {name}")
                print(f"   📌 {description}")
                print(f"   🎯 Ожидаемая итоговая категория: {expected_category}")
                if complete_case.get('has_error'):
                    print(f"   ⚠️  Содержит ошибку врача: {complete_case.get('error_specialty')}")
                print(f"{'='*80}")

                # Генерируем ИИН для полного случая (серия 3xx)
                iin = f"99010130{case_id:04d}"

                # Проверяем существование призывника
                check_query = text("SELECT id, iin, first_name, last_name FROM conscripts WHERE iin = :iin")
                result = await session.execute(check_query, {'iin': iin})
                existing_conscript = result.fetchone()

                if existing_conscript:
                    print(f"✅ Призывник уже существует: {existing_conscript.last_name} {existing_conscript.first_name} (IIN: {iin})")
                    conscript_id = existing_conscript.id
                else:
                    # Создаем нового призывника для полного случая
                    new_id = uuid.uuid4()
                    insert_conscript = text("""
                        INSERT INTO conscripts (id, iin, full_name, first_name, last_name, middle_name, date_of_birth, gender, address, phone, created_at, updated_at)
                        VALUES (:id, :iin, :full_name, :first_name, :last_name, :middle_name, :birth_date, :gender, :address, :phone, :created_at, :updated_at)
                        RETURNING id, iin, first_name, last_name
                    """)

                    first_name = 'ПОЛНЫЙ'
                    last_name = 'ОСМОТР'
                    middle_name = f'СЛУЧАЙ{case_id}'

                    full_name = f'{last_name} {first_name} {middle_name}'
                    now = datetime.now()
                    result = await session.execute(
                        insert_conscript,
                        {
                            'id': new_id,
                            'iin': iin,
                            'full_name': full_name,
                            'first_name': first_name,
                            'last_name': last_name,
                            'middle_name': middle_name,
                            'birth_date': date(1999, 1, 1),
                            'gender': 'М',
                            'address': f'г. Тестовый, ул. Полная {case_id}',
                            'phone': f'+7700{case_id:07d}',
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    conscript_row = result.fetchone()
                    conscript_id = conscript_row.id
                    created_conscripts += 1
                    await session.flush()
                    print(f"✅ Создан призывник: {conscript_row.last_name} {conscript_row.first_name} (IIN: {iin})")

                # Проверяем/создаем призывную кампанию
                check_draft = text("SELECT id FROM conscript_drafts WHERE conscript_id = :conscript_id")
                draft_result = await session.execute(check_draft, {'conscript_id': conscript_id})
                existing_draft = draft_result.fetchone()

                if existing_draft:
                    print(f"✅ Призывная кампания уже существует (ID: {existing_draft.id})")
                    draft_id = existing_draft.id
                else:
                    new_draft_id = uuid.uuid4()
                    insert_draft = text("""
                        INSERT INTO conscript_drafts (id, conscript_id, draft_name, draft_season, draft_year,
                                                       category_graph_id, status, commission_location, commission_date, created_at, updated_at)
                        VALUES (:id, :conscript_id, :draft_name, :draft_season, :draft_year,
                                :category_graph_id, :status, :commission_location, :commission_date, :created_at, :updated_at)
                        RETURNING id
                    """)
                    now = datetime.now()
                    draft_result = await session.execute(
                        insert_draft,
                        {
                            'id': new_draft_id,
                            'conscript_id': conscript_id,
                            'draft_name': f'ПОЛНЫЙ-2025-{case_id:04d}',
                            'draft_season': 'Весна',
                            'draft_year': 2025,
                            'category_graph_id': 1,
                            'status': 'in_progress',
                            'commission_location': 'Тестовый военкомат (полные обследования)',
                            'commission_date': date.today(),
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    draft_row = draft_result.fetchone()
                    draft_id = draft_row.id
                    created_drafts += 1
                    await session.flush()
                    print(f"✅ Создана призывная кампания (ID: {draft_id})")

                # Создаем записи для ВСЕХ 9 специалистов
                examinations_list = complete_case.get('examinations', [])
                examinations_added = 0

                for exam_data in examinations_list:
                    specialty = exam_data.get('specialty', 'Терапевт')
                    specialty_ru = SPECIALTY_MAP.get(specialty, specialty)
                    doctor_name = exam_data.get('doctor_name', 'Тестовый врач')

                    # Проверяем, существует ли уже запись
                    check_exam = text("""
                        SELECT id FROM specialists_examinations
                        WHERE conscript_draft_id = :draft_id AND specialty = :specialty
                    """)
                    exam_result = await session.execute(
                        check_exam,
                        {'draft_id': draft_id, 'specialty': specialty}
                    )
                    existing_exam = exam_result.fetchone()

                    if existing_exam:
                        print(f"   ⚠️  Запись {specialty} уже существует, пропускаем")
                        continue

                    # Получаем данные
                    icd10_codes = exam_data.get('icd10_codes', [])
                    icd10_code = icd10_codes[0] if icd10_codes else 'Z00.0'
                    category = exam_data.get('doctor_category', 'А')
                    conclusion = exam_data.get('conclusion', '')
                    anamnesis = exam_data.get('anamnesis', '')

                    # Формируем текст диагноза
                    if anamnesis and conclusion:
                        diagnosis_full = f"АНАМНЕЗ:\n{anamnesis}\n\nЗАКЛЮЧЕНИЕ:\n{conclusion}"
                    else:
                        diagnosis_full = conclusion or anamnesis or ''

                    # Создаем запись врача
                    new_exam_id = uuid.uuid4()
                    insert_exam = text("""
                        INSERT INTO specialists_examinations
                        (id, conscript_draft_id, specialty, specialty_ru, diagnosis_text, icd10_code,
                         doctor_category, doctor_name, conclusion_text,
                         complaints, anamnesis, objective_data, special_research_results,
                         examination_date, created_at, updated_at)
                        VALUES
                        (:id, :draft_id, :specialty, :specialty_ru, :diagnosis_text, :icd10_code,
                         :doctor_category, :doctor_name, :conclusion_text,
                         :complaints, :anamnesis, :objective_data, :special_research_results,
                         :examination_date, :created_at, :updated_at)
                        RETURNING id
                    """)

                    now = datetime.now()
                    exam_result = await session.execute(
                        insert_exam,
                        {
                            'id': new_exam_id,
                            'draft_id': draft_id,
                            'specialty': specialty,
                            'specialty_ru': specialty_ru,
                            'diagnosis_text': diagnosis_full or 'Без диагноза',
                            'icd10_code': icd10_code,
                            'doctor_category': category,
                            'doctor_name': doctor_name,
                            'conclusion_text': conclusion or diagnosis_full or 'Без заключения',
                            'complaints': exam_data.get('complaints', ''),
                            'anamnesis': anamnesis,
                            'objective_data': exam_data.get('objective_data', conclusion),
                            'special_research_results': exam_data.get('special_research_results', ''),
                            'examination_date': now.date(),
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    exam_row = exam_result.fetchone()
                    examinations_added += 1
                    created_examinations += 1

                    # Показываем ошибку если есть
                    if exam_data.get('is_error'):
                        error_desc = exam_data.get('error_description', 'Ошибка')
                        print(f"   ❌ {specialty_ru}: категория {category} (ОШИБКА: {error_desc})")
                    else:
                        print(f"   ✅ {specialty_ru}: категория {category}")

                await session.flush()
                print(f"\n📊 Для полного случая #{case_id} добавлено {examinations_added} записей врачей (все 9 специалистов)")

            # Коммитим все изменения
            await session.commit()

            print(f"\n{'='*80}")
            print("✅ ВСЕ ДАННЫЕ УСПЕШНО ЗАГРУЖЕНЫ В БАЗУ ДАННЫХ")
            print(f"{'='*80}")
            print(f"\n📊 Статистика:")
            print(f"   - Создано призывников: {created_conscripts}")
            print(f"   - Создано призывных кампаний: {created_drafts}")
            print(f"   - Создано записей врачей: {created_examinations}")
            print(f"\n💡 Данные теперь доступны во фронтенде!")
            print(f"   Перезагрузите страницу, чтобы увидеть новых призывников")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("🚀 Запуск загрузки заключений врачей из JSON файла...")
    print("📁 Загружаются все секции:")
    print("   - test_cases (основные случаи)")
    print("   - contradiction_test_cases (случаи с противоречиями)")
    print("   - missing_specialists_test_cases (дополнительные специалисты)")
    print("   - complete_examination_cases (ПОЛНЫЕ обследования - все 9 специалистов)")
    print("")
    asyncio.run(load_doctor_conclusions())
