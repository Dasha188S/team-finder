#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    while ! python -c "
import os, sys, psycopg2
try:
    psycopg2.connect(
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        host=os.environ['POSTGRES_HOST'],
        port=int(os.environ.get('POSTGRES_PORT', 5432)),
    ).close()
except Exception as exc:
    sys.exit(1)
" 2>/dev/null; do
        sleep 1
    done
    echo "PostgreSQL is up."
fi

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-0}" = "1" ]; then
    echo "Seeding demo data..."
    python manage.py seed_demo
fi

exec "$@"
