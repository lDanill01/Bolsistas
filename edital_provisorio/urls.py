from django.urls import path
from . import views

app_name = 'edital_provisorio'

urlpatterns = [
    path('', views.EditalProvisorioListView.as_view(), name='list'),
    path('novo/', views.EditalProvisorioCreateView.as_view(), name='create'),
    path('<int:pk>/', views.EditalProvisorioDetailView.as_view(), name='detail'),
    path('<int:pk>/editar/', views.EditalProvisorioUpdateView.as_view(), name='update'),
    path('<int:pk>/excluir/', views.EditalProvisorioDeleteView.as_view(), name='delete'),
]
