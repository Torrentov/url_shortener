#!/bin/sh
set -e

echo "Waiting for the database"
until nc -z db 5432; do
  echo "Database unavailable, retry in 5 seconds"
  sleep 5
done
echo "Database available"

alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
