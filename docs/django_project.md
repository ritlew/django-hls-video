# ritlew
To set up the project files, we place the files on the server in the correct location
and set up the virtual environment.

## Django user
Create a django user (normally use ritlew for this project):
```
sudo useradd -m ritlew
sudo passwd ritlew
```

## Project code
Now place the project files twice in the `ritlew` home directory. Once as a `prod` 
directory and once as a `dev` directory. This can be done in a number of ways 
(git clone, PyCharm deployment, FTP/SFTP, etc.).

## virtualenv
Set up two virtual environments so there is one for each version of the project.
```
cd /home/ritlew
sudo apt install python3-pip
sudo pip3 install virtualenv
virtualenv -p python3 dev_env
virtualenv -p python3 prod_env
source dev_env/bin/activate
cd dev
pip install -r requirements.txt
cd ..
deactivate
source prod_env/bin/activate
cd prod
pip install -r requirements.txt
cd ..
deactivate
```

The projects should now be configured for use by `uwsgi` and `nginx`.