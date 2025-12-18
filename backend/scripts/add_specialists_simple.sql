-- Добавление недостающих осмотров специалистов

-- Сначала получим список призывников и их последних призывов
DO $$
DECLARE
    conscript_rec RECORD;
    draft_rec RECORD;
    missing_specialty TEXT;
    examination_date TIMESTAMP;
BEGIN
    -- Для каждого призывника
    FOR conscript_rec IN
        SELECT id, CONCAT(last_name, ' ', first_name, ' ', COALESCE(middle_name, '')) as full_name
        FROM conscripts
    LOOP
        -- Получаем последний призыв
        SELECT id, draft_date INTO draft_rec
        FROM conscript_drafts
        WHERE conscript_id = conscript_rec.id
        ORDER BY draft_date DESC
        LIMIT 1;

        IF draft_rec.id IS NOT NULL THEN
            RAISE NOTICE 'Обработка призывника: % (ID: %)', conscript_rec.full_name, conscript_rec.id;

            examination_date := draft_rec.draft_date;

            -- Добавляем Фтизиатра если нет
            IF NOT EXISTS (
                SELECT 1 FROM specialists_examinations
                WHERE conscript_id = conscript_rec.id
                AND draft_id = draft_rec.id
                AND specialty = 'Фтизиатр'
            ) THEN
                INSERT INTO specialists_examinations
                (conscript_id, draft_id, specialty, diagnosis_text, icd10_code, article, category, examination_date, doctor_name)
                VALUES
                (conscript_rec.id, draft_rec.id, 'Фтизиатр', 'Здоров', NULL, NULL, 'А', examination_date, 'Врач-фтизиатр');
                RAISE NOTICE '  + Добавлен осмотр: Фтизиатр';
            END IF;

            -- Добавляем Психиатра если нет
            IF NOT EXISTS (
                SELECT 1 FROM specialists_examinations
                WHERE conscript_id = conscript_rec.id
                AND draft_id = draft_rec.id
                AND specialty = 'Психиатр'
            ) THEN
                INSERT INTO specialists_examinations
                (conscript_id, draft_id, specialty, diagnosis_text, icd10_code, article, category, examination_date, doctor_name)
                VALUES
                (conscript_rec.id, draft_rec.id, 'Психиатр', 'Здоров', NULL, NULL, 'А', examination_date, 'Врач-психиатр');
                RAISE NOTICE '  + Добавлен осмотр: Психиатр';
            END IF;

            -- Добавляем Стоматолога если нет
            IF NOT EXISTS (
                SELECT 1 FROM specialists_examinations
                WHERE conscript_id = conscript_rec.id
                AND draft_id = draft_rec.id
                AND specialty = 'Стоматолог'
            ) THEN
                INSERT INTO specialists_examinations
                (conscript_id, draft_id, specialty, diagnosis_text, icd10_code, article, category, examination_date, doctor_name)
                VALUES
                (conscript_rec.id, draft_rec.id, 'Стоматолог', 'Здоров', NULL, NULL, 'А', examination_date, 'Врач-стоматолог');
                RAISE NOTICE '  + Добавлен осмотр: Стоматолог';
            END IF;

            -- Добавляем Дерматолога если нет
            IF NOT EXISTS (
                SELECT 1 FROM specialists_examinations
                WHERE conscript_id = conscript_rec.id
                AND draft_id = draft_rec.id
                AND specialty = 'Дерматолог'
            ) THEN
                INSERT INTO specialists_examinations
                (conscript_id, draft_id, specialty, diagnosis_text, icd10_code, article, category, examination_date, doctor_name)
                VALUES
                (conscript_rec.id, draft_rec.id, 'Дерматолог', 'Здоров', NULL, NULL, 'А', examination_date, 'Врач-дерматолог');
                RAISE NOTICE '  + Добавлен осмотр: Дерматолог';
            END IF;

            -- Добавляем Отоларинголога если нет
            IF NOT EXISTS (
                SELECT 1 FROM specialists_examinations
                WHERE conscript_id = conscript_rec.id
                AND draft_id = draft_rec.id
                AND specialty = 'Отоларинголог'
            ) THEN
                INSERT INTO specialists_examinations
                (conscript_id, draft_id, specialty, diagnosis_text, icd10_code, article, category, examination_date, doctor_name)
                VALUES
                (conscript_rec.id, draft_rec.id, 'Отоларинголог', 'Здоров', NULL, NULL, 'А', examination_date, 'Врач-отоларинголог');
                RAISE NOTICE '  + Добавлен осмотр: Отоларинголог';
            END IF;
        END IF;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '✅ Готово!';
END $$;

-- Проверяем результат
SELECT specialty, COUNT(*) as count
FROM specialists_examinations
GROUP BY specialty
ORDER BY specialty;
