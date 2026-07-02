from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.core.cache import cache
from celery.result import AsyncResult
from decimal import Decimal
import csv
import json

from base.mixins import ManagerOrExecuteRequiredMixin, GROUP_MANAGER, GROUP_EXECUTE_USER
from cadastro.models import CadastroBolsista, FormacaoAcademica
from classificacao.models import CriterioClassificacao, AvaliacaoBolsista
from editais.models import EditalProvisorio
from . import tasks as ia_tasks


class PainelBolsistasListView(ManagerOrExecuteRequiredMixin, ListView):
    model = CadastroBolsista
    template_name = 'painel/lista_bolsistas.html'
    context_object_name = 'bolsistas'
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().select_related('user').prefetch_related('formacoes')
        sort = self.request.GET.get('sort', 'nome')
        edital_id = self.request.GET.get('edital')
        if edital_id:
            qs = qs.filter(aplicacoes__edital_id=edital_id).distinct()
        if sort == 'nome':
            qs = qs.order_by('user__nome_completo')
        else:
            qs = qs.order_by('user__nome_completo')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sort'] = self.request.GET.get('sort', 'nome')
        ctx['edital_id'] = self.request.GET.get('edital', '')
        return ctx


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


def painel_download_csv(request):
    if not request.user.is_authenticated:
        return HttpResponse('Nao autorizado', status=401)

    if not (
        request.user.is_superuser
        or request.user.groups.filter(name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]).exists()
    ):
        return HttpResponse('Nao autorizado', status=401)

    bolsistas = CadastroBolsista.objects.select_related('user').prefetch_related('formacoes').order_by('user__nome_completo')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="candidatos.csv"'

    writer = csv.writer(response)
    writer.writerow(['Nome', 'E-mail', 'Telefone', 'Cidade', 'Estado',
                     'Ultima Formacao', 'Area', 'Ano Conclusao',
                     'Projetos (anos)', 'Congressos', 'Resumo Anais',
                     'Artigo Anais', 'Artigo Nacional', 'Artigo Internacional',
                     'Livro/Patente', 'Minicurso', 'Treinamento',
                     'Pontuacao Previa'])

    for b in bolsistas:
        ultima = b.formacoes.order_by('-ano_conclusao').first()
        writer.writerow([
            b.user.nome_completo,
            b.user.email,
            b.telefone or '',
            b.cidade or '',
            b.estado or '',
            ultima.get_tipo_display() if ultima else '',
            ultima.area if ultima else '',
            ultima.ano_conclusao if ultima else '',
            b.participacao_projetos_anos,
            'Sim' if b.participacao_congressos else 'Nao',
            'Sim' if b.resumo_anais else 'Nao',
            'Sim' if b.artigo_completo_anais else 'Nao',
            'Sim' if b.artigo_cientifico_nacional else 'Nao',
            'Sim' if b.artigo_cientifico_internacional else 'Nao',
            'Sim' if b.livro_patente else 'Nao',
            'Sim' if b.participacao_minicurso else 'Nao',
            'Sim' if b.treinamento else 'Nao',
            str(b.pontuacao_previa),
        ])

    return response


def _pode_usar_ia(request):
    return request.user.is_authenticated and (
        request.user.is_superuser
        or request.user.groups.filter(name__in=[GROUP_MANAGER, GROUP_EXECUTE_USER]).exists()
    )


def _task_running_partial(request, task_id):
    return render_to_string('painel/partials/task_running.html', {
        'task_id': task_id,
    })


@require_POST
def resumir_bolsista(request, pk):
    if not _pode_usar_ia(request):
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(CadastroBolsista, pk=pk)
    task = ia_tasks.resumir_bolsista_task.delay(bolsista_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'bolsista_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)


@require_POST
def analisar_bolsista(request, pk):
    if not _pode_usar_ia(request):
        return HttpResponse('Não autorizado', status=401)

    get_object_or_404(CadastroBolsista, pk=pk)
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
        return _task_running_partial(request, task_id, 'painel_task_status')

    if result.failed():
        return HttpResponse(
            '<p class="text-danger">Ocorreu um erro ao processar a análise. Tente novamente.</p>',
            content_type='text/html; charset=utf-8',
        )

    dados = cache.get(f'task_result:{task_id}') or result.result or {}
    context = cache.get(f'task_context:{task_id}') or {}
    bolsista_id = context.get('bolsista_id')
    bolsista = get_object_or_404(CadastroBolsista, pk=bolsista_id) if bolsista_id else None

    if 'sugestoes' in dados:
        html = render_to_string('painel/partials/sugestao_avaliacao.html', {
            'bolsista': bolsista,
            'resumo': dados.get('resumo', ''),
            'sugestoes': dados.get('sugestoes', []),
            'sugestoes_json': json.dumps(dados.get('sugestoes', []), default=str),
            'total_sugerido': str(sum(s.get('pontos', 0) for s in dados.get('sugestoes', []))),
            'criterios': list(CriterioClassificacao.objects.filter(ativo=True).order_by('nome')),
        })
    elif 'radar' in dados:
        radar = dados.get('radar', [])
        html = render_to_string('painel/partials/analise_bolsista.html', {
            'resumo': dados.get('resumo', ''),
            'analise': dados.get('analise', ''),
            'radar': radar,
            'radar_labels': json.dumps([item.get('edital', '') for item in radar]),
            'radar_scores': json.dumps([item.get('score', 0) for item in radar]),
        })
    else:
        html = render_to_string('painel/partials/resumo_bolsista.html', {
            'resumo': dados.get('resumo', ''),
        })

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

        return redirect('painel_lista')

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
    task = ia_tasks.sugerir_avaliacao_task.delay(bolsista_id=pk, user_id=request.user.id)
    cache.set(f'task_owner:{task.id}', request.user.id, timeout=3600)
    cache.set(f'task_context:{task.id}', {'bolsista_id': pk}, timeout=3600)
    return _task_running_partial(request, task.id)
