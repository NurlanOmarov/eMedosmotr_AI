#!/bin/bash

cd /Users/nurlan/Documents/projects/eMedosmotr_AI

echo "Starting backend через Docker Compose..."
docker-compose up -d backend

echo ""
echo "✅ Backend запущен!"
echo "📍 API: http://localhost:8000"
echo "📍 Документация: http://localhost:8000/docs"
echo ""
echo "Просмотр логов: docker-compose logs -f backend"
