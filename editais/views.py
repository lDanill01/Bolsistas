from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
from .forms import EditalProvisorioForm, CronogramaEventoFormSet
from . import tasks as ia_tasks
from .ai_service import _score_heuristico


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
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(prefix='cronograma')
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        if cronograma_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.criado_por = self.request.user
            self.object.responsavel = self.request.user
            self.object.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
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
        else:
            context['cronograma_formset'] = CronogramaEventoFormSet(
                instance=self.object, prefix='cronograma'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        cronograma_formset = context['cronograma_formset']
        if cronograma_formset.is_valid():
            self.object = form.save()
            cronograma_formset.instance = self.object
            cronograma_formset.save()
            messages.success(self.request, 'Edital atualizado com sucesso!')
            return redirect(self.get_success_url())
        return self.render_to_response(context)


class EditalProvisorioDetailView(LoginRequiredMixin, ContextMixin, DetailView):
    model = EditalProvisorio
    template_name = 'editais/edital_detail.html'
    context_object_name = 'edital'

    CORES_EVENTOS = [
        '#0d6efd',  # azul
        '#198754',  # verde
        '#dc3545',  # vermelho
        '#fd7e14',  # laranja
        '#6f42c1',  # roxo
        '#0dcaf0',  # ciano
        '#d63384',  # rosa
    ]

    def get_queryset(self):
        return EditalProvisorio.objects.all().select_related('criado_por')

    def _montar_cores_cronograma(self, cronograma):
        cores = {}
        idx = 0
        for evento in cronograma:
            if evento.evento not in cores:
                cores[evento.evento] = self.CORES_EVENTOS[idx % len(self.CORES_EVENTOS)]
                idx += 1
        return cores

    def _montar_calendarios(self, cronograma):
        if not cronograma:
            return []
        datas = [e.data_evento for e in cronograma if e.data_evento]
        if not datas:
            return []
        data_inicio = min(datas).replace(day=1)
        data_fim = max(datas)
        calendarios = []
        atual = data_inicio
        while atual <= data_fim:
            calendarios.append(self._montar_mes(atual, cronograma))
            if atual.month == 12:
                atual = atual.replace(year=atual.year + 1, month=1, day=1)
            else:
                atual = atual.replace(month=atual.month + 1, day=1)
        return calendarios

    def _montar_mes(self, data_referencia, cronograma):
        import calendar
        cal = calendar.Calendar(firstweekday=6)  # domingo como primeiro dia
        dias_mes = cal.monthdayscalendar(data_referencia.year, data_referencia.month)

        eventos_por_dia = {}
        for evento in cronograma:
            if evento.data_evento and evento.data_evento.year == data_referencia.year and evento.data_evento.month == data_referencia.month:
                eventos_por_dia.setdefault(evento.data_evento.day, []).append(evento)

        semanas = []
        for semana in dias_mes:
            dias = []
            for dia in semana:
                if dia == 0:
                    dias.append(None)
                else:
                    dias.append({
                        'dia': dia,
                        'eventos': eventos_por_dia.get(dia, []),
                    })
            semanas.append(dias)

        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return {
            'nome_mes': f"{meses[data_referencia.month - 1]} {data_referencia.year}",
            'semanas': semanas,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cronograma = list(self.object.cronograma.all())
        context['cronograma'] = cronograma
        context['cronograma_cores'] = self._montar_cores_cronograma(cronograma)
        context['calendarios'] = self._montar_calendarios(cronograma)
        user = self.request.user
        context['is_superuser'] = user.is_superuser
        context['is_manager'] = user.groups.filter(name=GROUP_MANAGER).exists()
        context['is_execute_user'] = user.groups.filter(name=GROUP_EXECUTE_USER).exists()
        context['tem_cadastro'] = hasattr(user, 'cadastro')
        context['is_view_user'] = user.groups.filter(name=GROUP_VIEW_USER).exists()
        if hasattr(user, 'cadastro'):
            context['ja_aplicou'] = AplicacaoEdital.objects.filter(
                bolsista=user.cadastro, edital=self.object
            ).exists()
        else:
            context['ja_aplicou'] = False
        return context


class EditalProvisorioDeleteView(UserPassesTestMixin, ContextMixin, DeleteView):
    model = EditalProvisorio
    template_name = 'editais/edital_confirm_delete.html'
    success_url = reverse_lazy('edital_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        messages.success(self.request, 'Edital removido com sucesso!')
        return super().form_valid(form)


def validar_edital(request, pk):
    if not request.user.is_superuser and not request.user.groups.filter(name=GROUP_MANAGER).exists():
        messages.error(request, 'Você não tem permissão para validar editais.')
        return redirect('edital_list')

    edital = get_object_or_404(EditalProvisorio, pk=pk)
    if edital.status != 'em_analise':
        messages.warning(request, 'Este edital já foi validado ou não pode ser validado.')
        return redirect('edital_detail', pk=pk)

    edital.status = 'aberto'
    edital.save()
    messages.success(request, f'Edital "{edital}" validado e aberto com sucesso!')
    return redirect('edital_detail', pk=pk)


def edital_pdf_view(request, pk):
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    edital = get_object_or_404(
        EditalProvisorio.objects.select_related('criado_por').prefetch_related('cronograma'),
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


@require_POST
def minha_compatibilidade(request, pk):
    """Retorna resumo IA do edital + % de compatibilidade do ViewUser logado."""
    if not request.user.is_authenticated:
        return HttpResponse('Não autorizado', status=401)

    edital = get_object_or_404(EditalProvisorio, pk=pk)

    # Apenas ViewUser com cadastro
    is_view = request.user.groups.filter(name=GROUP_VIEW_USER).exists()
    if not is_view or not hasattr(request.user, 'cadastro'):
        return HttpResponse('Acesso restrito a candidatos com cadastro', status=403)

    bolsista = request.user.cadastro

    # Gera resumo do edital via IA
    from . import ai_service
    dados_resumo = ai_service.resumir_edital(edital)
    resumo = dados_resumo.get('resumo', 'Resumo não disponível.')

    # Calcula compatibilidade heurística (0-100)
    score = _score_heuristico(bolsista, edital)

    # Define cor e label com base no score
    if score >= 70:
        cor_barra = 'success'
        label_nivel = 'Alta compatibilidade'
    elif score >= 40:
        cor_barra = 'warning'
        label_nivel = 'Média compatibilidade'
    else:
        cor_barra = 'danger'
        label_nivel = 'Baixa compatibilidade'

    html = render_to_string('editais/partials/compatibilidade_viewuser.html', {
        'resumo': resumo,
        'score': score,
        'cor_barra': cor_barra,
        'label_nivel': label_nivel,
        'edital': edital,
    })
    return HttpResponse(html, content_type='text/html; charset=utf-8')


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
