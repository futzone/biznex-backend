#!/bin/bash

set -e
echo "Running Alembic migrations..."
alembic upgrade head

pip freeze > requirements.txt


uvicorn app.main.main:create_app --reload --factory --host 0.0.0.0 --port 8000
