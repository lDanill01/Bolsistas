from django.urls import path

from . import views

urlpatterns = [
    path('', views.NotificacaoListView.as_view(), name='notificacao_list'),
    path('contador/', views.notificacao_unread_count, name='notificacao_unread_count'),
    path('<int:pk>/marcar-lida/', views.MarcarLidaView.as_view(), name='marcar_lida'),
    path('marcar-todas-lidas/', views.MarcarTodasLidasView.as_view(), name='marcar_todas_lidas'),
]
