from django.http import HttpResponse
from django.shortcuts import render

import subprocess

# Create your views here.


def pull(request):
    if request.method == "POST":
        subprocess.call("ssh-agent bash -c 'ssh-add /home4/square13/public_html/ritlew/code/ritlew/id_rsa; git pull'", shell=True)
        return HttpResponse("thanks", status=200)
    return HttpResponse("sorry", status=404)
