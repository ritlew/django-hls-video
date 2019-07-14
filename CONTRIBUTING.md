# Contributing
Contributions are welcome through pull requests. 

1. Either take an issue from the issues page or come 
up with your own improvement or feature addition
and create a pull request. 

2. I will review it and suggest changes or start 
discussions.

3. The pull request wil be merged into dev when
approved.

## Building
The project is developed, tested, and deployed with the
use of docker. and docker-compose. There are several 
components/services that are necessary to make the project
functional. 

1. Install [docker](https://docs.docker.com/install/) and 
[docker-compose](https://docs.docker.com/compose/install/).

2. Navigate to the repo directory (where docker-compose.yml 
is).

3. Create superuser account (this will be needed for development):
```
docker run uwsgi sh
python manage.py createsuperuser
exit
```

4. Run `docker-compose up --build`. The server will be available
on http://localhost:4002. Login at http://localhost:4002/admin
using the credentials created earlier to use most of the 
functionality of the website.

## Development
Make changes to the local files and then start the containers with
`docker-compose up --build`. Note the `--build` is necessary to update
the files in the containers.
