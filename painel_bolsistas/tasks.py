import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache

from cadastro.models import CadastroBolsista
from classificacao.models import CriterioClassificacao
from editais.models import EditalProvisorio
from notifications.models import Notificacao

from . import ai_service

User = get_user_model()
logger = logging.getLogger(__name__)


def _notificar_conclusao(user_id, bolsista, descricao):
    try:
        usuario = User.objects.get(pk=user_id)
        Notificacao.objects.create(
            destinatario=usuario,
            titulo='Análise por IA concluída',
            mensagem=f'A {descricao} de {bolsista.user.nome_completo} está pronta.',
            tipo='sistema',
        )
    except User.DoesNotExist:
        pass


@shared_task(bind=True, max_retries=2)
def resumir_bolsista_task(self, bolsista_id, user_id):
    try:
        bolsista = CadastroBolsista.objects.select_related('user').get(pk=bolsista_id)
        resultado = ai_service.resumir_bolsista(bolsista)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
        _notificar_conclusao(user_id, bolsista, 'análise resumida do perfil')
        return resultado
    except Exception as exc:
        logger.exception('Erro na task resumir_bolsista')
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=2)
def analisar_bolsista_task(self, bolsista_id, user_id):
    try:
        bolsista = CadastroBolsista.objects.select_related('user').prefetch_related(
            'formacoes', 'experiencias'
        ).get(pk=bolsista_id)
        editais = list(EditalProvisorio.objects.all())
        resultado = ai_service.analisar_bolsista(bolsista, editais)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
        _notificar_conclusao(user_id, bolsista, 'análise comparativa do perfil')
        return resultado
    except Exception as exc:
        logger.exception('Erro na task analisar_bolsista')
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=2)
def sugerir_avaliacao_task(self, bolsista_id, user_id):
    try:
        bolsista = CadastroBolsista.objects.select_related('user').prefetch_related(
            'formacoes', 'experiencias'
        ).get(pk=bolsista_id)
        criterios = CriterioClassificacao.objects.filter(ativo=True).order_by('nome')
        resultado = ai_service.sugerir_avaliacao(bolsista, criterios)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
        _notificar_conclusao(user_id, bolsista, 'sugestão de avaliação')
        return resultado
    except Exception as exc:
        logger.exception('Erro na task sugerir_avaliacao')
        raise self.retry(exc=exc, countdown=10)
