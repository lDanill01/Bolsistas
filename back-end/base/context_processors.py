from .mixins import GROUP_MANAGER, GROUP_VIEW_USER, GROUP_EXECUTE_USER


def perfil_context(request):
    if not request.user.is_authenticated:
        return {
            'is_superuser': False,
            'is_manager': False,
            'is_view_user': False,
            'is_execute_user': False,
            'has_cadastro': False,
        }

    groups = set(request.user.groups.values_list('name', flat=True))

    return {
        'is_superuser': request.user.is_superuser,
        'is_manager': GROUP_MANAGER in groups,
        'is_view_user': GROUP_VIEW_USER in groups,
        'is_execute_user': GROUP_EXECUTE_USER in groups,
        'has_cadastro': hasattr(request.user, 'cadastro'),
    }
