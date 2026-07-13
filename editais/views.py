from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.db.models import Count, Q
from celery.result import AsyncResult
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings

from base.mixins import (
    ManagerRequiredMixin, ManagerOrExecuteRequiredMixin,
    ViewUserRequiredMixin, GROUP_MANAGER, GROUP_EXECUTE_USER, GROUP_VIEW_USER,
)
from cadastro.models import CadastroBolsista
from .models import EditalProvisorio, AplicacaoEdital, NIVEL_BOLSA_CONFIG
from .forms import EditalProvisorioForm, CronogramaEventoFormSet, DistribuicaoBolsaFormSet
from . import tasks as ia_tasks


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = EditalProvisorio.STATUS_CHOICES
        context['nivel_config_json'] = json.dumps(NIVEL_BOLSA_CONFIG)
        return context


class EditalProvisorioListView(LoginRequiredMixin, ContextMixin, ListView):
    model = EditalProvisorio
    template_name = 'editais/edital_list.html'
    context_object_name = 'editais'
    paginate_by = 10

    def get_queryset(self):
        qs = EditalProvisorio.objects.all().select_related('criado_por')\
            .prefetch_related('cronograma')\
            .annotate(num_inscritos=Count('aplicacoes'))
        busca = self.request.GET.get('busca', '')
        status = self.request.GET.get('status', '')
        if busca:
            qs = qs.filter(
                Q(nome_instituto__icontains=busca) | Q(numero_serie__icontains=busca)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['busca'] = self.request.GET.get('busca', '')
        context['status_atual'] = self.request.GET.get('status', '')
        return context


class EditalProvisorioCreateView(ManagerOrExecuteRequiredMixin, ContextMixin, CreateView):
    model = EditalProvisorio
    template_name = 'editais/edital_form.html'
    form_class = EditalProvisorioForm
    success_url = reverse_lazy('edital_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
            self.object.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            distribuicao_formset.instance = self.object
            distribuicao_formset.save()
            messages.success(self.request, 'Edital criado com sucesso!')
            return redirect(self.get_success_url())
        return self.render_to_response(context)


class EditalProvisorioUpdateView(ManagerRequiredMixin, ContextMixin, UpdateView):
    model = EditalProvisorio
    template_name = 'editais/edital_form.html'
    form_class = EditalProvisorioForm
    success_url = reverse_lazy('edital_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

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
        return self.render_to_response(context)


class EditalProvisorioDetailView(LoginRequiredMixin, ContextMixin, DetailView):
    model = EditalProvisorio
    template_name = 'editais/edital_detail.html'
    context_object_name = 'edital'

    def get_queryset(self):
        return EditalProvisorio.objects.all().select_related('criado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cronograma'] = self.object.cronograma.all()
        user = self.request.user
        context['tem_cadastro'] = hasattr(user, 'cadastro')
        context['is_view_user'] = user.groups.filter(name=GROUP_VIEW_USER).exists()
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

    def form_valid(self, form):
        messages.success(self.request, 'Edital removido com sucesso!')
        return super().form_valid(form)


def edital_pdf_view(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    edital = get_object_or_404(
        EditalProvisorio.objects.select_related('criado_por').prefetch_related('distribuicoes', 'cronograma'),
        pk=pk,
    )
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


class AplicarEditalView(ViewUserRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        edital = get_object_or_404(EditalProvisorio, pk=kwargs['pk'])

        if edital.status != 'aberto':
            messages.error(request, 'Este edital não está aberto para candidaturas.')
            return redirect('edital_detail', pk=edital.pk)

        if not hasattr(request.user, 'cadastro'):
            messages.warning(request, 'Complete seu cadastro antes de se candidatar.')
            return redirect('cadastro_create')

        bolsista = request.user.cadastro
        if AplicacaoEdital.objects.filter(bolsista=bolsista, edital=edital).exists():
            messages.warning(request, 'Você já se candidatou a este edital.')
        else:
            AplicacaoEdital.objects.create(bolsista=bolsista, edital=edital)
            messages.success(request, 'Candidatura realizada com sucesso!')
        return redirect('edital_detail', pk=edital.pk)


class AplicacaoListView(LoginRequiredMixin, ListView):
    model = AplicacaoEdital
    template_name = 'editais/aplicacao_list.html'
    context_object_name = 'aplicacoes'
    paginate_by = 20

    def get_queryset(self):
        qs = AplicacaoEdital.objects.select_related(
            'bolsista', 'bolsista__user', 'edital'
        ).order_by('-data_aplicacao')

        user = self.request.user
        is_manager = user.is_superuser or user.groups.filter(
            name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]
        ).exists()

        if not is_manager:
            if hasattr(user, 'cadastro'):
                qs = qs.filter(bolsista=user.cadastro)
            else:
                qs = qs.none()

        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_atual'] = self.request.GET.get('status', '')
        user = self.request.user
        context['is_manager'] = user.is_superuser or user.groups.filter(
            name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]
        ).exists()
        return context


class AplicacaoEditalListView(LoginRequiredMixin, ListView):
    model = AplicacaoEdital
    template_name = 'editais/aplicacao_edital_list.html'
    context_object_name = 'aplicacoes'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.edital = get_object_or_404(EditalProvisorio, pk=kwargs['edital_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = AplicacaoEdital.objects.filter(edital=self.edital).select_related(
            'bolsista', 'bolsista__user', 'edital'
        ).order_by('-data_aplicacao')

        user = self.request.user
        is_manager = user.is_superuser or user.groups.filter(
            name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]
        ).exists()

        if not is_manager:
            if hasattr(user, 'cadastro'):
                qs = qs.filter(bolsista=user.cadastro)
            else:
                qs = qs.none()

        status = self.request.GET.get('status', '')
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['edital'] = self.edital
        context['status_choices'] = AplicacaoEdital.STATUS_CHOICES
        context['status_atual'] = self.request.GET.get('status', '')
        user = self.request.user
        context['is_manager'] = user.is_superuser or user.groups.filter(
            name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]
        ).exists()
        return context


class CancelarAplicacaoView(ViewUserRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        if hasattr(request.user, 'cadastro'):
            aplicacao = get_object_or_404(
                AplicacaoEdital,
                pk=kwargs['pk'],
                bolsista=request.user.cadastro,
                status='pendente',
            )
            aplicacao.delete()
            messages.success(request, 'Candidatura cancelada com sucesso.')
        return redirect('aplicacao_list')


class AlterarStatusAplicacaoView(ManagerOrExecuteRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        aplicacao = get_object_or_404(AplicacaoEdital, pk=kwargs['pk'])
        novo_status = request.POST.get('status')

        if novo_status not in dict(AplicacaoEdital.STATUS_CHOICES):
            messages.error(request, 'Status inválido.')
            return redirect('aplicacao_list')

        aplicacao.status = novo_status
        aplicacao.save(update_fields=['status'])
        messages.success(
            request,
            f'Status da candidatura de {aplicacao.bolsista.user.nome_completo} alterado para {aplicacao.get_status_display()}.'
        )

        if request.headers.get('HX-Request'):
            html = render_to_string(
                'editais/partials/aplicacao_row.html',
                {'a': aplicacao},
                request=request,
            )
            return HttpResponse(html)
        return redirect('aplicacao_list')


class AvaliarCandidatoView(ManagerOrExecuteRequiredMixin, TemplateView):
    template_name = 'editais/avaliar_candidato.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aplicacao'] = get_object_or_404(
            AplicacaoEdital.objects.select_related('bolsista__user', 'edital'),
            pk=kwargs['pk'],
        )
        context['feriados_json'] = json.dumps(getattr(settings, 'FERIADOS_NACIONAIS', []))
        return context

    def post(self, request, *args, **kwargs):
        aplicacao = get_object_or_404(
            AplicacaoEdital.objects.select_related('edital'),
            pk=kwargs['pk'],
        )
        nota_str = (request.POST.get('nota', '') or '').strip().replace(',', '.')

        try:
            nota = Decimal(nota_str) if nota_str else Decimal('0')
        except (ValueError, InvalidOperation):
            messages.error(request, 'Nota inválida. Use um número entre 0 e 10.')
            return redirect('avaliar_candidato', pk=aplicacao.pk)

        if nota < 0 or nota > 10:
            messages.error(request, 'Nota deve estar entre 0 e 10.')
            return redirect('avaliar_candidato', pk=aplicacao.pk)

        novo_status = 'aprovado' if nota > 6 else 'rejeitado'

        data_entrevista_str = (request.POST.get('data_entrevista', '') or '').strip()
        data_entrevista = None
        if data_entrevista_str:
            try:
                data_entrevista = datetime.strptime(data_entrevista_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                messages.error(request, 'Data da entrevista inválida.')
                return redirect('avaliar_candidato', pk=aplicacao.pk)

        aplicacao.nota = nota
        aplicacao.status = novo_status
        aplicacao.data_entrevista = data_entrevista
        aplicacao.save(update_fields=['nota', 'status', 'data_entrevista'])

        status_display = 'Apto' if novo_status == 'aprovado' else 'Inapto'
        messages.success(
            request,
            f'{aplicacao.bolsista.user.nome_completo}: nota {nota} — {status_display}.',
        )
        return redirect('edital_candidatos', edital_pk=aplicacao.edital.pk)


def _task_running_partial(request, task_id):
    return render_to_string('editais/partials/task_running.html', {
        'task_id': task_id,
    })


def _render_edital_result(dados):
    if dados.get('erro'):
        return (
            f'<p class="text-danger"><i class="bi bi-exclamation-triangle me-2"></i>'
            f'{dados["erro"]}</p>'
        )

    if 'radar' in dados:
        radar = dados.get('radar', [])
        return render_to_string('editais/partials/analise_edital.html', {
            'resumo': dados.get('resumo', ''),
            'analise': dados.get('analise', ''),
            'radar': radar,
            'radar_labels': json.dumps([item.get('bolsista', '') for item in radar]),
            'radar_scores': json.dumps([item.get('score', 0) for item in radar]),
        })

    return render_to_string('editais/partials/resumo_edital.html', {
        'resumo': dados.get('resumo', ''),
    })


@require_POST
def resumir_edital(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(EditalProvisorio, pk=pk)

    if not settings.IA_ASYNC:
        dados = ia_tasks.resumir_edital_task.run(
            edital_id=pk, user_id=request.user.id
        ) or {}
        return HttpResponse(_render_edital_result(dados), content_type='text/html; charset=utf-8')

    task = ia_tasks.resumir_edital_task.delay(edital_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'edital_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)


@require_POST
def analisar_edital(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(EditalProvisorio, pk=pk)

    if not settings.IA_ASYNC:
        dados = ia_tasks.analisar_edital_task.run(
            edital_id=pk, user_id=request.user.id
        ) or {}
        return HttpResponse(_render_edital_result(dados), content_type='text/html; charset=utf-8')

    task = ia_tasks.analisar_edital_task.delay(edital_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'edital_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)


def edital_task_status(request, task_id):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)
    if cache.get(f'task_owner:{task_id}') != request.user.id:
        return HttpResponse('Não autorizado', status=403)

    result = AsyncResult(task_id)
    if result.status in ('PENDING', 'STARTED', 'RETRY'):
        return _task_running_partial(request, task_id)

    if result.failed():
        return HttpResponse(
            '<p class="text-danger">Ocorreu um erro ao processar a análise. Tente novamente.</p>',
            content_type='text/html; charset=utf-8',
        )

    dados = cache.get(f'task_result:{task_id}') or result.result or {}
    html = _render_edital_result(dados)
    return HttpResponse(html, content_type='text/html; charset=utf-8')
