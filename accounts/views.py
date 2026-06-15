from django.views.generic import TemplateView, CreateView, FormView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django import forms

from base.mixins import ManagerRequiredMixin

from .models import User, Perfil, Tenant, DocumentoExterno
from editais.models import Edital, AplicacaoEdital
from classificacao.models import Classificacao
from cadastro.models import SolicitacaoEdicao

class RegistroForm(forms.ModelForm):
    telefone = forms.CharField(
        max_length=20, required=False, label='Telefone',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(67) 99999-9999'})
    )
    documentos = forms.FileField(
        required=False, label='RG / CPF',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['nome_completo', 'email']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('As senhas não conferem.')
        return p2


class LandingPageView(TemplateView):
    template_name = 'accounts/landing.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().get(request, *args, **kwargs)


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
        Perfil.objects.create(
            user=user,
            tipo='COMMON',
            telefone=form.cleaned_data.get('telefone', ''),
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
        if user.is_superuser:
            tipo = 'ADMIN'
        else:
            tipo = perfil.tipo if perfil else 'COMMON'
        tenant = perfil.tenant if perfil else None
        context['tipo_usuario'] = tipo
        context['has_cadastro'] = hasattr(user, 'cadastro')

        if tipo == 'ADMIN':
            context['total_usuarios'] = User.objects.filter(
                perfil__tenant=tenant, is_active=True
            ).count()
            context['total_pendentes'] = User.objects.filter(
                perfil__tenant=tenant, is_active=False
            ).count()
            context['total_editais'] = Edital.objects.filter(tenant=tenant).count()
            context['total_aplicacoes'] = AplicacaoEdital.objects.filter(tenant=tenant).count()
            context['total_classificacoes'] = Classificacao.objects.filter(tenant=tenant).count()
            context['total_pendentes_solicitacao'] = SolicitacaoEdicao.objects.filter(
                tenant=tenant, status='pendente'
            ).count()

        elif tipo == 'MANAGER':
            context['total_editais_abertos'] = Edital.objects.filter(
                tenant=tenant, status='aberto'
            ).count()
            context['total_pendentes_avaliacao'] = AplicacaoEdital.objects.filter(
                tenant=tenant, status__in=['pendente', 'em_analise']
            ).count()
            context['total_aplicacoes'] = AplicacaoEdital.objects.filter(tenant=tenant).count()
            context['total_pendentes_solicitacao'] = SolicitacaoEdicao.objects.filter(
                tenant=tenant, status='pendente'
            ).count()

        else:
            context['total_editais_abertos'] = Edital.objects.filter(
                tenant=tenant, status='aberto'
            ).count()
            if hasattr(user, 'cadastro'):
                context['total_aplicacoes'] = AplicacaoEdital.objects.filter(
                    bolsista=user.cadastro
                ).count()
                context['total_classificacoes'] = Classificacao.objects.filter(
                    aplicacao__bolsista=user.cadastro
                ).count()
            else:
                context['total_aplicacoes'] = 0
                context['total_classificacoes'] = 0

        return context


class AprovarUsuarioView(ManagerRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(
            User, pk=kwargs['pk'], perfil__tenant=getattr(request, 'tenant', None)
        )
        user.is_active = True
        user.save()
        messages.success(request, f'Usuário {user.nome_completo} aprovado.')
        if request.headers.get('HX-Request'):
            html = render_to_string(
                'accounts/partials/usuario_row.html',
                {'u': user},
                request=request,
            )
            return HttpResponse(html)
        return redirect('admin_dashboard')
