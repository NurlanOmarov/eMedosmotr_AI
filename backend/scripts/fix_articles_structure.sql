-- ========================================
-- ИСПРАВЛЕНИЕ СТРУКТУРЫ СТАТЕЙ
-- ========================================

-- Статья 8: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 8 AND subpoint IN ('3', '4');

-- Статья 11: Специфическая нумерация: 1, 3, 4 (пропущен подпункт 2)

-- Статья 12: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 12 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 12 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 29: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 29 AND subpoint IN ('3', '4');

-- Статья 30: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 30 AND subpoint IN ('3', '4');

-- Статья 31: уменьшение до 1 подпунктов
DELETE FROM point_criteria WHERE article = 31 AND subpoint IN ('2', '3', '4');

-- Статья 33: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 33 AND subpoint IN ('3', '4');

-- Статья 38: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 38 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 38 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 39: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 39 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 39 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 44: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 44 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 44 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 46: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 46 AND subpoint IN ('3', '4');

-- Статья 48: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 48 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 48 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 49: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 49 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 49 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 50: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 50 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 50 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 54: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 54 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 54 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 57: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 57 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 57 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 60: В Приложении 2 упоминается только подпункт 1. Требует ручной проверки.

-- Статья 64: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 64 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 64 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 65: уменьшение до 4 подпунктов
DELETE FROM point_criteria WHERE article = 65 AND subpoint = '5';

-- Статья 68: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 68 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 68 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 74: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 74 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 74 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 75: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 75 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 75 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 76: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 76 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 76 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 77: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 77 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 77 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 81: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 81 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 81 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 82: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 82 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 82 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 84: уменьшение до 3 подпунктов
DELETE FROM point_criteria WHERE article = 84 AND subpoint = '4';

UPDATE point_criteria
SET description = 'при наличии объективных данных без нарушения функций'
WHERE article = 84 AND subpoint = '3'
  AND description LIKE '%незначительным нарушением%';


-- Статья 89: уменьшение до 2 подпунктов
DELETE FROM point_criteria WHERE article = 89 AND subpoint IN ('3', '4');

-- ========================================
-- ПРОВЕРКА РЕЗУЛЬТАТОВ
-- ========================================


SELECT
    article,
    COUNT(DISTINCT subpoint) as subpoints_count,
    string_agg(DISTINCT subpoint::text, ', ' ORDER BY subpoint::text) as subpoints
FROM point_criteria
WHERE article IN (8, 11, 12, 29, 30, 31, 33, 38, 39, 44, 46, 48, 49, 50, 54, 57, 59, 60, 64, 65, 68, 74, 75, 76, 77, 81, 82, 84, 89)
GROUP BY article
ORDER BY article;
