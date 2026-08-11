from django.urls import path

from . import views

urlpatterns = [
    path('trilha/', views.TrilhaBolsistaView.as_view(), name='painel_trilha'),
    path('<int:pk>/', views.PainelBolsistaDetailView.as_view(), name='painel_detalhe'),
    path('<int:pk>/resumir/', views.resumir_bolsista, name='painel_resumir_bolsista'),
    path('<int:pk>/analisar/', views.analisar_bolsista, name='painel_analisar_bolsista'),
    path('tarefa/<str:task_id>/status/', views.painel_task_status, name='painel_task_status'),
]
