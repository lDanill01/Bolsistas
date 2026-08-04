from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.cache import cache
from celery.result import AsyncResult
from decimal import Decimal
import json

from django.conf import settings

from base.mixins import ManagerOrExecuteRequiredMixin, GROUP_MANAGER, GROUP_EXECUTE_USER
from cadastro.models import CadastroBolsista, FormacaoAcademica
from classificacao.models import CriterioClassificacao, AvaliacaoBolsista
from editais.models import EditalProvisorio
from . import tasks as ia_tasks


class PainelBolsistaDetailView(ManagerOrExecuteRequiredMixin, DetailView):
    model = CadastroBolsista
    template_name = 'painel/detalhe_bolsista.html'
    context_object_name = 'bolsista'

    def get_queryset(self):
        return super().get_queryset().select_related('user').prefetch_related('formacoes')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['formacoes'] = self.object.formacoes.order_by('-ano_conclusao')
        return ctx


def _pode_usar_ia(request):
    return request.user.is_authenticated and (
        request.user.is_superuser
        or request.user.groups.filter(name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]).exists()
    )


def _task_running_partial(request, task_id):
    return render_to_string('painel/partials/task_running.html', {
        'task_id': task_id,
    })


class TrilhaBolsistaView(ManagerOrExecuteRequiredMixin, ListView):
    """Pagina 'Trilha do Bolsista' — historico completo de cada candidato:
    aplicacoes, status, notas, avaliacoes, pontuacoes."""
    model = CadastroBolsista
    template_name = 'painel/trilha_bolsistas.html'
    context_object_name = 'bolsistas'
    paginate_by = 15

    def get_queryset(self):
        return (
            CadastroBolsista.objects
            .select_related('user')
            .prefetch_related(
                'aplicacoes__edital',
                'avaliacoes__criterio',
                'avaliacoes__avaliado_por',
                'formacoes',
            )
            .order_by('user__nome_completo')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Para cada bolsista, anexa dados agregados
        for bolsista in ctx['bolsistas']:
            apps = list(bolsista.aplicacoes.all())
            bolsista.total_aplicacoes = len(apps)
            bolsista.total_aprovado = sum(1 for a in apps if a.status == 'aprovado')
            bolsista.total_rejeitado = sum(1 for a in apps if a.status == 'rejeitado')
            bolsista.total_em_analise = sum(1 for a in apps if a.status == 'em_analise')
            bolsista.total_pendente = sum(1 for a in apps if a.status == 'pendente')
            avals = list(bolsista.avaliacoes.all())
            bolsista.total_avaliacoes = len(avals)
            bolsista.pontuacao_total = sum(a.pontos for a in avals)
            bolsista.formacao_principal = (
                bolsista.formacoes.order_by('-ano_conclusao').first()
            )
        return ctx


def _render_bolsista_result(dados, bolsista_id=None):
    if dados.get('erro'):
        return (
            f'<p class="text-danger"><i class="bi bi-exclamation-triangle me-2"></i>'
            f'{dados["erro"]}</p>'
        )

    bolsista = None
    if bolsista_id:
        bolsista = get_object_or_404(CadastroBolsista, pk=bolsista_id)

    if 'sugestoes' in dados:
        return render_to_string('painel/partials/sugestao_avaliacao.html', {
            'bolsista': bolsista,
            'resumo': dados.get('resumo', ''),
            'sugestoes': dados.get('sugestoes', []),
            'sugestoes_json': json.dumps(dados.get('sugestoes', []), default=str),
            'total_sugerido': str(sum(s.get('pontos', 0) for s in dados.get('sugestoes', []))),
            'criterios': list(CriterioClassificacao.objects.filter(ativo=True).order_by('nome')),
        })

    if 'radar' in dados:
        radar = dados.get('radar', [])
        return render_to_string('painel/partials/analise_bolsista.html', {
            'resumo': dados.get('resumo', ''),
            'analise': dados.get('analise', ''),
            'radar': radar,
            'radar_labels': json.dumps([item.get('edital', '') for item in radar]),
            'radar_scores': json.dumps([item.get('score', 0) for item in radar]),
        })

    return render_to_string('painel/partials/resumo_bolsista.html', {
        'resumo': dados.get('resumo', ''),
    })


@require_POST
def resumir_bolsista(request, pk):
    if not _pode_usar_ia(request):
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(CadastroBolsista, pk=pk)

    if not settings.IA_ASYNC:
        dados = ia_tasks.resumir_bolsista_task.run(
            bolsista_id=pk, user_id=request.user.id
        ) or {}
        return HttpResponse(_render_bolsista_result(dados, pk), content_type='text/html; charset=utf-8')

    task = ia_tasks.resumir_bolsista_task.delay(bolsista_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'bolsista_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)


@require_POST
def analisar_bolsista(request, pk):
    if not _pode_usar_ia(request):
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(CadastroBolsista, pk=pk)

    if not settings.IA_ASYNC:
        dados = ia_tasks.analisar_bolsista_task.run(
            bolsista_id=pk, user_id=request.user.id
        ) or {}
        return HttpResponse(_render_bolsista_result(dados, pk), content_type='text/html; charset=utf-8')

    task = ia_tasks.analisar_bolsista_task.delay(bolsista_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'bolsista_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)


def painel_task_status(request, task_id):
    if not _pode_usar_ia(request):
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
    context = cache.get(f'task_context:{task_id}') or {}
    bolsista_id = context.get('bolsista_id')

    html = _render_bolsista_result(dados, bolsista_id)
    return HttpResponse(html, content_type='text/html; charset=utf-8')


def avaliar_bolsista(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    if not (
        request.user.is_superuser
        or request.user.groups.filter(name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]).exists()
    ):
        return HttpResponse('Não autorizado', status=401)

    bolsista = get_object_or_404(
        CadastroBolsista.objects.select_related('user').prefetch_related('formacoes'),
        pk=pk,
    )

    criterios = CriterioClassificacao.objects.filter(ativo=True).order_by('nome')

    if request.method == 'POST':
        total = Decimal('0')
        for criterio in criterios:
            pontos_str = request.POST.get(f'criterio_{criterio.pk}', '0')
            try:
                pontos = Decimal(pontos_str.replace(',', '.'))
            except Exception:
                pontos = Decimal('0')

            pontos = max(Decimal('0'), pontos)
            if criterio.peso_maximo > 0:
                pontos = min(pontos, criterio.peso_maximo)

            AvaliacaoBolsista.objects.update_or_create(
                bolsista=bolsista,
                criterio=criterio,
                defaults={
                    'pontos': pontos,
                    'avaliado_por': request.user,
                },
            )
            total += pontos

        bolsista.pontuacao_previa = total
        bolsista.save(update_fields=['pontuacao_previa'])

        return redirect('painel_trilha')

    avaliacoes_existentes = {
        a.criterio_id: a.pontos
        for a in AvaliacaoBolsista.objects.filter(bolsista=bolsista)
    }

    itens = []
    for criterio in criterios:
        pontos_default = avaliacoes_existentes.get(criterio.pk)
        if pontos_default is None:
            pontos_default = criterio.peso
        itens.append({
            'criterio': criterio,
            'pontos': pontos_default,
        })

    return render(request, 'painel/avaliar_bolsista.html', {
        'bolsista': bolsista,
        'formacoes': bolsista.formacoes.order_by('-ano_conclusao'),
        'itens': itens,
    })


@require_POST
def sugerir_avaliacao_bolsista(request, pk):
    if not _pode_usar_ia(request):
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(CadastroBolsista, pk=pk)

    if not settings.IA_ASYNC:
        dados = ia_tasks.sugerir_avaliacao_task.run(
            bolsista_id=pk, user_id=request.user.id
        ) or {}
        return HttpResponse(_render_bolsista_result(dados, pk), content_type='text/html; charset=utf-8')

    task = ia_tasks.sugerir_avaliacao_task.delay(bolsista_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'bolsista_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)
