docker-compose build
docker-compose run uwsgi bash -c "python manage.py collectstatic --noinput && python manage.py migrate"
docker-compose up --force-recreate
