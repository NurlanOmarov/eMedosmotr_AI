-- Инициализация базы данных eMedosmotr
-- Создание расширений PostgreSQL

-- pgvector для векторного поиска (RAG)
CREATE EXTENSION IF NOT EXISTS vector;

-- uuid-ossp для генерации UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pg_trgm для полнотекстового поиска
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Создание схемы
CREATE SCHEMA IF NOT EXISTS public;

-- Комментарии
COMMENT ON EXTENSION vector IS 'Векторное расширение для RAG поиска по критериям';
COMMENT ON EXTENSION "uuid-ossp" IS 'Генерация UUID для первичных ключей';
COMMENT ON EXTENSION pg_trgm IS 'Полнотекстовый поиск по медицинским терминам';

-- Вывод информации
DO $$
BEGIN
    RAISE NOTICE '✅ База данных emedosmotr инициализирована';
    RAISE NOTICE '✅ Расширения установлены: vector, uuid-ossp, pg_trgm';
    RAISE NOTICE '📊 База данных готова к созданию таблиц';
END $$;
