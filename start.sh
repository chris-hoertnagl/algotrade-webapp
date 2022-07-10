#!/bin/bash
sleep 3
echo "Running personalized entry script"
cd src || exit

rand=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 50)
export DJANGO_SECRET_KEY=$rand

rm -rf tradeapp/migrations
mkdir tradeapp/migrations
touch tradeapp/migrations/__init__.py

python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
echo "Creating super user"
echo "from django.contrib.auth.models import User; User.objects.filter(email='admin@example.com').delete(); User.objects.create_superuser('admin', 'admin@example.com', 'algotrade210')" | python manage.py shell
echo "Starting server"
#python manage.py runserver 0.0.0.0:8000

gunicorn algotrade.wsgi:application --bind 0.0.0.0:8000
