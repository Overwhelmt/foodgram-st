#!/bin/sh
set -e

until python manage.py migrate --noinput; do
    echo "База ещё не готова, повтор через 2 секунды."
    sleep 2
done

python manage.py collectstatic --noinput
python manage.py load_ingredients
python manage.py load_demo

exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
