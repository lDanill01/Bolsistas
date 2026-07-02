from django.urls import path

from . import views

urlpatterns = [
    path('', views.PainelBolsistasListView.as_view(), name='painel_lista'),
    path('<int:pk>/', views.PainelBolsistaDetailView.as_view(), name='painel_detalhe'),
    path('<int:pk>/resumir/', views.resumir_bolsista, name='painel_resumir_bolsista'),
    path('<int:pk>/analisar/', views.analisar_bolsista, name='painel_analisar_bolsista'),
    path('<int:pk>/avaliar/', views.avaliar_bolsista, name='painel_avaliar_bolsista'),
    path('<int:pk>/sugerir-avaliacao/', views.sugerir_avaliacao_bolsista, name='painel_sugerir_avaliacao'),
    path('tarefa/<str:task_id>/status/', views.painel_task_status, name='painel_task_status'),
    path('download/', views.painel_download_csv, name='painel_download_csv'),
]
