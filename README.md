# eMedosmotr AI - Система медицинского освидетельствования с AI

Интеллектуальная система для определения категорий годности граждан к воинской службе на основе медицинских данных и приказа МЗ РК №722.

## Возможности

- 🤖 **AI-ассистент** для анализа медицинских заключений
- 📋 **Векторный поиск** по МКБ-10 и медицинским справочникам  
- 🔍 **RAG (Retrieval-Augmented Generation)** для точных рекомендаций
- 📊 **Автоматическое определение** категорий годности (А, Б, В, Г, Д, НГ)
- 🎯 **Специализация** по типам призыва (графы 1-4)
- 🏥 **Интеграция** с приказом №722 МЗ РК

## Технологический стек

**Backend:**
- FastAPI (Python 3.11)
- PostgreSQL + pgvector (векторный поиск)
- OpenAI API (GPT-4o-mini)
- SQLAlchemy (ORM)
- Asyncpg (async PostgreSQL driver)

**Frontend:**
- React 18
- Vite
- Axios
- Modern CSS

**DevOps:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- Let's Encrypt (SSL/TLS)

## Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- OpenAI API ключ

### Установка

1. **Клонировать репозиторий:**
```bash
git clone https://github.com/NurlanOmarov/eMedosmotr_AI.git
cd eMedosmotr_AI
```

2. **Настроить переменные окружения:**
```bash
cp .env.example .env
# Отредактировать .env и добавить ваш OPENAI_API_KEY
nano .env
```

3. **Запустить все сервисы:**
```bash
docker-compose up -d
```

4. **Загрузить справочники (первый запуск):**
```bash
curl -X POST http://localhost:8000/api/v1/references/load-references
```

5. **Открыть приложение:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API документация: http://localhost:8000/docs

## Структура проекта

```
eMedosmotr_AI/
├── backend/                  # FastAPI приложение
│   ├── app/
│   │   ├── main.py          # Точка входа
│   │   ├── models/          # SQLAlchemy модели
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Бизнес-логика
│   │   └── utils/           # Утилиты
│   ├── requirements.txt     # Python зависимости
│   ├── Dockerfile           # Development Dockerfile
│   └── Dockerfile.production # Production Dockerfile
├── frontend/                 # React приложение
│   ├── src/
│   │   ├── components/      # React компоненты
│   │   ├── pages/           # Страницы
│   │   └── App.jsx          # Главный компонент
│   ├── package.json         # Node зависимости
│   ├── Dockerfile           # Development Dockerfile
│   ├── Dockerfile.production # Production Dockerfile
│   └── nginx.conf           # Nginx конфигурация для production
├── docker-compose.yml        # Development оркестрация
├── docker-compose.production.yml # Production оркестрация
├── .env.example             # Пример переменных окружения
└── deploy.sh                # Скрипт деплоя
```

## API Endpoints

### Чат с AI ассистентом
```bash
POST /api/v1/chat/message
{
  "message": "Пациент с диагнозом J45.0, нужна категория годности",
  "conversation_id": "optional-uuid"
}
```

### Поиск кодов МКБ-10
```bash
GET /api/v1/references/icd10/search?query=астма&top_k=10
```

### Категории годности
```bash
GET /api/v1/references/categories
```

### Графы призыва
```bash
GET /api/v1/references/graphs
```

Полная документация API: http://localhost:8000/docs

## Конфигурация

### Переменные окружения

Основные переменные в `.env`:

```env
# OpenAI API
OPENAI_API_KEY=your_api_key_here

# Database
POSTGRES_USER=admin
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=emedosmotr

# AI Settings
AI_MODEL=gpt-4o-mini
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4000

# RAG Settings
RAG_CHUNK_SIZE=1024
RAG_TOP_K=5
EMBEDDING_MODEL=text-embedding-3-small
```

Полный список переменных смотрите в `.env.example`

## Разработка

### Запуск в режиме разработки

```bash
# Запустить все сервисы с hot reload
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Перезапуск отдельного сервиса
docker-compose restart backend
```

### Остановка

```bash
docker-compose down
```

### Доступ к базе данных

```bash
docker exec -it emedosmotr_db psql -U admin -d emedosmotr
```

## Production деплой

### Автоматический деплой через GitHub Actions (рекомендуется)

При каждом push в ветку `main` GitHub Actions автоматически развернет изменения на production сервер.

**Настройка GitHub Secrets:**

1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте следующие secrets:
   - `SERVER_HOST` = 69.197.178.118
   - `SERVER_USER` = administrator
   - `SERVER_PASSWORD` = ваш_пароль_от_сервера

**Workflow файл:** [.github/workflows/deploy.yml](.github/workflows/deploy.yml)

**Как это работает:**
1. Вы редактируете код локально
2. Делаете `git add .`, `git commit -m "описание"`, `git push`
3. GitHub Actions автоматически:
   - Подключается к серверу
   - Делает `git pull`
   - Пересобирает Docker контейнеры
   - Перезапускает приложение
4. Изменения появляются на https://iproject.sbs

### Ручной деплой

Для production используйте `docker-compose.production.yml` с production Dockerfile'ами:

```bash
docker-compose -f docker-compose.production.yml up -d --build
```

Или используйте скрипт `deploy.sh` на сервере:

```bash
cd /var/www/emedosmotr
./deploy.sh
```

Подробные инструкции по деплою смотрите в документации.

## Безопасность

⚠️ **ВАЖНО:**
- НЕ коммитьте `.env` файлы в Git
- Используйте сильные пароли для PostgreSQL
- Генерируйте случайный `SECRET_KEY`
- Ограничьте доступ к API в production
- Используйте HTTPS в production

## Лицензия

MIT License

## Контакты

- GitHub: [@NurlanOmarov](https://github.com/NurlanOmarov)
- Репозиторий: [eMedosmotr_AI](https://github.com/NurlanOmarov/eMedosmotr_AI)

---

Создано с использованием Claude Code 🤖
