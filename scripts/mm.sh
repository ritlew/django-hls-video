SECRET_KEY="test" DB_ENV="dummy" bash -c "
    source venv/bin/activate;
    python manage.py makemigrations video blog"

