#!/bin/bash

echo "Running alembic migrations..."
alembic upgrade head

echo "Start FastAPI service..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload