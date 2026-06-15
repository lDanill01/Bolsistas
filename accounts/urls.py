from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('sair/', LogoutView.as_view(next_page='login'), name='logout'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('usuarios/<int:pk>/aprovar/', views.AprovarUsuarioView.as_view(), name='aprovar_usuario'),
]
