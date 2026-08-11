from django.urls import path
from django.contrib.auth.views import (
    LogoutView,
    PasswordChangeView,
    PasswordChangeDoneView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from . import views

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('sair/', LogoutView.as_view(next_page='landing'), name='logout'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('usuarios/<int:pk>/aprovar/', views.AprovarUsuarioView.as_view(), name='aprovar_usuario'),

    # Alteracao de senha (usuario logado)
    path(
        'alterar-senha/',
        PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            success_url='/alterar-senha/concluido/',
        ),
        name='password_change',
    ),
    path(
        'alterar-senha/concluido/',
        PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'),
        name='password_change_done',
    ),

    # Recuperacao de senha (Django built-in auth views)
    path(
        'recuperar-senha/',
        PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url='/recuperar-senha/enviado/',
        ),
        name='password_reset',
    ),
    path(
        'recuperar-senha/enviado/',
        PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done',
    ),
    path(
        'redefinir-senha/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url='/redefinir-senha/concluido/',
        ),
        name='password_reset_confirm',
    ),
    path(
        'redefinir-senha/concluido/',
        PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete',
    ),
]
