#!/bin/bash

set -e

cd ~/game-zone

mkdir -p backups

DATE=$(date +%Y-%m-%d_%H-%M-%S)

docker compose cp bot:/app/data/requests.db "backups/requests_$DATE.db"

echo "Резервная копия создана: backups/requests_$DATE.db"
