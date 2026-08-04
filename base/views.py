from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.db import connection
from django.core.files.storage import default_storage

from accounts.models import DocumentoExterno
from cadastro.models import CadastroBolsista, AnexoComprobatorio, ExperienciaProfissional
from .mixins import GROUP_MANAGER


def health_check(request):
    """Endpoint simples para health checks do load balancer/monitoramento."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse({"status": "ok"}, status=200)
    except Exception as exc:
        return JsonResponse({"status": "error", "detail": str(exc)}, status=503)

PASTAS_RESTRITAS = {
    'curriculos': CadastroBolsista,
    'fotos': CadastroBolsista,
    'anexos': AnexoComprobatorio,
    'experiencias': ExperienciaProfissional,
}


def _verificar_dono_arquivo(request, relative):
    """Verifica se o usuario autenticado eh dono do arquivo em pastas restritas."""
    for prefix, model in PASTAS_RESTRITAS.items():
        if not relative.startswith(prefix + '/'):
            continue
        if model == CadastroBolsista:
            cadastro = CadastroBolsista.objects.filter(user=request.user).first()
            if cadastro:
                campo_arquivo = 'curriculo' if prefix == 'curriculos' else 'foto'
                arquivo_campo = getattr(cadastro, campo_arquivo, None)
                if arquivo_campo and arquivo_campo.name == relative:
                    return True
            return False
        else:
            obj = model.objects.filter(anexo=relative).first()
            if obj and hasattr(obj, 'bolsista') and obj.bolsista.user == request.user:
                return True
            return False
    return False


def media_protegida(request, path):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Acesso negado')

    relative = path.replace('\\', '/')
    if relative.startswith('/') or '..' in relative.split('/'):
        return HttpResponseForbidden('Acesso negado')

    if not default_storage.exists(relative):
        raise Http404('Arquivo não encontrado')

    if request.user.is_superuser or request.user.groups.filter(name=GROUP_MANAGER).exists():
        return FileResponse(default_storage.open(relative, 'rb'))

    if relative.startswith('documentos/'):
        doc = DocumentoExterno.objects.filter(arquivo=relative).first()
        if doc and doc.user == request.user:
            return FileResponse(default_storage.open(relative, 'rb'))
        return HttpResponseForbidden('Acesso negado')

    if _verificar_dono_arquivo(request, relative):
        return FileResponse(default_storage.open(relative, 'rb'))

    return HttpResponseForbidden('Acesso negado')
