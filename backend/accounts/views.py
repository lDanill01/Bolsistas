from django.views.generic import TemplateView, FormView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.models import Group
from django import forms

from base.mixins import (
    ManagerRequiredMixin, GROUP_MANAGER,
    GROUP_VIEW_USER, GROUP_EXECUTE_USER,
)

from .models import User, Perfil
from editais.models import EditalProvisorio, AplicacaoEdital
from cadastro.models import SolicitacaoEdicao, CadastroBolsista


class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crie uma senha'})
    )
    password2 = forms.CharField(
        label='Confirme a Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme a senha'})
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
    success_url = reverse_lazy('landing')

    def form_valid(self, form):
        user = User.objects.create_user(
            email=form.cleaned_data['email'],
            nome_completo=form.cleaned_data['nome_completo'],
            password=form.cleaned_data['password1'],
        )
        Perfil.objects.create(user=user)
        view_group, _ = Group.objects.get_or_create(name=GROUP_VIEW_USER)
        user.groups.add(view_group)
        messages.success(self.request, 'Conta criada com sucesso! Faça login.')
        return super().form_valid(form)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'base/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_superuser'] = user.is_superuser
        context['is_manager'] = user.groups.filter(name=GROUP_MANAGER).exists()
        context['is_view_user'] = user.groups.filter(name=GROUP_VIEW_USER).exists()
        context['is_execute_user'] = user.groups.filter(name=GROUP_EXECUTE_USER).exists()
        context['has_cadastro'] = hasattr(user, 'cadastro')

        # Dados comuns para Superuser / Manager / ExecuteUser
        if user.is_superuser or context['is_manager'] or context['is_execute_user']:
            editais = EditalProvisorio.objects.all()
            context['total_bolsistas'] = CadastroBolsista.objects.count()
            context['total_editais'] = editais.count()
            context['editais_abertos'] = editais.filter(status='aberto').count()
            context['editais_encerrados'] = editais.filter(status='encerrado').count()
            context['editais_em_analise'] = editais.filter(status='em_analise').count()
            context['editais_cancelados'] = editais.filter(status='cancelado').count()
            context['total_candidaturas'] = AplicacaoEdital.objects.count()
            context['candidaturas_pendentes'] = AplicacaoEdital.objects.filter(status='pendente').count()
            context['candidaturas_aprovadas'] = AplicacaoEdital.objects.filter(status='aprovado').count()
            context['candidaturas_rejeitadas'] = AplicacaoEdital.objects.filter(status='rejeitado').count()
            context['solicitacoes_pendentes'] = SolicitacaoEdicao.objects.filter(status='pendente').count()
            context['solicitacoes_total'] = SolicitacaoEdicao.objects.count()
            context['ultimos_editais'] = editais.select_related('criado_por').order_by('-created_at')[:5]
            context['total_usuarios'] = User.objects.filter(is_active=True).count()
            context['total_usuarios_inativos'] = User.objects.filter(is_active=False).count()

        # Dados especificos para ViewUser
        if context['is_view_user']:
            open_editais = EditalProvisorio.objects.filter(status='aberto').order_by('-created_at')
            context['editais_abertos_count'] = open_editais.count()
            context['ultimos_editais_abertos'] = open_editais[:5]

            if context['has_cadastro']:
                bolsista = user.cadastro
                apps = AplicacaoEdital.objects.filter(bolsista=bolsista).select_related('edital')
                context['total_aplicacoes'] = apps.count()
                context['aplicacoes_pendentes'] = apps.filter(status='pendente').count()
                context['aplicacoes_em_analise'] = apps.filter(status='em_analise').count()
                context['aplicacoes_aprovadas'] = apps.filter(status='aprovado').count()
                context['aplicacoes_rejeitadas'] = apps.filter(status='rejeitado').count()
                context['ultimas_aplicacoes'] = apps.order_by('-created_at')[:5]
                # Taxa de aprovação
                if context['total_aplicacoes'] > 0:
                    context['taxa_aprovacao'] = round(
                        context['aplicacoes_aprovadas'] / context['total_aplicacoes'] * 100
                    )
                else:
                    context['taxa_aprovacao'] = 0
                context['cadastro_completo'] = True
            else:
                context['total_aplicacoes'] = 0
                context['aplicacoes_pendentes'] = 0
                context['aplicacoes_em_analise'] = 0
                context['aplicacoes_aprovadas'] = 0
                context['aplicacoes_rejeitadas'] = 0
                context['ultimas_aplicacoes'] = []
                context['taxa_aprovacao'] = 0
                context['cadastro_completo'] = False

        return context


class AprovarUsuarioView(ManagerRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        user = get_object_or_404(
            User, pk=kwargs['pk']
        )
        user.is_active = True
        user.save()

        view_group, _ = Group.objects.get_or_create(name=GROUP_VIEW_USER)
        user.groups.add(view_group)

        messages.success(request, f'Usuário {user.nome_completo} aprovado.')
        if request.headers.get('HX-Request'):
            html = render_to_string(
                'accounts/partials/usuario_row.html',
                {'u': user},
                request=request,
            )
            return HttpResponse(html)
        return redirect('home')
