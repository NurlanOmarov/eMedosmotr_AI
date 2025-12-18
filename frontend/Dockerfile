# Frontend Dockerfile для eMedosmotr AI
FROM node:20-alpine

# Установка рабочей директории
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm install

# Копирование кода приложения
COPY . .

# Экспорт порта Vite dev server
EXPOSE 5173

# Команда по умолчанию (переопределяется в docker-compose.yml)
CMD ["npm", "run", "dev"]
