from django.views.generic import TemplateView, CreateView, FormView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms

from .models import User, Perfil, Tenant, DocumentoExterno

TIPO_USUARIO_MAP = {
    'bolsista': 'COMMON',
    'colaborador': 'COMMON',
    'externo': 'COMMON',
}


class RegistroForm(forms.ModelForm):
    telefone = forms.CharField(max_length=20, required=False, label='Telefone')
    tipo_usuario = forms.ChoiceField(
        choices=[('bolsista', 'Bolsista'), ('colaborador', 'Colaborador'), ('externo', 'Externo')],
        label='Tipo de usuário'
    )
    unidade = forms.CharField(max_length=255, required=False, label='Unidade')
    documentos = forms.FileField(required=False, label='RG / CPF')
    password1 = forms.CharField(widget=forms.PasswordInput, label='Senha')
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirmar senha')

    class Meta:
        model = User
        fields = ['nome_completo', 'email']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('As senhas não conferem.')
        return p2


class LandingPageView(TemplateView):
    template_name = 'accounts/landing.html'


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('home')


class RegistroView(FormView):
    template_name = 'accounts/registro.html'
    form_class = RegistroForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = User.objects.create_user(
            email=form.cleaned_data['email'],
            nome_completo=form.cleaned_data['nome_completo'],
            password=form.cleaned_data['password1'],
        )
        tenant, _ = Tenant.objects.get_or_create(
            nome='SESI', defaults={'dominio': 'sesi', 'ativo': True}
        )
        perfil = Perfil.objects.create(
            user=user,
            tipo=TIPO_USUARIO_MAP.get(form.cleaned_data['tipo_usuario'], 'COMMON'),
            telefone=form.cleaned_data.get('telefone', ''),
            unidade=form.cleaned_data.get('unidade', ''),
            tenant=tenant,
        )
        if form.cleaned_data.get('documentos'):
            DocumentoExterno.objects.create(
                user=user,
                arquivo=form.cleaned_data['documentos'],
                tipo='OUTRO',
                tenant=tenant,
            )
        messages.success(self.request, 'Conta criada com sucesso! Faça login.')
        return super().form_valid(form)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'base/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        tipo = perfil.tipo if perfil else 'COMMON'
        context['tipo_usuario'] = tipo
        context['has_cadastro'] = hasattr(user, 'cadastro')
        return context


class AprovarUsuarioView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=kwargs['pk'])
        user.is_active = True
        user.save()
        messages.success(request, f'Usuário {user.nome_completo} aprovado.')
        return redirect('admin_dashboard')
