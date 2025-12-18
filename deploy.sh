#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Переход в директорию проекта
cd /var/www/emedosmotr

# Получение последних изменений
echo "📥 Pulling latest changes..."
git pull origin main

# Остановка контейнеров
echo "🛑 Stopping containers..."
docker-compose -f docker-compose.production.yml down

# Сборка и запуск
echo "🔨 Building and starting containers..."
docker-compose -f docker-compose.production.yml up -d --build

# Очистка неиспользуемых образов
echo "🧹 Cleaning up unused images..."
docker image prune -f

echo "✅ Deployment complete!"
echo "📊 Container status:"
docker-compose -f docker-compose.production.yml ps
