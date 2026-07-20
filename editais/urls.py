from django.urls import path
from . import views

urlpatterns = [
    path('', views.EditalProvisorioListView.as_view(), name='edital_list'),
    path('criar/', views.EditalProvisorioCreateView.as_view(), name='edital_create'),
    path('<int:edital_pk>/candidatos/', views.AplicacaoEditalListView.as_view(), name='edital_candidatos'),
    path('<int:pk>/', views.EditalProvisorioDetailView.as_view(), name='edital_detail'),
    path('<int:pk>/pdf/', views.edital_pdf_view, name='edital_pdf'),
    path('<int:pk>/editar/', views.EditalProvisorioUpdateView.as_view(), name='edital_update'),
    path('<int:pk>/validar/', views.validar_edital, name='edital_validar'),
    path('<int:pk>/excluir/', views.EditalProvisorioDeleteView.as_view(), name='edital_delete'),
    path('<int:pk>/aplicar/', views.AplicarEditalView.as_view(), name='aplicar_edital'),
    path('<int:pk>/resumir/', views.resumir_edital, name='edital_resumir'),
    path('<int:pk>/analisar/', views.analisar_edital, name='edital_analisar'),
    path('<int:pk>/minha-compatibilidade/', views.minha_compatibilidade, name='edital_compatibilidade'),
    path('tarefa/<str:task_id>/status/', views.edital_task_status, name='edital_task_status'),
    path('aplicacoes/', views.AplicacaoListView.as_view(), name='aplicacao_list'),
    path('aplicacoes/<int:pk>/cancelar/', views.CancelarAplicacaoView.as_view(), name='cancelar_aplicacao'),
    path('aplicacoes/<int:pk>/status/', views.AlterarStatusAplicacaoView.as_view(), name='alterar_status_aplicacao'),
    path('aplicacoes/salvar-avaliacoes/', views.SalvarAvaliacoesLoteView.as_view(), name='salvar_avaliacoes_lote'),
    path('aplicacoes/<int:pk>/editar-avaliacao/', views.EditarAvaliacaoView.as_view(), name='editar_avaliacao'),
]
