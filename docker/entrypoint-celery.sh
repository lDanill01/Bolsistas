#!/bin/sh
set -e

export PYTHONPATH="/app/backend:$PYTHONPATH"
python /app/backend/manage.py migrate --noinput

exec "$@"
