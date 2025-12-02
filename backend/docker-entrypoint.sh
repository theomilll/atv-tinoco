#!/bin/bash
set -e

echo "Running database migrations..."
flask db upgrade || (flask db init && flask db migrate && flask db upgrade)

echo "Creating default superuser..."
python manage.py create-superuser || echo "Superuser may already exist"

echo "Starting server..."
exec "$@"
