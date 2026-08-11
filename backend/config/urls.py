from django.contrib import admin
from django.urls import path, include

from base import views as base_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/tasks/', include('dj_celery_panel.urls')),
    path('', include('accounts.urls')),
    path('cadastro/', include('cadastro.urls')),
    path('editais/', include('editais.urls')),
    path('notificacoes/', include('notifications.urls')),
    path('classificacao/', include('classificacao.urls')),
    path('painel/', include('painel_bolsistas.urls')),
    path('health/', base_views.health_check, name='health_check'),

    path('media/<path:path>', base_views.media_protegida, name='protected_media'),
]
