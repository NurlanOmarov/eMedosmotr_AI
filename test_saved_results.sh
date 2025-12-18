#!/bin/bash

echo "🧪 Тест сохраненных результатов AI анализа"
echo "=========================================="
echo ""

# 1. Проверка БД
echo "1️⃣ Проверка данных в PostgreSQL БД..."
docker-compose exec -T postgres psql -U admin -d emedosmotr -c "
SELECT
    cd.id as draft_id,
    c.full_name,
    COUNT(ar.id) as analyses_count
FROM conscript_drafts cd
JOIN conscripts c ON c.id = cd.conscript_id
LEFT JOIN ai_analysis_results ar ON ar.conscript_draft_id = cd.id
WHERE c.full_name LIKE '%ТЕСТОВЫЙ ПРИЗЫВНИК #11%'
GROUP BY cd.id, c.full_name;
" 2>/dev/null

echo ""

# 2. Получаем draft_id
DRAFT_ID=$(docker-compose exec -T postgres psql -U admin -d emedosmotr -t -A -c "
SELECT cd.id
FROM conscript_drafts cd
JOIN conscripts c ON c.id = cd.conscript_id
WHERE c.full_name LIKE '%ТЕСТОВЫЙ ПРИЗЫВНИК #11%'
LIMIT 1;
" 2>/dev/null | tr -d '\r')

echo "2️⃣ ID призывника (draft_id): $DRAFT_ID"
echo ""

# 3. Тест API endpoint
echo "3️⃣ Тест API /api/v1/validation/saved-analysis/$DRAFT_ID"
RESPONSE=$(curl -s "http://localhost:8000/api/v1/validation/saved-analysis/$DRAFT_ID")
TOTAL_COUNT=$(echo $RESPONSE | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('total_count', 0))" 2>/dev/null || echo "ERROR")

echo "   Результат: total_count = $TOTAL_COUNT"
echo ""

# 4. Проверка CORS
echo "4️⃣ Проверка CORS headers..."
curl -s -I -H "Origin: http://localhost:5173" \
  "http://localhost:8000/api/v1/validation/saved-analysis/$DRAFT_ID" | grep -i "access-control"
echo ""

# 5. Проверка призывников через API
echo "5️⃣ Проверка GET /api/v1/conscripts/ (первый призывник)..."
FIRST_CONSCRIPT=$(curl -s "http://localhost:8000/api/v1/conscripts/?limit=1" | \
  python3 -c "import sys, json; data = json.load(sys.stdin); c = data['conscripts'][0]; print(f\"ID: {c['id']}, Name: {c['full_name']}\")" 2>/dev/null || echo "ERROR")
echo "   $FIRST_CONSCRIPT"
echo ""

echo "✅ Тест завершен!"
echo ""
echo "📋 Инструкция для проверки фронтенда:"
echo "   1. Откройте http://localhost:5173"
echo "   2. Нажмите F12 (DevTools)"
echo "   3. Перейдите на вкладку Console"
echo "   4. Выберите призывника 'ТЕСТОВЫЙ ПРИЗЫВНИК #11'"
echo "   5. Нажмите '🤖 ИИ АНАЛИЗ'"
echo "   6. Проверьте логи в консоли"
