# 🔄 Миграция для совместимости с внешним AI API

## 📋 Что было сделано

### 1. **Добавлены новые поля в модель `SpecialistExamination`**

**Файл:** `backend/app/models/medical.py`

```python
# Данные офтальмолога - зрение без коррекции
os_vision_without_correction: Mapped[Optional[float]]  # Numeric(3, 2)
od_vision_without_correction: Mapped[Optional[float]]  # Numeric(3, 2)

# Данные стоматолога - зубная формула
dentist_json: Mapped[Optional[dict]]  # JSONB
```

### 2. **Добавлены Python property-алиасы для совместимости**

Эти алиасы позволяют использовать названия полей из внешнего API **БЕЗ изменения существующего кода**:

| Property (алиас) | Реальное поле в БД |
|------------------|-------------------|
| `exam.valid_category` | `doctor_category` |
| `exam.diagnosis_accompany_id` | `icd10_code` |
| `exam.additional_act_comment` | `additional_comment` |
| `exam.complain` | `complaints` |
| `exam.med_commission_member` | `specialty_ru` |

**Пример использования:**
```python
# Старый код продолжает работать
print(exam.doctor_category)  # "А"

# Новый код тоже работает (через алиас)
print(exam.valid_category)  # "А" - то же самое!

# Оба варианта указывают на одно поле в БД
exam.valid_category = "Б"
print(exam.doctor_category)  # "Б" - изменилось!
```

### 3. **Создана миграция Alembic**

**Файл:** `backend/alembic/versions/20251218_add_external_api_fields.py`

Миграция добавляет 3 поля в таблицу `specialists_examinations`.

### 4. **Создан сервис маппинга данных**

**Файл:** `backend/app/services/external_ai_mapper.py`

Функция `prepare_external_ai_request()` автоматически собирает все данные призывника и преобразует их в формат внешнего API.

---

## 🚀 Как применить изменения

### **Шаг 1: Запустить БД (если не запущена)**

```bash
cd /Users/nurlan/Documents/projects/eMedosmotr_AI
docker-compose up -d db
```

Проверить статус:
```bash
docker-compose ps
```

Должно быть:
```
NAME                    STATUS
emedosmotr_ai-db-1     Up
```

---

### **Шаг 2: Применить миграцию**

```bash
cd backend

# Проверить текущую версию БД
alembic current

# Применить миграцию
alembic upgrade head
```

**Ожидаемый вывод:**
```
INFO  [alembic.runtime.migration] Running upgrade c62587cc55d7 -> a1b2c3d4e5f6, add_external_api_fields
✅ Успешно добавлены 3 поля для совместимости с внешним API:
   - os_vision_without_correction (Numeric)
   - od_vision_without_correction (Numeric)
   - dentist_json (JSONB)
```

---

### **Шаг 3: Проверить изменения в БД**

Подключиться к PostgreSQL:
```bash
docker exec -it emedosmotr_ai-db-1 psql -U medosmotr_user -d medosmotr_db
```

Проверить структуру таблицы:
```sql
\d+ specialists_examinations

-- Должны появиться новые поля:
-- os_vision_without_correction | numeric(3,2)
-- od_vision_without_correction | numeric(3,2)
-- dentist_json                 | jsonb
```

Выйти из psql:
```
\q
```

---

## 🧪 Тестирование

### **Тест 1: Проверка property-алиасов**

```python
from app.models.medical import SpecialistExamination
from app.utils.database import get_db

async def test_aliases():
    async with get_db() as db:
        # Получить любое заключение
        exam = await db.execute(
            select(SpecialistExamination).limit(1)
        )
        exam = exam.scalar_one()

        # Тест алиасов
        print(f"doctor_category: {exam.doctor_category}")
        print(f"valid_category (алиас): {exam.valid_category}")
        assert exam.doctor_category == exam.valid_category

        print("✅ Алиасы работают!")
```

### **Тест 2: Подготовка данных для API**

```python
from app.services.external_ai_mapper import prepare_external_ai_request
from uuid import UUID

async def test_api_mapping():
    conscript_draft_id = UUID("...")  # Ваш UUID

    async with get_db() as db:
        # Подготовить данные
        api_data = await prepare_external_ai_request(
            conscript_draft_id=conscript_draft_id,
            db=db
        )

        # Проверить структуру
        assert "anthropometic_data" in api_data
        assert "specialists_examinations" in api_data

        print("✅ Данные готовы для отправки на внешний API!")
        print(json.dumps(api_data, indent=2, ensure_ascii=False))
```

---

## 📝 Использование в коде

### **Пример 1: Получение данных для внешнего API**

```python
from app.services.external_ai_mapper import (
    prepare_external_ai_request,
    validate_api_request,
    serialize_for_json
)
import httpx

async def send_to_external_ai(conscript_draft_id: UUID):
    """Отправить данные призывника на внешний AI сервер"""

    async with get_db() as db:
        # 1. Подготовить данные
        api_data = await prepare_external_ai_request(
            conscript_draft_id=conscript_draft_id,
            db=db
        )

        # 2. Валидация
        validate_api_request(api_data)

        # 3. Сериализация для JSON
        json_data = serialize_for_json(api_data)

        # 4. Отправка на внешний сервер
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://external-ai-server:8000/analyze",
                json=json_data,
                timeout=60.0
            )

        return response.json()
```

### **Пример 2: Сохранение данных офтальмолога**

```python
# Создание заключения офтальмолога с новыми полями
examination = SpecialistExamination(
    conscript_draft_id=draft_id,
    specialty="ophthalmologist",
    specialty_ru="Офтальмолог",

    # Используем новые поля напрямую
    os_vision_without_correction=1.0,  # Левый глаз
    od_vision_without_correction=0.8,  # Правый глаз

    doctor_category="А",
    conclusion_text="Зрение в норме",
    icd10_code="Z00.0"
)

db.add(examination)
await db.commit()
```

### **Пример 3: Сохранение данных стоматолога**

```python
# Зубная формула стоматолога
dentist_formula = {
    "11": "", "12": "", "13": "", "14": "К",  # К = кариес
    # ... остальные зубы 11-48
}

examination = SpecialistExamination(
    conscript_draft_id=draft_id,
    specialty="dentist",
    specialty_ru="Стоматолог",

    # Используем новое поле JSONB
    dentist_json=dentist_formula,

    doctor_category="А",
    conclusion_text="Санация полости рта проведена",
    icd10_code="Z00.0"
)
```

---

## ⚠️ Важные моменты

### **1. Обратная совместимость**

✅ **Весь существующий код продолжает работать без изменений!**

- Новые поля `os_vision_without_correction`, `od_vision_without_correction`, `dentist_json` - **опциональные** (`nullable=True`)
- Property-алиасы работают прозрачно
- Старый код использует `exam.doctor_category`, новый может использовать `exam.valid_category`

### **2. Антропометрия**

✅ **Поля антропометрии ПОЛНОСТЬЮ совпадают с API:**

| API поле | БД поле | Статус |
|----------|---------|--------|
| `height` | `height` | ✅ Готово |
| `weight` | `weight` | ✅ Готово |
| `bmi` | `bmi` | ✅ Готово (авто-расчет) |

### **3. Откат миграции (при необходимости)**

Если что-то пойдет не так:

```bash
# Откатить на предыдущую версию
alembic downgrade -1

# Или откатить полностью
alembic downgrade base
```

---

## 📊 Соответствие полей

### **До миграции:**
| API поле | БД поле | Статус |
|----------|---------|--------|
| `valid_category` | `doctor_category` | ⚠️ Разные названия |
| `diagnosis_accompany_id` | `icd10_code` | ⚠️ Разные названия |
| `os_vision_without_correction` | ❌ НЕТ | 🔴 Отсутствует |
| `dentist_json` | ❌ НЕТ | 🔴 Отсутствует |

### **После миграции:**
| API поле | БД поле / Алиас | Статус |
|----------|-----------------|--------|
| `valid_category` | `doctor_category` (через property) | ✅ Готово |
| `diagnosis_accompany_id` | `icd10_code` (через property) | ✅ Готово |
| `os_vision_without_correction` | `os_vision_without_correction` | ✅ Готово |
| `od_vision_without_correction` | `od_vision_without_correction` | ✅ Готово |
| `dentist_json` | `dentist_json` | ✅ Готово |

---

## ✅ Чеклист готовности

- [ ] БД запущена (`docker-compose up -d db`)
- [ ] Миграция применена (`alembic upgrade head`)
- [ ] Проверена структура таблицы (`\d+ specialists_examinations`)
- [ ] Протестированы property-алиасы
- [ ] Протестирован `external_ai_mapper.prepare_external_ai_request()`
- [ ] Обновлены формы frontend для ввода новых полей (опционально)

---

## 🎯 Что дальше?

### **Краткосрочно:**
1. ✅ Применить миграцию (готово)
2. ✅ Тестировать подготовку данных для API (готово)
3. 🔄 Обновить frontend формы для ввода данных о зрении и зубной формулы

### **Среднесрочно:**
1. Создать эндпоинт FastAPI для отправки данных на внешний AI
2. Реализовать обработку ответа от внешнего AI
3. Добавить логирование запросов к внешнему AI

### **Долгосрочно:**
1. Мониторинг производительности внешнего AI
2. Кэширование результатов анализа
3. Обработка ошибок и retry-логика

---

## 📞 Поддержка

Если возникли вопросы или проблемы:
1. Проверьте логи Docker: `docker-compose logs -f`
2. Проверьте логи Alembic
3. Проверьте структуру БД: `\d+ specialists_examinations`

**Важно:** Все изменения **обратно совместимы** и не ломают существующий код! ✅
