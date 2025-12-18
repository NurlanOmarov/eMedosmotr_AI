-- ========================================
-- ИСПРАВЛЕНИЕ СТАТЬИ 11 - Болезни крови
-- ========================================
--
-- ПРОБЛЕМА: В БД есть подпункт 2, которого НЕТ в Приложении 2
-- РЕШЕНИЕ: Удалить подпункт 2
--
-- СПЕЦИАЛЬНАЯ НУМЕРАЦИЯ в Приказе: подпункты 1, 3, 4 (без подпункта 2)
--

-- Показываем что будет удалено
SELECT 'БУДЕТ УДАЛЕНО:' as action;
SELECT article, subpoint, description, graph_1, graph_2, graph_3, graph_4
FROM point_criteria
WHERE article = 11 AND subpoint = '2';

-- Удаляем подпункт 2
DELETE FROM point_criteria WHERE article = 11 AND subpoint = '2';

-- Проверяем результат
SELECT 'ТЕКУЩАЯ СТРУКТУРА ПОСЛЕ УДАЛЕНИЯ:' as result;
SELECT
    subpoint,
    COUNT(*) as criteria_count,
    string_agg(DISTINCT graph_1 || ',' || graph_2 || ',' || graph_3 || ',' || graph_4, '; ') as categories
FROM point_criteria
WHERE article = 11
GROUP BY subpoint
ORDER BY subpoint::int;

-- Показываем все критерии
SELECT 'ВСЕ КРИТЕРИИ СТАТЬИ 11:' as details;
SELECT subpoint, description, graph_1, graph_2, graph_3, graph_4
FROM point_criteria
WHERE article = 11
ORDER BY subpoint::int, description;
