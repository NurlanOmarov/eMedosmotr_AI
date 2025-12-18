-- Скрипт для автоматического обновления статусов призывных кампаний
-- на основе количества пройденных осмотров

DO $$
DECLARE
    draft_rec RECORD;
    exams_count INT;
    required_exams INT := 9; -- Всего нужно 9 специалистов
BEGIN
    RAISE NOTICE '🔄 Обновление статусов призывных кампаний...';
    RAISE NOTICE '';

    -- Для каждой призывной кампании
    FOR draft_rec IN
        SELECT
            cd.id,
            cd.conscript_id,
            cd.status as current_status,
            CONCAT(c.last_name, ' ', c.first_name) as conscript_name
        FROM conscript_drafts cd
        JOIN conscripts c ON c.id = cd.conscript_id
    LOOP
        -- Подсчитываем количество осмотров
        SELECT COUNT(*) INTO exams_count
        FROM specialists_examinations
        WHERE draft_id = draft_rec.id;

        -- Определяем новый статус
        IF exams_count >= required_exams THEN
            -- Все осмотры завершены
            IF draft_rec.current_status != 'completed' THEN
                UPDATE conscript_drafts
                SET status = 'completed'
                WHERE id = draft_rec.id;

                RAISE NOTICE '✅ % (ID: %): % осмотров → completed',
                    draft_rec.conscript_name,
                    draft_rec.conscript_id,
                    exams_count;
            END IF;
        ELSIF exams_count > 0 THEN
            -- Осмотры в процессе
            IF draft_rec.current_status != 'in_progress' THEN
                UPDATE conscript_drafts
                SET status = 'in_progress'
                WHERE id = draft_rec.id;

                RAISE NOTICE '⏳ % (ID: %): % осмотров → in_progress',
                    draft_rec.conscript_name,
                    draft_rec.conscript_id,
                    exams_count;
            END IF;
        ELSE
            -- Осмотры не начаты
            IF draft_rec.current_status != 'pending' THEN
                UPDATE conscript_drafts
                SET status = 'pending'
                WHERE id = draft_rec.id;

                RAISE NOTICE '⏸️ % (ID: %): 0 осмотров → pending',
                    draft_rec.conscript_name,
                    draft_rec.conscript_id;
            END IF;
        END IF;
    END LOOP;

    RAISE NOTICE '';
    RAISE NOTICE '✅ Статусы обновлены!';
END $$;

-- Показываем результат
SELECT
    cd.status,
    COUNT(*) as count,
    STRING_AGG(CONCAT(c.last_name, ' ', c.first_name), ', ') as conscripts
FROM conscript_drafts cd
JOIN conscripts c ON c.id = cd.conscript_id
GROUP BY cd.status
ORDER BY
    CASE cd.status
        WHEN 'pending' THEN 1
        WHEN 'in_progress' THEN 2
        WHEN 'completed' THEN 3
    END;
