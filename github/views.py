from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import subprocess


@csrf_exempt
def pull(request):
    if request.method == "POST":
        subprocess.call("ssh-agent bash -c 'ssh-add /home4/square13/public_html/ritlew/code/ritlew/id_rsa; git pull'", shell=True)
        return HttpResponse(status=200)
    return HttpResponse(status=404)
