from django.shortcuts import redirect
from django.conf import settings

PATHS_LIVRES = [
    'login',
    'registro',
    'admin',
    'static',
    'media',
    'health',
    'recuperar-senha',
    'redefinir-senha',
]

PATHS_EXATOS = [
    '',
]


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info.strip('/')
            if path in PATHS_EXATOS:
                return self.get_response(request)
            if not any(path.startswith(p) for p in PATHS_LIVRES):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
