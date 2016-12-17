from django.http import HttpResponse
from django.shortcuts import render

import subprocess

# Create your views here.


def pull(request):
    subprocess.call("ssh-agent bash -c 'ssh-add /home4/square13/public_html/ritlew/code/id_rsa; git pull'", shell=True)
    return HttpResponse(status=200)
