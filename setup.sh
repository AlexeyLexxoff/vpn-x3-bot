#!/bin/bash

# Цвета для красивого вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== Автоматическая установка VPN Бота ===${NC}"

# 1. Проверка прав root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Пожалуйста, запустите скрипт от имени root (sudo bash setup.sh)${NC}"
  exit 1
fi

# 2. Установка зависимостей
echo -e "${YELLOW}[1/4] Установка системных зависимостей (Git, Docker)...${NC}"
apt-get update -y && apt-get install -y git curl
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker уже установлен."
fi

# 3. Клонирование репозитория
echo -e "${YELLOW}[2/4] Скачивание файлов бота...${NC}"
if [ ! -d "/opt/vpn-bot" ]; then
    git clone https://github.com/AlexeyLexxoff/vpn-x3-bot.git /opt/vpn-bot
else
    echo "Папка /opt/vpn-bot уже существует. Обновляем код..."
    cd /opt/vpn-bot && git pull
fi

cd /opt/vpn-bot

# 4. Настройка .env
echo -e "${YELLOW}[3/4] Проверка конфигурации...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${RED}⚠️ ВНИМАНИЕ: Создан файл /opt/vpn-bot/.env${NC}"
    echo -e "Отредактируйте его (nano /opt/vpn-bot/.env), вставив ваши токены, и запустите скрипт еще раз."
    exit 0
fi

# 5. Запуск Docker
echo -e "${YELLOW}[4/4] Сборка и запуск контейнера...${NC}"
docker compose up -d --build

echo -e "${GREEN}✅ Установка успешно завершена!${NC}"
echo -e "Логи можно посмотреть командой: docker compose logs -f"
