# UWSGI

UWSGI is the Web Server Gateway Interface software that is 
required by the project for nginx to function properly.

Reference: https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html

## Installation

For the django project, it is already included with the `requirements.txt` file.

Install it system wide for apache to use like so:
```
sudo pip3 install uwsgi
```

## Configuration
For configuration, we need to create two files for the upstart process, and create
two ini files for the dev and prod versions of the website.


### Project specific ini files
```
sudo mkdir /etc/uwsgi/sites
sudo nano /etc/uwsgi/sites/dev-ritlew
```
Enter the following:
```
project = dev
base = /home/ritlew
env = dev_env

plugins = python3

chdir = %(base)/%(project)
home = %(base)/%(env)
module = %(project).wsgi:application
wsgi-file = ritlew/wsgi.py

py-autoreload = 1

master = true
processes = 5

socket = %(base)/%(project)/%(project).sock
chmod-socket = 664
vacuum = true
```
Now do the same for the production version of the website:
```
sudo nano /etc/uwsgi/sites/prod-ritlew
```
```
[uwsgi]
project = prod
base = /home/ritlew
env = prod_env

plugins = python3

chdir = %(base)/%(project)
home = %(base)/%(env)
module = %(project).wsgi:application
wsgi-file = ritlew/wsgi.py

py-autoreload = 1

master = true
processes = 5

socket = %(base)/%(project)/%(project).sock
chmod-socket = 664
vacuum = true
```

### Upstart and service files
For the upstart file:
```
sudo nano /etc/init/uwsgi.conf
```
Enter the following:
```
description "uWSGI application server in Emperor mode"

start on runlevel [2345]
stop on runlevel [!2345]

setuid ritlew
setgid www-data

exec /usr/bin/uwsgi --emperor /etc/uwsgi/sites
```

For the service file:
```
sudo nano /etc/systemd/system/uwsgi.service
```
Enter the following:
```
[Unit]
Description=uWSGI Emperor service
After=syslog.target

[Service]
ExecStart=/usr/local/bin/uwsgi --emperor /etc/uwsgi/sites
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all
User=ritlew
Group=www-data

[Install]
WantedBy=multi-user.target
```

```
sudo service uwsgi restart
```
