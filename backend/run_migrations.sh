#!/bin/bash
# Run database migrations with the correct database URL

export DATABASE_URL="postgresql+psycopg://postgres:ChgMeS0m3t_m3123@localhost:5432/promptshare"

cd "$(dirname "$0")"
source venv/bin/activate

echo "Running database migrations..."
alembic upgrade head

echo "Migration complete!"

