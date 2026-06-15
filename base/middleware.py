from django.shortcuts import redirect
from django.conf import settings

PATHS_LIVRES = [
    '/',
    '/login/',
    '/registro/',
    '/admin/',
    '/static/',
    '/media/',
]


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if not any(path.startswith(p) for p in PATHS_LIVRES):
                return redirect(LOGIN_URL)
        return self.get_response(request)
