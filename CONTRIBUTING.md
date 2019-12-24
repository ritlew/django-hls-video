# Contributing
Contributions are welcome through pull requests. 

1. Either take an issue from the issues page or come 
up with your own improvement or feature addition
and create a pull request. 

2. I will review it and suggest changes or start 
discussions.

3. The pull request will be merged into dev when
approved.

## Building
The project is developed, tested, and deployed with the
use of docker and docker-compose. There are several 
components/services that are necessary to make the project
functional. 

1. Install [docker](https://docs.docker.com/install/) and 
[docker-compose](https://docs.docker.com/compose/install/).

2. Navigate to the repo directory (where dev.yml and prod.yml 
is).

3. Copy the file `.blankenv` to `.env` and enter values that
would be appropriate for your use case. `UWSGI_PROD` should be blank
if it is not a production environment (turns Django's debug on 
if so). Otherwise, make it anything and it will be production settings.
For `SECRET_KEY`, use the `venv.sh` and `gen.sh` scripts included
in the `scripts` directory.


4. Create superuser account (this will be needed for development):
```
docker run web sh
python manage.py createsuperuser
exit
```

5. Run `docker-compose -f dev.yml up --build`. The server will be available
on http://localhost:4001. Login at http://localhost:4001/admin
using the credentials created earlier to use most of the 
functionality of the website.

## Development
Make changes to the local files the files will update automatically as long
as you used the `dev.yml` in the `docker-compose` command. If things aren't 
updating or you are changing other services, you will probably need to rebuild.
