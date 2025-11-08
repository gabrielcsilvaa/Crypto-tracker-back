#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

# cria superuser padrão (opcional)
echo "from django.contrib.auth import get_user_model; User=get_user_model(); \
      User.objects.filter(username='admin').exists() or \
      User.objects.create_superuser('admin','admin@example.com','admin123')" \
      | python manage.py shell || true

python manage.py runserver 0.0.0.0:3000
