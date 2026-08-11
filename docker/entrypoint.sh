#!/bin/sh
set -e

export PYTHONPATH="/app/back-end:$PYTHONPATH"
python /app/back-end/manage.py migrate --noinput
python /app/back-end/manage.py collectstatic --noinput --clear

exec "$@"
