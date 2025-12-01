#!/bin/bash
set -e

echo "Running database migrations..."
flask db upgrade || flask db init && flask db migrate && flask db upgrade

echo "Starting server..."
exec "$@"
