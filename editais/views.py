from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django import forms

from base.mixins import TenantRequiredMixin, ManagerRequiredMixin
from .models import Edital, AplicacaoEdital
from cadastro.models import CadastroBolsista


class EditalForm(forms.ModelForm):
    class Meta:
        model = Edital
        fields = ['nome', 'descricao', 'requisitos', 'data_abertura', 'data_fechamento', 'status']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requisitos': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'data_abertura': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'data_fechamento': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class EditalListView(TenantRequiredMixin, ListView):
    model = Edital
    template_name = 'editais/edital_list.html'
    context_object_name = 'editais'
    paginate_by = 10

    def get_queryset(self):
        qs = Edital.objects.filter(tenant=self.request.tenant).select_related('criado_por')
        busca = self.request.GET.get('busca', '')
        status = self.request.GET.get('status', 'todos')
        if busca:
            qs = qs.filter(nome__icontains=busca)
        if status and status != 'todos':
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = getattr(self.request.user, 'perfil', None)
        context['pode_criar'] = perfil and perfil.tipo in ('ADMIN', 'MANAGER')
        context['busca'] = self.request.GET.get('busca', '')
        context['status_atual'] = self.request.GET.get('status', 'todos')
        return context


class EditalCreateView(ManagerRequiredMixin, CreateView):
    model = Edital
    template_name = 'editais/edital_form.html'
    form_class = EditalForm
    success_url = reverse_lazy('edital_list')

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        form.instance.tenant = self.request.tenant
        messages.success(self.request, 'Edital criado com sucesso!')
        return super().form_valid(form)


class EditalDetailView(TenantRequiredMixin, DetailView):
    model = Edital
    template_name = 'editais/edital_detail.html'
    context_object_name = 'edital'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        perfil = getattr(user, 'perfil', None)
        context['pode_editar'] = perfil and perfil.tipo in ('ADMIN', 'MANAGER')
        context['tem_cadastro'] = hasattr(user, 'cadastro')
        if hasattr(user, 'cadastro'):
            context['ja_aplicou'] = AplicacaoEdital.objects.filter(
                bolsista=user.cadastro, edital=self.object
            ).exists()
        else:
            context['ja_aplicou'] = False
        return context

    def get_queryset(self):
        return Edital.objects.filter(tenant=self.request.tenant)


class EditalUpdateView(ManagerRequiredMixin, UpdateView):
    model = Edital
    template_name = 'editais/edital_form.html'
    form_class = EditalForm

    def get_queryset(self):
        return Edital.objects.filter(tenant=self.request.tenant)

    def get_success_url(self):
        return reverse_lazy('edital_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Edital atualizado com sucesso!')
        return super().form_valid(form)


class AplicarEditalView(TenantRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        from decimal import Decimal
        from cadastro.utils import calcular_pontuacao_previa
        from classificacao.models import CriterioClassificacao, Classificacao, ClassificacaoCriterio

        edital = get_object_or_404(Edital, pk=kwargs['pk'], tenant=request.tenant)
        if not hasattr(request.user, 'cadastro'):
            messages.warning(request, 'Complete seu cadastro antes de se candidatar.')
            return redirect('cadastro_create')
        bolsista = request.user.cadastro
        if AplicacaoEdital.objects.filter(bolsista=bolsista, edital=edital).exists():
            messages.warning(request, 'Você já se candidatou a este edital.')
        else:
            aplicacao = AplicacaoEdital.objects.create(
                bolsista=bolsista, edital=edital, tenant=request.tenant
            )

            criterios = CriterioClassificacao.objects.filter(tenant=request.tenant, ativo=True)
            pontos_por_criterio, pontuacao_total = calcular_pontuacao_previa(bolsista, criterios)

            if pontos_por_criterio:
                classificacao = Classificacao.objects.create(
                    aplicacao=aplicacao,
                    classificador=request.user,
                    pontuacao_total=Decimal('0'),
                    observacoes='Classificação automática baseada no perfil do candidato.',
                    tenant=request.tenant,
                )
                for tipo_criterio, dados in pontos_por_criterio.items():
                    criterio = criterios.filter(tipo_criterio=tipo_criterio).first()
                    if criterio:
                        ClassificacaoCriterio.objects.create(
                            classificacao=classificacao,
                            criterio=criterio,
                            nota=dados['nota'],
                        )
                classificacao.pontuacao_total = pontuacao_total
                classificacao.save(update_fields=['pontuacao_total'])

            messages.success(request, 'Candidatura realizada com sucesso!')
        return redirect('edital_detail', pk=edital.pk)


class AplicacaoListView(TenantRequiredMixin, ListView):
    model = AplicacaoEdital
    template_name = 'editais/aplicacao_list.html'
    context_object_name = 'aplicacoes'
    paginate_by = 10

    def get_queryset(self):
        qs = AplicacaoEdital.objects.filter(tenant=self.request.tenant)
        perfil = getattr(self.request.user, 'perfil', None)
        if perfil and perfil.tipo in ('ADMIN', 'MANAGER'):
            status = self.request.GET.get('status', 'todas')
            if status and status != 'todas':
                qs = qs.filter(status=status)
        else:
            if hasattr(self.request.user, 'cadastro'):
                qs = qs.filter(bolsista=self.request.user.cadastro)
            else:
                qs = AplicacaoEdital.objects.none()
        return qs.select_related('bolsista__user', 'edital')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        perfil = getattr(self.request.user, 'perfil', None)
        context['eh_gestor'] = perfil and perfil.tipo in ('ADMIN', 'MANAGER')
        context['status_atual'] = self.request.GET.get('status', 'todas')
        return context


class CancelarAplicacaoView(TenantRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        aplicacao = get_object_or_404(
            AplicacaoEdital, pk=kwargs['pk'], bolsista__user=request.user, tenant=request.tenant
        )
        if aplicacao.status == 'pendente':
            aplicacao.delete()
            messages.success(request, 'Candidatura cancelada.')
        else:
            messages.warning(request, 'Não é possível cancelar uma candidatura em andamento.')
        return redirect('aplicacao_list')


class AlterarStatusAplicacaoView(ManagerRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        aplicacao = get_object_or_404(
            AplicacaoEdital, pk=kwargs['pk'], tenant=request.tenant
        )
        novo_status = request.POST.get('status')
        if novo_status in dict(AplicacaoEdital.STATUS_CHOICES):
            aplicacao.status = novo_status
            aplicacao.save()
            messages.success(request, f'Status da candidatura alterado para {aplicacao.get_status_display()}.')
        if request.headers.get('HX-Request'):
            html = render_to_string(
                'editais/partials/aplicacao_row.html',
                {'a': aplicacao, 'eh_gestor': True},
                request=request,
            )
            return HttpResponse(html)
        return redirect('aplicacao_list')
