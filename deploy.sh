#!/bin/bash

set -e

echo "================================"
echo "     GAME ZONE DEPLOY"
echo "================================"

cd /home/grigorii/game-zone

echo "[1/3] Создание резервной копии..."
./backup.sh

echo "[2/3] Сборка и запуск контейнеров..."
docker compose up -d --build

echo "[3/3] Проверка контейнеров..."
docker compose ps

echo "================================"
echo "   GAME ZONE DEPLOY COMPLETE"
echo "================================"
