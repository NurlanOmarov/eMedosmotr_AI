#!/bin/bash

cd /Users/nurlan/Documents/projects/eMedosmotr_AI

echo "Starting frontend через Docker Compose..."
docker-compose up -d frontend

echo ""
echo "✅ Frontend запущен!"
echo "📍 URL: http://localhost:5173"
echo ""
echo "Просмотр логов: docker-compose logs -f frontend"
