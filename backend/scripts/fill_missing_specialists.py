"""
Скрипт для дозаполнения призывников недостающими специалистами
Добавляет заключения от всех 9 врачей для каждого призывника
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, datetime
import uuid

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings

# Все 9 обязательных специалистов
REQUIRED_SPECIALISTS = [
    'Терапевт',
    'Хирург',
    'Офтальмолог',
    'Невролог',
    'Отоларинголог',
    'Дерматолог',
    'Психиатр',
    'Стоматолог',
    'Фтизиатр'
]

# Шаблоны здоровых заключений для каждого специалиста
HEALTHY_TEMPLATES = {
    'Терапевт': {
        'doctor_name': 'Иванов И.И.',
        'conclusion': 'Практически здоров. Общее состояние удовлетворительное. АД 120/75. ЧСС 72 уд/мин. Дыхание везикулярное, хрипов нет. Тоны сердца ясные, ритмичные. Живот мягкий, безболезненный. Патологии не выявлено.',
        'anamnesis': 'Жалоб нет. Хронических заболеваний не имеет. На учете не состоит.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Хирург': {
        'doctor_name': 'Сидоров В.П.',
        'conclusion': 'Хирургической патологии не выявлено. Грыжевых выпячиваний нет. Варикозного расширения вен нет. Стопы без деформации. Позвоночник без искривления.',
        'anamnesis': 'Травм, операций не было. К хирургу ранее не обращался.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Офтальмолог': {
        'doctor_name': 'Петрова А.С.',
        'conclusion': 'Острота зрения: OD 1.0, OS 1.0. Рефракция эмметропическая. Глазное дно без патологии. ВГД в норме. Цветоощущение нормальное.',
        'anamnesis': 'На зрение не жалуется. Очки не носит.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Невролог': {
        'doctor_name': 'Смирнова О.Н.',
        'conclusion': 'Неврологический статус без патологии. Черепные нервы интактны. Сухожильные рефлексы живые, симметричные. Патологических знаков нет. Координация не нарушена.',
        'anamnesis': 'Головных болей, головокружений нет. Судорог не было. На учете не состоит.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Отоларинголог': {
        'doctor_name': 'Жумагулов Б.С.',
        'conclusion': 'ЛОР-органы без патологии. Носовое дыхание свободное. Слизистая носа и глотки розовая. Миндалины не увеличены. Слух: шепотная речь 6 м на оба уха.',
        'anamnesis': 'Жалоб нет. Ангинами болеет редко. Слух хороший.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Дерматолог': {
        'doctor_name': 'Сарсенова М.А.',
        'conclusion': 'Кожные покровы чистые, физиологической окраски. Высыпаний нет. Волосы и ногти без патологии.',
        'anamnesis': 'Кожных заболеваний не было. Аллергии нет.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Психиатр': {
        'doctor_name': 'Тулегенова Г.К.',
        'conclusion': 'Психически здоров. Сознание ясное, ориентирован правильно. Контактен, адекватен. Настроение ровное. Мышление последовательное. Критика сохранена.',
        'anamnesis': 'К психиатру не обращался. На учете в ПНД не состоит.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Стоматолог': {
        'doctor_name': 'Ахметова С.Н.',
        'conclusion': 'Полость рта санирована. Слизистая без патологии. Прикус ортогнатический. Пародонт без воспаления.',
        'anamnesis': 'Зубы не болят. К стоматологу обращается для профосмотров.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    },
    'Фтизиатр': {
        'doctor_name': 'Досымбеков К.А.',
        'conclusion': 'Туберкулез не выявлен. Флюорография: легочные поля прозрачные. Диаскинтест отрицательный.',
        'anamnesis': 'Туберкулезом не болел. Контакта с больными не было. На учете в ПТД не состоит.',
        'icd10_code': 'Z00.0',
        'category': 'А'
    }
}


async def fill_missing_specialists():
    """Дозаполнить всех призывников недостающими специалистами"""

    # Создаем движок БД
    database_url = settings.DATABASE_URL.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    engine = create_async_engine(
        database_url,
        echo=False,
        future=True
    )

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Получаем все призывные кампании
            get_drafts = text("""
                SELECT cd.id as draft_id, c.full_name, c.iin
                FROM conscript_drafts cd
                JOIN conscripts c ON c.id = cd.conscript_id
                ORDER BY c.iin
            """)
            result = await session.execute(get_drafts)
            drafts = result.fetchall()

            print(f"📋 Найдено {len(drafts)} призывных кампаний")

            total_added = 0

            for draft in drafts:
                draft_id = draft.draft_id
                full_name = draft.full_name
                iin = draft.iin

                # Получаем существующих специалистов для этого призывника
                get_existing = text("""
                    SELECT specialty FROM specialists_examinations
                    WHERE conscript_draft_id = :draft_id
                """)
                existing_result = await session.execute(get_existing, {'draft_id': draft_id})
                existing_specialists = {row.specialty for row in existing_result.fetchall()}

                # Находим недостающих специалистов
                missing = [s for s in REQUIRED_SPECIALISTS if s not in existing_specialists]

                if not missing:
                    continue  # Все специалисты уже есть

                print(f"\n{'='*60}")
                print(f"📝 {full_name} (ИИН: {iin})")
                print(f"   Имеется: {len(existing_specialists)}/9 специалистов")
                print(f"   Добавляем: {', '.join(missing)}")

                # Добавляем недостающих специалистов
                for specialty in missing:
                    template = HEALTHY_TEMPLATES.get(specialty)
                    if not template:
                        continue

                    new_exam_id = uuid.uuid4()
                    now = datetime.now()

                    # Формируем текст диагноза
                    anamnesis = template['anamnesis']
                    conclusion = template['conclusion']
                    diagnosis_full = f"АНАМНЕЗ:\n{anamnesis}\n\nЗАКЛЮЧЕНИЕ:\n{conclusion}"

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

                    await session.execute(
                        insert_exam,
                        {
                            'id': new_exam_id,
                            'draft_id': draft_id,
                            'specialty': specialty,
                            'specialty_ru': specialty,
                            'diagnosis_text': diagnosis_full,
                            'icd10_code': template['icd10_code'],
                            'doctor_category': template['category'],
                            'doctor_name': template['doctor_name'],
                            'conclusion_text': conclusion,
                            'complaints': '',
                            'anamnesis': anamnesis,
                            'objective_data': conclusion,
                            'special_research_results': '',
                            'examination_date': now.date(),
                            'created_at': now,
                            'updated_at': now
                        }
                    )
                    total_added += 1
                    print(f"   ✅ {specialty}: категория {template['category']}")

                await session.flush()

            # Коммитим все изменения
            await session.commit()

            print(f"\n{'='*60}")
            print("✅ ДОЗАПОЛНЕНИЕ ЗАВЕРШЕНО")
            print(f"{'='*60}")
            print(f"\n📊 Добавлено записей врачей: {total_added}")
            print(f"\n💡 Теперь все призывники имеют заключения от всех 9 специалистов!")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("🚀 Запуск дозаполнения призывников недостающими специалистами...")
    print("📋 Обязательные специалисты:")
    for i, spec in enumerate(REQUIRED_SPECIALISTS, 1):
        print(f"   {i}. {spec}")
    print("")
    asyncio.run(fill_missing_specialists())
