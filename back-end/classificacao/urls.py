from django.urls import path
from . import views

urlpatterns = [
    path('criterios/', views.CriterioListView.as_view(), name='criterio_list'),
    path('criterios/criar/', views.CriterioCreateView.as_view(), name='criterio_create'),
    path('criterios/<int:pk>/editar/', views.CriterioUpdateView.as_view(), name='criterio_update'),
    path('avaliacoes/', views.AvaliacaoListView.as_view(), name='avaliacao_list'),
    path('avaliacoes/<int:pk>/', views.AvaliacaoDetailView.as_view(), name='avaliacao_detail'),
]
