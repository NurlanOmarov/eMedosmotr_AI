-- Добавление автоматического расчета ИМТ (индекса массы тела)
-- ИМТ = вес (кг) / (рост (м))^2

-- Шаг 1: Добавить колонку bmi в таблицу
ALTER TABLE anthropometric_data
ADD COLUMN IF NOT EXISTS bmi NUMERIC(5,2);

-- Шаг 2: Создать функцию для расчета ИМТ
CREATE OR REPLACE FUNCTION calculate_bmi()
RETURNS TRIGGER AS $$
BEGIN
    -- Рассчитываем ИМТ, если есть рост и вес
    -- Формула: вес(кг) / (рост(см) / 100)^2
    IF NEW.height IS NOT NULL AND NEW.weight IS NOT NULL AND NEW.height > 0 THEN
        NEW.bmi := ROUND(NEW.weight / POWER(NEW.height / 100.0, 2), 2);
    ELSE
        NEW.bmi := NULL;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Шаг 3: Удалить старый триггер, если существует
DROP TRIGGER IF EXISTS trigger_calculate_bmi ON anthropometric_data;

-- Шаг 4: Создать триггер для автоматического расчета ИМТ
CREATE TRIGGER trigger_calculate_bmi
    BEFORE INSERT OR UPDATE OF height, weight
    ON anthropometric_data
    FOR EACH ROW
    EXECUTE FUNCTION calculate_bmi();

-- Шаг 5: Рассчитать ИМТ для существующих записей
UPDATE anthropometric_data
SET bmi = ROUND(weight / POWER(height / 100.0, 2), 2)
WHERE height IS NOT NULL
  AND weight IS NOT NULL
  AND height > 0;

-- Шаг 6: Проверка результатов
SELECT
    c.first_name,
    c.last_name,
    ad.height,
    ad.weight,
    ad.bmi,
    CASE
        WHEN ad.bmi IS NULL THEN 'Нет данных'
        WHEN ad.bmi < 18.5 THEN 'Недостаточный вес'
        WHEN ad.bmi >= 18.5 AND ad.bmi < 25 THEN 'Норма'
        WHEN ad.bmi >= 25 AND ad.bmi < 30 THEN 'Избыточный вес'
        ELSE 'Ожирение'
    END as bmi_category
FROM conscripts c
JOIN anthropometric_data ad ON c.id = ad.conscript_id
ORDER BY c.id;
