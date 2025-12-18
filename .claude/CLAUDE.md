# Инструкции для Claude Code - проект eMedosmotr_AI

## Структура проекта

Это fullstack приложение с:
- **Backend**: FastAPI (Python) - запускается в Docker
- **Frontend**: React + Vite - запускается в Docker
- **База данных**: PostgreSQL с pgvector - запускается в Docker

## ВАЖНО: Запуск проекта

**ВСЕ КОМПОНЕНТЫ ЗАПУСКАЮТСЯ ЧЕРЕЗ DOCKER COMPOSE!**

### Правильный способ запуска:

```bash
# Запуск всех сервисов (backend, frontend, database)
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### НЕ ИСПОЛЬЗУЙ:

❌ `python3 -m uvicorn app.main:app` - backend в Docker, не локально!
❌ `npm run dev` в корне - frontend тоже в Docker!
❌ Скрипты `start_backend.sh` и `start_frontend.sh` - устаревшие!

### Порты:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API документация: http://localhost:8000/docs
- PostgreSQL: localhost:5432

### Если порт занят:

```bash
# Проверить процесс на порту
lsof -i :5173  # или :8000, :5432

# Остановить процесс
kill <PID>
```

## Разработка

- Backend код: `/backend`
- Frontend код: `/frontend`
- Docker-compose файл: `/docker-compose.yml`
- Переменные окружения: `/.env`

Volumes монтированы, изменения применяются автоматически (hot reload).
