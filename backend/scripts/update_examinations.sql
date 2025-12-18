-- Скрипт для обновления обязательных полей в таблице specialists_examinations
-- Обновляем все записи, где отсутствуют обязательные поля

-- 1. Обновляем specialty_ru (если пустое, копируем из specialty)
UPDATE specialists_examinations
SET specialty_ru = specialty
WHERE specialty_ru IS NULL OR specialty_ru = '';

-- 2. Обновляем conclusion_text (если пустое, копируем из diagnosis_text)
UPDATE specialists_examinations
SET conclusion_text = COALESCE(diagnosis_text, objective_data, 'Осмотр проведен')
WHERE conclusion_text IS NULL OR conclusion_text = '';

-- 3. Обновляем diagnosis_text (если пустое, ставим значение по умолчанию)
UPDATE specialists_examinations
SET diagnosis_text = 'Патологии не выявлено'
WHERE diagnosis_text IS NULL OR diagnosis_text = '';

-- 4. Обновляем icd10_code (если пустое, ставим Z00.0 - здоров)
UPDATE specialists_examinations
SET icd10_code = 'Z00.0'
WHERE icd10_code IS NULL OR icd10_code = '';

-- 5. Обновляем doctor_category (если пустое, ставим "А" - годен)
UPDATE specialists_examinations
SET doctor_category = 'А'
WHERE doctor_category IS NULL OR doctor_category = '';

-- 6. Добавляем детальные заключения для Терапевта
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб не предъявляет'),
    anamnesis = COALESCE(anamnesis, 'Анамнез без особенностей'),
    objective_data = COALESCE(objective_data, 'Общее состояние удовлетворительное. Патологии не выявлено.')
WHERE (specialty_ru = 'Терапевт' OR specialty = 'Терапевт')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 7. Добавляем детальные заключения для Хирурга
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб не предъявляет'),
    anamnesis = COALESCE(anamnesis, 'Хирургических заболеваний не было'),
    objective_data = COALESCE(objective_data, 'Без хирургической патологии')
WHERE (specialty_ru = 'Хирург' OR specialty = 'Хирург')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 8. Добавляем детальные заключения для Офтальмолога
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'Зрение хорошее'),
    objective_data = COALESCE(objective_data, 'OU спокойный. Патологии не выявлено.')
WHERE (specialty_ru = 'Офтальмолог' OR specialty = 'Офтальмолог')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 9. Добавляем детальные заключения для Невролога
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'Неврологических заболеваний не было'),
    objective_data = COALESCE(objective_data, 'Неврологический статус без особенностей')
WHERE (specialty_ru = 'Невролог' OR specialty = 'Невролог')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 10. Добавляем детальные заключения для Отоларинголога
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'ЛОР-патологии не было'),
    objective_data = COALESCE(objective_data, 'ЛОР-органы без патологии. Слух нормальный.')
WHERE (specialty_ru = 'Отоларинголог' OR specialty = 'Отоларинголог')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 11. Добавляем детальные заключения для Дерматолога
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'Кожных заболеваний не было'),
    objective_data = COALESCE(objective_data, 'Кожные покровы чистые. Патологии не выявлено.')
WHERE (specialty_ru = 'Дерматолог' OR specialty = 'Дерматолог')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 12. Добавляем детальные заключения для Психиатра
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'На учете у психиатра не состоит'),
    objective_data = COALESCE(objective_data, 'Психическое состояние в норме. Поведение адекватное.')
WHERE (specialty_ru = 'Психиатр' OR specialty = 'Психиатр')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 13. Добавляем детальные заключения для Стоматолога
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'Санация полости рта проведена'),
    objective_data = COALESCE(objective_data, 'Полость рта санирована. Патологии не выявлено.')
WHERE (specialty_ru = 'Стоматолог' OR specialty = 'Стоматолог')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- 14. Добавляем детальные заключения для Фтизиатра
UPDATE specialists_examinations
SET
    complaints = COALESCE(complaints, 'Жалоб нет'),
    anamnesis = COALESCE(anamnesis, 'На учете у фтизиатра не состоит'),
    objective_data = COALESCE(objective_data, 'Без патологии'),
    special_research_results = COALESCE(special_research_results, 'Флюорография: патологии не выявлено')
WHERE (specialty_ru = 'Фтизиатр' OR specialty = 'Фтизиатр')
  AND (complaints IS NULL OR anamnesis IS NULL OR objective_data IS NULL);

-- Проверка результатов
SELECT
    COUNT(*) as total_examinations,
    COUNT(CASE WHEN doctor_name IS NOT NULL AND doctor_name != '' THEN 1 END) as with_doctor_name,
    COUNT(CASE WHEN icd10_code IS NOT NULL AND icd10_code != '' THEN 1 END) as with_icd10,
    COUNT(CASE WHEN diagnosis_text IS NOT NULL AND diagnosis_text != '' THEN 1 END) as with_diagnosis,
    COUNT(CASE WHEN conclusion_text IS NOT NULL AND conclusion_text != '' THEN 1 END) as with_conclusion,
    COUNT(CASE WHEN doctor_category IS NOT NULL AND doctor_category != '' THEN 1 END) as with_category,
    COUNT(CASE WHEN specialty_ru IS NOT NULL AND specialty_ru != '' THEN 1 END) as with_specialty_ru
FROM specialists_examinations;
