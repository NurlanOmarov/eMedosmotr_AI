-- eMedosmotr AI - Initial Schema
-- Создание таблиц для MVP прототипа

-- Включаем расширение pgvector (если еще не включено)
CREATE EXTENSION IF NOT EXISTS vector;

-- ===========================================
-- СПРАВОЧНИКИ (REFERENCE TABLES)
-- ===========================================

-- Классификатор МКБ-10
CREATE TABLE IF NOT EXISTS icd10_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name_ru TEXT NOT NULL,
    name_kk TEXT,
    chapter VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Статьи Приложения 1 (Приказ 722)
CREATE TABLE IF NOT EXISTS points_diagnoses (
    id SERIAL PRIMARY KEY,
    article INTEGER NOT NULL,
    point_name TEXT NOT NULL,
    description TEXT,
    icd10_chapter VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(article, point_name)
);

-- Критерии Приложения 2 (детализация подпунктов)
CREATE TABLE IF NOT EXISTS point_criteria (
    id SERIAL PRIMARY KEY,
    point_diagnosis_id INTEGER REFERENCES points_diagnoses(id) ON DELETE CASCADE,
    article INTEGER NOT NULL,
    subpoint VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    graph_1 VARCHAR(50),
    graph_2 VARCHAR(50),
    graph_3 VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Категории годности
CREATE TABLE IF NOT EXISTS category_dictionary (
    id SERIAL PRIMARY KEY,
    category_code VARCHAR(10) UNIQUE NOT NULL,
    description_ru TEXT NOT NULL,
    description_kk TEXT,
    sort_order INTEGER DEFAULT 0
);

-- Графы категорий (для разных типов призывников)
CREATE TABLE IF NOT EXISTS category_graph (
    id SERIAL PRIMARY KEY,
    graph_number INTEGER NOT NULL,
    description TEXT,
    applicable_to TEXT
);

-- Маппинг глав МКБ-10 на специальности
CREATE TABLE IF NOT EXISTS chapter_specialty_mapping (
    id SERIAL PRIMARY KEY,
    icd10_chapter VARCHAR(10) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE
);

-- ===========================================
-- ПРИЗЫВНИКИ (CONSCRIPTS)
-- ===========================================

-- Основная таблица призывников
CREATE TABLE IF NOT EXISTS conscripts (
    id SERIAL PRIMARY KEY,
    iin VARCHAR(12) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    birth_date DATE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Призывные кампании
CREATE TABLE IF NOT EXISTS conscript_drafts (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    draft_number VARCHAR(50) UNIQUE NOT NULL,
    draft_date DATE NOT NULL,
    graph INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Антропометрические данные
CREATE TABLE IF NOT EXISTS anthropometric_data (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    draft_id INTEGER REFERENCES conscript_drafts(id) ON DELETE CASCADE,
    height NUMERIC(5,2),
    weight NUMERIC(5,2),
    chest_circumference NUMERIC(5,2),
    vision_left NUMERIC(3,2),
    vision_right NUMERIC(3,2),
    blood_pressure VARCHAR(20),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- МЕДИЦИНСКИЕ ЗАКЛЮЧЕНИЯ (MEDICAL)
-- ===========================================

-- Заключения специалистов
CREATE TABLE IF NOT EXISTS specialists_examinations (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    draft_id INTEGER REFERENCES conscript_drafts(id) ON DELETE CASCADE,
    specialty VARCHAR(100) NOT NULL,
    diagnosis_text TEXT,
    icd10_code VARCHAR(10),
    article INTEGER,
    subpoint VARCHAR(10),
    category VARCHAR(50),
    examination_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    doctor_name VARCHAR(200),
    notes TEXT
);

-- История диагнозов из ЭРДБ
CREATE TABLE IF NOT EXISTS erdb_diagnoses_history (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    icd10_code VARCHAR(10) NOT NULL,
    diagnosis_text TEXT,
    diagnosis_date DATE NOT NULL,
    medical_org VARCHAR(200),
    specialty VARCHAR(100),
    source VARCHAR(50) DEFAULT 'ERDB'
);

-- Госпитализации из МБП
CREATE TABLE IF NOT EXISTS bureau_hospitalizations (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    admission_date DATE NOT NULL,
    discharge_date DATE,
    diagnosis TEXT,
    medical_org VARCHAR(200),
    department VARCHAR(100)
);

-- История из ЭРСБ (Единый регистр скорой помощи)
CREATE TABLE IF NOT EXISTS ersb_history (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    call_date TIMESTAMP NOT NULL,
    complaint TEXT,
    diagnosis TEXT,
    provided_care TEXT,
    ambulance_team VARCHAR(100)
);

-- Результаты инструментальных обследований
CREATE TABLE IF NOT EXISTS instrumental_exam_results (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    exam_type VARCHAR(100) NOT NULL,
    exam_date DATE NOT NULL,
    result_text TEXT,
    conclusion TEXT,
    medical_org VARCHAR(200)
);

-- Особые статусы из ЭРДБ (инвалидность, хронические заболевания)
CREATE TABLE IF NOT EXISTS erdb_special_status (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    status_type VARCHAR(50) NOT NULL,
    status_code VARCHAR(20),
    valid_from DATE,
    valid_until DATE,
    issuing_org VARCHAR(200)
);

-- ===========================================
-- AI АНАЛИЗ (AI ANALYSIS)
-- ===========================================

-- Результаты AI-анализа отдельных врачей
CREATE TABLE IF NOT EXISTS ai_analysis_results (
    id SERIAL PRIMARY KEY,
    examination_id INTEGER REFERENCES specialists_examinations(id) ON DELETE CASCADE,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    specialty VARCHAR(100) NOT NULL,

    -- Входные данные
    diagnosis_text TEXT,
    icd10_code VARCHAR(10),
    doctor_category VARCHAR(50),

    -- Результаты AI
    ai_article INTEGER,
    ai_subpoint VARCHAR(10),
    ai_category VARCHAR(50),
    confidence_score NUMERIC(5,2),
    risk_level VARCHAR(20),

    -- Статус сравнения
    match_status VARCHAR(20),
    discrepancy_description TEXT,
    reasoning TEXT,

    -- Метаданные
    model_used VARCHAR(50),
    prompt_version VARCHAR(20),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,

    -- Векторное представление для поиска похожих случаев
    embedding vector(1536)
);

-- Итоговое заключение AI по всему призывнику
CREATE TABLE IF NOT EXISTS ai_final_verdicts (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE CASCADE,
    draft_id INTEGER REFERENCES conscript_drafts(id) ON DELETE CASCADE,

    -- Агрегированные результаты
    overall_risk_level VARCHAR(20),
    total_examinations INTEGER,
    matches_count INTEGER,
    mismatches_count INTEGER,
    requires_review BOOLEAN DEFAULT FALSE,

    -- Итоговая категория
    recommended_category VARCHAR(50),
    confidence_score NUMERIC(5,2),

    -- Обоснование
    summary TEXT,
    key_findings TEXT[],
    recommendations TEXT[],

    -- Метаданные
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(20)
);

-- Обратная связь от председателя/врача
CREATE TABLE IF NOT EXISTS ai_analysis_feedback (
    id SERIAL PRIMARY KEY,
    analysis_result_id INTEGER REFERENCES ai_analysis_results(id) ON DELETE CASCADE,
    verdict_id INTEGER REFERENCES ai_final_verdicts(id) ON DELETE SET NULL,

    user_name VARCHAR(200),
    feedback_type VARCHAR(50),
    is_correct BOOLEAN,
    corrected_category VARCHAR(50),
    comment TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- БАЗА ЗНАНИЙ (KNOWLEDGE BASE)
-- ===========================================

-- Документы базы знаний
CREATE TABLE IF NOT EXISTS knowledge_base_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    document_type VARCHAR(50),
    source_file VARCHAR(500),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Чанки документов для RAG
CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES knowledge_base_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Кэш похожих случаев
CREATE TABLE IF NOT EXISTS similar_cases_cache (
    id SERIAL PRIMARY KEY,
    query_embedding vector(1536) NOT NULL,
    similar_case_ids INTEGER[],
    similarity_scores NUMERIC[],
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    hit_count INTEGER DEFAULT 0
);

-- Промпты AI
CREATE TABLE IF NOT EXISTS ai_prompts (
    id SERIAL PRIMARY KEY,
    prompt_name VARCHAR(100) UNIQUE NOT NULL,
    prompt_text TEXT NOT NULL,
    version VARCHAR(20) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- СИСТЕМНЫЕ ТАБЛИЦЫ (SYSTEM)
-- ===========================================

-- Лог запросов к AI
CREATE TABLE IF NOT EXISTS ai_request_logs (
    id SERIAL PRIMARY KEY,
    conscript_id INTEGER REFERENCES conscripts(id) ON DELETE SET NULL,
    request_type VARCHAR(50) NOT NULL,
    model_used VARCHAR(50),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost NUMERIC(10,6),
    response_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Настройки системы
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===========================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ===========================================

-- Индексы для поиска по IIN
CREATE INDEX IF NOT EXISTS idx_conscripts_iin ON conscripts(iin);

-- Индексы для заключений врачей
CREATE INDEX IF NOT EXISTS idx_specialists_conscript ON specialists_examinations(conscript_id);
CREATE INDEX IF NOT EXISTS idx_specialists_specialty ON specialists_examinations(specialty);

-- Индексы для ЭРДБ
CREATE INDEX IF NOT EXISTS idx_erdb_conscript ON erdb_diagnoses_history(conscript_id);
CREATE INDEX IF NOT EXISTS idx_erdb_icd10 ON erdb_diagnoses_history(icd10_code);

-- Индексы для AI анализа
CREATE INDEX IF NOT EXISTS idx_ai_analysis_conscript ON ai_analysis_results(conscript_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_status ON ai_analysis_results(match_status);

-- Индексы для векторного поиска (pgvector)
CREATE INDEX IF NOT EXISTS idx_ai_analysis_embedding ON ai_analysis_results
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding ON knowledge_base_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ===========================================
-- ВСТАВКА БАЗОВЫХ ДАННЫХ
-- ===========================================

-- Категории годности
INSERT INTO category_dictionary (category_code, description_ru, sort_order) VALUES
('А', 'Годен к военной службе', 1),
('А-ИНД', 'Годен к военной службе с индивидуальными показателями', 2),
('Б', 'Годен к военной службе с незначительными ограничениями', 3),
('Б-1', 'Годен к военной службе с незначительными ограничениями (1)', 4),
('Б-2', 'Годен к военной службе с незначительными ограничениями (2)', 5),
('Б-3', 'Годен к военной службе с незначительными ограничениями (3)', 6),
('В', 'Ограниченно годен к военной службе', 7),
('В-ИНД', 'Ограниченно годен с индивидуальными показателями', 8),
('Г', 'Временно не годен к военной службе', 9),
('Д', 'Не годен к военной службе', 10),
('EXAM', 'Требуется обследование', 11)
ON CONFLICT (category_code) DO NOTHING;

-- Графы
INSERT INTO category_graph (graph_number, description) VALUES
(1, 'Граждане, подлежащие призыву на срочную военную службу'),
(2, 'Военнослужащие, проходящие военную службу по контракту'),
(3, 'Курсанты военных учебных заведений')
ON CONFLICT DO NOTHING;

-- Базовые промпты AI
INSERT INTO ai_prompts (prompt_name, prompt_text, version) VALUES
('determine_subpoint_v1', 'Ты эксперт медицинской комиссии. Определи подпункт статьи Приказа 722...', '1.0'),
('generate_reasoning_v1', 'Проанализируй соответствие категории годности заключению врача...', '1.0'),
('aggregate_results_v1', 'Агрегируй результаты анализа от всех специалистов...', '1.0')
ON CONFLICT (prompt_name) DO NOTHING;

-- Настройки системы
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('ai_model', 'gpt-4o-mini', 'Модель OpenAI для анализа'),
('ai_temperature', '0.2', 'Temperature для AI'),
('rag_top_k', '5', 'Количество результатов в RAG'),
('cache_ttl_hours', '24', 'TTL кэша в часах')
ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value;

-- ✅ Схема БД создана успешно!
