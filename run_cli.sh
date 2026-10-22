#!/usr/bin/env bash
# Основне завдання ЛР1: топологія через Docker CLI в одній мережі lab1-net
set -euo pipefail
cd "$(dirname "$0")"

# виконання команди у мережевому просторі хоста (VM Docker Desktop)
hostexec() { docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -u -n -i sh -c "$*"; }

docker network create --driver bridge --subnet 172.28.0.0/24 --gateway 172.28.0.1 lab1-net
docker run -d --name db --network lab1-net redis:7-alpine
docker build -q -t lab1-app:1.0 ./app
docker run -d --name app --network lab1-net -e REDIS_HOST=db lab1-app:1.0
docker run -d --name proxy --network lab1-net -p 8080:80 \
  -v "$PWD/nginx.conf:/etc/nginx/conf.d/default.conf:ro" nginx:1.27-alpine
sleep 3
curl -s http://localhost:8080/
