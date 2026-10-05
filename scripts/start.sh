#!/bin/bash
# Render build script - runs migrations before starting the server

python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec gunicorn ccams.wsgi --log-file -
