from django.http import Http404

def auth_or_404(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404()
        return function(request, *args, **kwargs)
    return wrap
