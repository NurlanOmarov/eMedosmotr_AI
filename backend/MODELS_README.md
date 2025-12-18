# SQLAlchemy Модели eMedosmotr AI

## Обзор

Все SQLAlchemy модели созданы на основе схемы из `DATABASE_DESIGN.md` с поддержкой **трёхэтапной валидации**.

### Структура файлов

```
backend/app/models/
├── __init__.py           # Экспорт всех моделей
├── conscript.py          # 3 модели - данные призывников
├── medical.py            # 6 моделей - медицинские данные
├── reference.py          # 6 моделей - справочники
├── ai.py                 # 7 моделей - AI и RAG
├── contradiction.py      # 1 модель - логи противоречий (Этап 0)
└── system.py             # 2 модели - системные таблицы
```

**Итого: 25 моделей SQLAlchemy**

### Трёхэтапная валидация

```
[ЭТАП 0] ContradictionLog → 6 типов противоречий (A-F)
[ЭТАП 1] PointCriterion → Клинические критерии (Приложение 2)
[ЭТАП 2] PointDiagnosis → Категории годности (Приложение 1)
```

---

## 1. Модели призывников (conscript.py)

### Conscript
**Таблица:** `conscripts`

Главная таблица с базовой информацией о призывниках.

```python
from app.models import Conscript

# Создание нового призывника
conscript = Conscript(
    iin="123456789012",
    full_name="Иванов Иван Иванович",
    first_name="Иван",
    last_name="Иванов",
    middle_name="Иванович",
    date_of_birth=date(2005, 3, 15),
    gender="M",
    phone="+77012345678",
    email="ivanov@example.com"
)
```

**Поля:**
- `id` (UUID) - Primary Key
- `iin` (String) - ИИН, уникальный, обязательный
- `full_name` (String) - ФИО полностью
- `date_of_birth` (Date) - Дата рождения
- `gender` (String) - Пол (M/F)
- Timestamps: `created_at`, `updated_at`

**Relationships:**
- `drafts` - список призывных кампаний
- `erdb_diagnoses` - амбулаторные обращения
- `bureau_hospitalizations` - визиты в бюро госпитализации
- `ersb_history` - стационарные госпитализации
- `special_statuses` - специальные учёты

---

### ConscriptDraft
**Таблица:** `conscript_drafts`

Связь призывника с конкретной призывной кампанией.

```python
from app.models import ConscriptDraft

draft = ConscriptDraft(
    conscript_id=conscript.id,
    draft_name="Осенний призыв 2025",
    draft_season="autumn",
    draft_year=2025,
    category_graph_id=1,  # График 1 - обычные призывники
    status="pending"
)
```

**Важные поля:**
- `category_graph_id` - График (1-4), определяет категорию годности
- `final_category` - Финальная категория после ВВК
- `status` - Статус (pending, in_progress, completed)

---

### AnthropometricData
**Таблица:** `anthropometric_data`

Физические измерения призывника.

```python
from app.models import AnthropometricData

anthropo = AnthropometricData(
    conscript_draft_id=draft.id,
    height=175.5,
    weight=68.2,
    bmi=22.15,
    visual_acuity_left="1.0",
    visual_acuity_right="1.0",
    blood_pressure_systolic=120,
    blood_pressure_diastolic=80
)
```

---

## 2. Медицинские модели (medical.py)

### SpecialistExamination
**Таблица:** `specialists_examinations`

Заключения врачей ВВК.

```python
from app.models import SpecialistExamination

examination = SpecialistExamination(
    conscript_draft_id=draft.id,
    specialty="therapist",
    specialty_ru="Терапевт",
    doctor_name="Петров П.П.",
    conclusion_text="Здоров. Жалоб нет.",
    icd10_code="Z00.0",
    doctor_category="А",
    examination_date=date.today()
)
```

**Векторное поле:**
- `conclusion_embedding` (Vector(1536)) - для RAG поиска

**Индексы:**
- Векторный индекс `idx_examinations_embedding` (ivfflat)

---

### ErdbDiagnosisHistory
**Таблица:** `erdb_diagnoses_history`

История диспансерного наблюдения (ЭРДБ).

```python
from app.models import ErdbDiagnosisHistory

erdb = ErdbDiagnosisHistory(
    conscript_id=conscript.id,
    icd10_code="K29.3",
    diagnosis_name_ru="Хронический гастрит",
    begin_date=date(2023, 1, 15),
    d_accounting_group="Д-2",
    medical_facility="Поликлиника №5"
)
```

---

### InstrumentalExamResult
**Таблица:** `instrumental_exam_results`

Результаты инструментальных исследований (ЭКГ, УЗИ, рентген).

```python
from app.models import InstrumentalExamResult

exam_result = InstrumentalExamResult(
    conscript_draft_id=draft.id,
    exam_type="ЭКГ",
    objective_data="Ритм синусовый, 72 уд/мин",
    conclusion_text="Патологии не выявлено",
    exam_date=date.today()
)
```

**Векторное поле:**
- `result_embedding` (Vector(1536))

---

## 3. Справочники (reference.py)

### ICD10Code
**Таблица:** `icd10_codes`

Справочник МКБ-10.

```python
from app.models import ICD10Code

icd10 = ICD10Code(
    code="K29.3",
    name_ru="Хронический поверхностный гастрит",
    level=3,
    parent_code="K29"
)
```

**Векторное поле:**
- `name_embedding` (Vector(1536)) - для семантического поиска болезней

---

### PointDiagnosis
**Таблица:** `points_diagnoses`

Приказ 722 - таблица категорий.

```python
from app.models import PointDiagnosis

point = PointDiagnosis(
    chapter="Глава5.Болезни органов пищеварения",
    article=58,
    subpoint="1",
    diagnoses_codes="K29, K30",
    graph_1="Г",  # Призывники - временно не годен
    graph_2="Б",  # Курсанты
    graph_3="А",  # Офицеры
    graph_4="В"   # Спецназ
)
```

**КРИТИЧНО:** Разные графы (1-4) имеют разные категории для одного диагноза!

---

### PointCriterion
**Таблица:** `point_criteria`

Критерии подпунктов (Приложение 2 Приказа 722).

```python
from app.models import PointCriterion

criterion = PointCriterion(
    article=58,
    subpoint="1",
    criteria_text="Со значительным нарушением функции пищеварения",
    criteria_details="Частые обострения (3-4 раза в год)"
)
```

**Векторное поле:**
- `criteria_embedding` (Vector(1536)) - для RAG поиска критериев

---

### CategoryDictionary
**Таблица:** `category_dictionary`

Словарь категорий годности.

```python
from app.models import CategoryDictionary

# Предзаполненные данные:
# А - Годен
# Б - Годен с незначительными ограничениями
# В - Ограниченно годен
# Г - Временно не годен
# Д - Не годен в мирное время
# Е - Не годен с исключением с воинского учета
# НГ - Не годен к службе в определенных войсках
```

---

## 4. AI и RAG модели (ai.py)

### AIAnalysisResult
**Таблица:** `ai_analysis_results`

Результаты AI-анализа заключения врача.

```python
from app.models import AIAnalysisResult

ai_result = AIAnalysisResult(
    conscript_draft_id=draft.id,
    examination_id=examination.id,
    specialty="therapist",
    doctor_category="А",
    ai_recommended_category="Г",
    status="MISMATCH",  # OK или MISMATCH
    risk_level="MEDIUM",
    article=58,
    subpoint="1",
    reasoning="AI считает, что частые обострения гастрита требуют категории Г",
    confidence=0.85,
    model_used="gpt-4",
    tokens_used=1500
)
```

**Векторное поле:**
- `reasoning_embedding` (Vector(1536))

---

### AIFinalVerdict
**Таблица:** `ai_final_verdicts`

Финальный вердикт AI по призывнику.

```python
from app.models import AIFinalVerdict

verdict = AIFinalVerdict(
    conscript_draft_id=draft.id,
    recommended_category="Г",
    status="MISMATCH",
    risk_level="HIGH",
    summary="Несоответствие в 2 из 5 заключений",
    total_specialists=5,
    mismatch_count=2
)
```

---

### KnowledgeBaseDocument
**Таблица:** `knowledge_base_documents`

База знаний для RAG (Приказ 722, медицинские руководства).

```python
from app.models import KnowledgeBaseDocument

doc = KnowledgeBaseDocument(
    document_type="order_722",
    title="Приказ 722, Статья 58, Подпункт 1",
    content="Полный текст критериев...",
    source="Приказ №722 МО РК",
    section="Глава 5",
    article=58
)
```

**Векторное поле:**
- `content_embedding` (Vector(1536))

---

### KnowledgeBaseChunk
**Таблица:** `knowledge_base_chunks`

Чанки документов для более точного RAG поиска.

```python
from app.models import KnowledgeBaseChunk

chunk = KnowledgeBaseChunk(
    document_id=doc.id,
    chunk_text="Со значительным нарушением функции...",
    chunk_order=1,
    chunk_metadata={"article": 58, "subpoint": "1"}
)
```

**Векторное поле:**
- `chunk_embedding` (Vector(1536))

---

### AIPrompt
**Таблица:** `ai_prompts`

Версионирование промптов для AI.

```python
from app.models import AIPrompt

prompt = AIPrompt(
    prompt_name="subpoint_determination_v2",
    prompt_text="Ты - эксперт военно-врачебной комиссии...",
    version=2,
    model_type="gpt-4",
    temperature=0.2,
    max_tokens=2000,
    is_active=True
)
```

---

## 5. Модель противоречий (contradiction.py)

### ContradictionLog
**Таблица:** `contradiction_logs`

Логи противоречий, выявленных на Этапе 0 валидации.

```python
from app.models import ContradictionLog

contradiction = ContradictionLog(
    examination_id=examination.id,
    conscript_draft_id=draft.id,
    contradiction_type="A",  # A-F
    diagnosis_field="Здоров",
    additional_field="Хронический гастрит K29.3 в ЭРДБ",
    additional_field_source="erdb",
    found_diseases=[{
        "icd10_code": "K29.3",
        "disease_name": "Хронический поверхностный гастрит",
        "source_field": "erdb_diagnoses",
        "similarity_score": 0.95
    }],
    doctor_category="А",
    expected_category="Б",
    severity="HIGH",
    recommendation="Требуется проверка: врач указал 'Здоров', но в ЭРДБ есть диагноз K29.3"
)
```

**Типы противоречий:**

| Тип | Описание | Пример |
|-----|----------|--------|
| **A** | "Здоров" в диагнозе + болезнь в доп. полях | Диагноз "Здоров", но в ЭРДБ есть K29.3 |
| **B** | Болезнь в диагнозе + "здоров" в доп. полях | Диагноз K29.3, но в анамнезе "жалоб нет" |
| **C** | Болезнь A в диагнозе + Болезнь B в доп. полях | Диагноз K29.3, но в ЭРСБ была госпитализация с J45.0 |
| **D** | Диагноз vs неправильная категория | Диагноз K29.3 подпункт 2 = Б, а врач поставил А |
| **E** | Логическая ошибка | "Здоров" + категория ≠ "А" |
| **F** | Тяжёлое заболевание + категория "А" | Диагноз J45.0 (астма) + категория А |

**Поля:**
- `id` (UUID) - Primary Key
- `examination_id` (UUID) - Ссылка на заключение врача
- `conscript_draft_id` (UUID) - Ссылка на призывную кампанию
- `contradiction_type` (CHAR) - Тип противоречия (A-F)
- `diagnosis_field` (TEXT) - Содержимое основного диагноза
- `additional_field` (TEXT) - Содержимое дополнительного поля
- `additional_field_source` (VARCHAR) - Источник: anamnesis, erdb, ersb, observations
- `found_diseases` (JSONB) - Найденные заболевания через RAG
- `doctor_category` (VARCHAR) - Категория врача
- `expected_category` (VARCHAR) - Ожидаемая категория
- `severity` (VARCHAR) - Серьёзность: LOW, MEDIUM, HIGH, CRITICAL
- `recommendation` (TEXT) - Рекомендация для председателя
- `detected_by` (VARCHAR) - Кем обнаружено: AI, RULE, MANUAL
- `created_at` (TIMESTAMP) - Дата создания

---

## 6. Системные модели (system.py)

### AIRequestLog
**Таблица:** `ai_request_logs`

Логирование всех AI-запросов.

```python
from app.models import AIRequestLog

log = AIRequestLog(
    conscript_draft_id=draft.id,
    request_type="analysis",
    model_used="gpt-4",
    tokens_prompt=800,
    tokens_completion=500,
    tokens_total=1300,
    cost_usd=0.026,
    duration_seconds=2.5,
    status="success"
)
```

---

### SystemSetting
**Таблица:** `system_settings`

Настройки системы.

```python
from app.models import SystemSetting

setting = SystemSetting(
    setting_key="ai_model",
    setting_value="gpt-4",
    setting_type="string",
    description="Модель AI для анализа"
)
```

---

## Векторный поиск (RAG)

### Пример: Поиск похожих критериев

```python
from sqlalchemy import select
from app.models import PointCriterion

# Получаем embedding заключения врача
query_embedding = get_embedding("Частые обострения гастрита")

# Векторный поиск
stmt = (
    select(PointCriterion)
    .where(PointCriterion.article == 58)
    .order_by(PointCriterion.criteria_embedding.cosine_distance(query_embedding))
    .limit(5)
)

results = session.execute(stmt).scalars().all()
```

### Пример: Поиск похожих случаев

```python
from app.models import SpecialistExamination

# Поиск похожих заключений
stmt = (
    select(SpecialistExamination)
    .where(SpecialistExamination.specialty == "therapist")
    .order_by(SpecialistExamination.conclusion_embedding.cosine_distance(query_embedding))
    .limit(10)
)

similar_cases = session.execute(stmt).scalars().all()
```

---

## Использование в API

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models import Conscript, ConscriptDraft

router = APIRouter()

@router.get("/conscripts/{iin}")
async def get_conscript(iin: str, db: Session = Depends(get_db)):
    conscript = db.query(Conscript).filter(Conscript.iin == iin).first()
    if not conscript:
        raise HTTPException(status_code=404, detail="Призывник не найден")
    return conscript
```

---

## Создание таблиц в БД

```python
from app.utils.database import Base, engine

# Создать все таблицы
Base.metadata.create_all(bind=engine)
```

Или использовать Alembic миграции (рекомендуется):

```bash
alembic revision --autogenerate -m "Initial models"
alembic upgrade head
```

---

## Важные особенности

### 1. Векторные поля требуют pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Векторные индексы создаются автоматически

Все модели с векторными полями имеют ivfflat индексы для быстрого поиска.

### 3. Каскадное удаление

При удалении призывника удаляются все связанные записи:
- Призывные кампании
- Заключения врачей
- AI-анализы
- И т.д.

### 4. Графы Приказа 722

**КРИТИЧЕСКИ ВАЖНО:** При определении категории годности нужно использовать правильный график:
- График 1 - обычные призывники
- График 2 - курсанты военных училищ
- График 3 - офицеры по контракту
- График 4 - спецназ, ВДВ

```python
# Получить категорию для конкретного графа
stmt = select(PointDiagnosis).where(
    PointDiagnosis.article == 58,
    PointDiagnosis.subpoint == "1"
)
point = session.execute(stmt).scalar_one()

graph_number = 1  # Обычный призывник
category = getattr(point, f"graph_{graph_number}")  # "Г"
```

---

## Технические требования

- **Python:** 3.10+
- **SQLAlchemy:** 2.0+
- **PostgreSQL:** 14+ с расширением pgvector
- **pgvector:** для векторных операций

### Установка зависимостей

```bash
pip install sqlalchemy[asyncio] psycopg2-binary pgvector
```

---

## Дополнительная информация

Для подробной информации о схеме базы данных см. `/Users/nurlan/Documents/projects/eMedosmotr_AI/DATABASE_DESIGN.md`
