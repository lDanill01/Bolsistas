import json
import logging

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.template.loader import render_to_string

from base.mixins import TenantRequiredMixin, ManagerRequiredMixin
from .models import EditalProvisorio, AplicacaoEdital, NIVEL_BOLSA_CONFIG
from .forms import EditalProvisorioForm, CronogramaEventoFormSet, DistribuicaoBolsaFormSet
from accounts.models import Tenant

logger = logging.getLogger(__name__)


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = EditalProvisorio.STATUS_CHOICES
        context['nivel_config_json'] = json.dumps(NIVEL_BOLSA_CONFIG)
        return context


class EditalProvisorioListView(TenantRequiredMixin, ContextMixin, ListView):
    model = EditalProvisorio
    template_name = 'editais/edital_list.html'
    context_object_name = 'editais'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            qs = EditalProvisorio.objects.all().select_related('criado_por')
        else:
            qs = EditalProvisorio.objects.filter(tenant=self.request.tenant).select_related('criado_por')
        busca = self.request.GET.get('busca', '')
        status = self.request.GET.get('status', '')
        if busca:
            qs = qs.filter(nome_instituto__icontains=busca)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busca'] = self.request.GET.get('busca', '')
        context['status_atual'] = self.request.GET.get('status', '')
        return context


class EditalProvisorioCreateView(ManagerRequiredMixin, ContextMixin, CreateView):
    model = EditalProvisorio
    template_name = 'editais/edital_form.html'
    form_class = EditalProvisorioForm
    success_url = reverse_lazy('edital_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                self.request.POST, prefix='cronograma'
            )
            context['distribuicao_formset'] = DistribuicaoBolsaFormSet(
                self.request.POST, prefix='distribuicao'
            )
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(prefix='cronograma')
            context['distribuicao_formset'] = DistribuicaoBolsaFormSet(prefix='distribuicao')
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        distribuicao_formset = context['distribuicao_formset']
        if cronograma_formset.is_valid() and distribuicao_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.criado_por = self.request.user
            self.object.tenant = self.request.tenant or Tenant.objects.filter(ativo=True).first()
            self.object.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            distribuicao_formset.instance = self.object
            distribuicao_formset.save()
            messages.success(self.request, 'Edital criado com sucesso!')
            return redirect(self.get_success_url())
        logger.error('Formset errors - cronograma: %s, distribuicao: %s',
                     cronograma_formset.errors, distribuicao_formset.errors)
        return self.render_to_response(context)


class EditalProvisorioUpdateView(ManagerRequiredMixin, ContextMixin, UpdateView):
    model = EditalProvisorio
    template_name = 'editais/edital_form.html'
    form_class = EditalProvisorioForm

    def get_queryset(self):
        if self.request.user.is_superuser:
            return EditalProvisorio.objects.all()
        return EditalProvisorio.objects.filter(tenant=self.request.tenant)

    success_url = reverse_lazy('edital_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                self.request.POST, instance=self.object, prefix='cronograma'
            )
            context['distribuicao_formset'] = DistribuicaoBolsaFormSet(
                self.request.POST, instance=self.object, prefix='distribuicao'
            )
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                instance=self.object, prefix='cronograma'
            )
            context['distribuicao_formset'] = DistribuicaoBolsaFormSet(
                instance=self.object, prefix='distribuicao'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        distribuicao_formset = context['distribuicao_formset']
        if cronograma_formset.is_valid() and distribuicao_formset.is_valid():
            self.object = form.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            distribuicao_formset.instance = self.object
            distribuicao_formset.save()
            messages.success(self.request, 'Edital atualizado com sucesso!')
            return redirect(self.get_success_url())
        logger.error('Formset errors - cronograma: %s, distribuicao: %s',
                     cronograma_formset.errors, distribuicao_formset.errors)
        return self.render_to_response(context)


class EditalProvisorioDetailView(TenantRequiredMixin, ContextMixin, DetailView):
    model = EditalProvisorio
    template_name = 'editais/edital_detail.html'
    context_object_name = 'edital'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return EditalProvisorio.objects.all().select_related('criado_por')
        return EditalProvisorio.objects.filter(tenant=self.request.tenant).select_related('criado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cronograma'] = self.object.cronograma.all()
        user = self.request.user
        context['tem_cadastro'] = hasattr(user, 'cadastro')
        if hasattr(user, 'cadastro'):
            context['ja_aplicou'] = AplicacaoEdital.objects.filter(
                bolsista=user.cadastro, edital=self.object
            ).exists()
        else:
            context['ja_aplicou'] = False
        return context


class EditalProvisorioDeleteView(ManagerRequiredMixin, ContextMixin, DeleteView):
    model = EditalProvisorio
    template_name = 'editais/edital_confirm_delete.html'
    success_url = reverse_lazy('edital_list')

    def get_queryset(self):
        if self.request.user.is_superuser:
            return EditalProvisorio.objects.all()
        return EditalProvisorio.objects.filter(tenant=self.request.tenant)

    def form_valid(self, form):
        messages.success(self.request, 'Edital removido com sucesso!')
        return super().form_valid(form)


def edital_pdf_view(request, pk):
    if request.user.is_superuser:
        edital = EditalProvisorio.objects.select_related('criado_por').prefetch_related('distribuicoes', 'cronograma').get(pk=pk)
    else:
        edital = EditalProvisorio.objects.filter(tenant=request.tenant).select_related('criado_por').prefetch_related('distribuicoes', 'cronograma').get(pk=pk)
    cronograma = edital.cronograma.all()
    html_string = render(request, 'editais/edital_pdf.html', {
        'edital': edital,
        'cronograma': cronograma,
    }).content.decode('utf-8')

    from xhtml2pdf import pisa
    import io

    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html_string.encode('utf-8')), result)
    if pdf.err:
        return HttpResponse('Erro ao gerar PDF', status=500)
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    filename = f'edital_{edital.get_nome_instituto_display().replace(" ", "_")}_{edital.pk}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


class AplicarEditalView(TenantRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        from decimal import Decimal
        from cadastro.utils import calcular_pontuacao_previa
        from classificacao.models import CriterioClassificacao, Classificacao, ClassificacaoCriterio

        edital = get_object_or_404(EditalProvisorio, pk=kwargs['pk'], tenant=request.tenant)
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


class EditalResumoView(TenantRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        edital = get_object_or_404(EditalProvisorio, pk=kwargs['pk'], tenant=request.tenant)

        from .ai_service import summarize_edital
        result = summarize_edital(edital)

        if result["error"]:
            html = f'<div class="alert alert-danger py-2 small"><i class="bi bi-exclamation-triangle me-1"></i>{result["error"]}</div>'
        else:
            html = render_to_string('editais/partials/edital_resumo.html', {
                'resumo': result['summary'],
                'edital': edital,
            }, request=request)

        return HttpResponse(html)
