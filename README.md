# ЛР1. Контейнерні мережі (Docker)

Трирівневий сервіс nginx → Flask → Redis у двох сегментованих мережах Docker.

## Запуск
    docker compose up -d --build
    curl http://localhost:8080/        # лічильник зростає на кожен запит
    docker compose up -d --scale app=3 # кілька реплік app

Базовий варіант через Docker CLI: `./run_cli.sh`, очищення: `./cleanup_cli.sh`.

## Склад
- `docker-compose.yml`: мережі `frontend` та `backend` (internal), healthcheck, depends_on.
- `app/`: Flask-застосунок із лічильником у Redis.
- `nginx.conf`: зворотний проксі з динамічним DNS-резолвінгом.
- `evidence/`: виводи команд, `report/`: звіт (PDF, DOCX).
- Перегенерація звіту: `pip install -r common/requirements-report.txt && LAB_AUTHOR="Прізвище_Ім'я" LAB_GROUP="ІО-XX" python build_report.py`
