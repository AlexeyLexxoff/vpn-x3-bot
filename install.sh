#!/bin/bash

echo "=== Установка VPN Бота ==="

# 1. Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "Docker не найден. Устанавливаем..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker уже установлен."
fi

# 2. Проверка наличия Docker Compose
if ! docker compose version &> /dev/null; then
    echo "Docker Compose не найден. Устанавливаем..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

# 3. Проверка файла .env
if [ ! -f .env ]; then
    echo "⚠️ Файл .env не найден! Создайте его по примеру .env.example и запустите скрипт снова."
    exit 1
fi

# 4. Сборка и запуск
echo "Собираем и запускаем бота..."
docker compose up -d --build

echo "✅ Установка завершена!"
echo "Проверьте статус: docker compose logs -f"

