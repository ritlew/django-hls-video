# nginx

nginx is the web server used by this project

## Installation
Simply:
```
sudo apt install nginx
sudo service nginx start
```

## Configuration
Only two configuration file needs to be edited for the project:
```
sudo rm /etc/nginx/sites-enabled/default
sudo nano /etc/nginx/sites-available/dev-ritlew
```
Enter:
```
# configuration of the server
server {
    # the port your site will be served on
    listen      8080;
    # the domain name it will serve for
    server_name ritlew.com; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /media  {
        alias /home/ritlew/media;  # your Django project's media files - amend as required
    }

    location /static {
        alias /home/ritlew/dev/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        include    /home/ritlew/dev/uwsgi_params;
        uwsgi_pass unix:///home/ritlew/dev/dev.sock; # for a file socket
    }
}

```
Now for the production version:
```
sudo nano /etc/nginx/sites-available/prod-ritlew
```
Enter:
```
# configuration of the server
server {
    # the port your site will be served on
    listen      80;
    # the domain name it will serve for
    server_name ritlew.com; # substitute your machine's IP address or FQDN
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /media  {
        alias /home/ritlew/media;  # your Django project's media files - amend as required
    }

    location /static {
        alias /home/ritlew/prod/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        include    /home/ritlew/prod/uwsgi_params;
        uwsgi_pass unix:///home/ritlew/prod/prod.sock; # for a file socket
    }
}
```

Finally, just symlink these to the enabled folder:
```
sudo ln -s /etc/nginx/sites-available/dev-ritlew /etc/nginx/sites-enabled/dev-ritlew
sudo ln -s /etc/nginx/sites-available/prod-ritlew /etc/nginx/sites-enabled/prod-ritlew
```

```
sudo service nginx restart
```