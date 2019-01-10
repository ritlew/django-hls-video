mkdir -p media
mkdir -p static

docker-compose run www_uwsgi python manage.py collectstatic --noinput
CURRENT_UID=$(id -u) CURRENT_GID=$(id -g) docker-compose run www_uwsgi python manage.py migrate
CURRENT_UID=$(id -u) CURRENT_GID=$(id -g) docker-compose up --force-recreate

