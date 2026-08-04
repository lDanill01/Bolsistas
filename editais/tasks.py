import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache

from cadastro.models import CadastroBolsista
from notifications.models import Notificacao

from . import ai_service
from .models import EditalProvisorio

User = get_user_model()
logger = logging.getLogger(__name__)


def _notificar_conclusao(user_id, edital, descricao):
    try:
        usuario = User.objects.get(pk=user_id)
        Notificacao.objects.create(
            destinatario=usuario,
            titulo='Análise por IA concluída',
            mensagem=f'A {descricao} "{edital.nome_edital or edital}" está pronta.',
            tipo='sistema',
        )
    except User.DoesNotExist:
        pass


@shared_task(bind=True, max_retries=2)
def resumir_edital_task(self, edital_id, user_id):
    try:
        edital = EditalProvisorio.objects.prefetch_related(
            'cronograma'
        ).get(pk=edital_id)
        resultado = ai_service.resumir_edital(edital)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
        _notificar_conclusao(user_id, edital, 'análise resumida do edital')
        return resultado
    except Exception as exc:
        logger.exception('Erro na task resumir_edital')
        raise self.retry(exc=exc, countdown=10)


@shared_task(bind=True, max_retries=2)
def analisar_edital_task(self, edital_id, user_id):
    try:
        edital = EditalProvisorio.objects.prefetch_related(
            'cronograma'
        ).get(pk=edital_id)
        bolsistas = list(
            CadastroBolsista.objects.select_related('user').prefetch_related('formacoes')
        )
        resultado = ai_service.analisar_edital(edital, bolsistas)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
        _notificar_conclusao(user_id, edital, 'análise comparativa do edital')
        return resultado
    except Exception as exc:
        logger.exception('Erro na task analisar_edital')
        raise self.retry(exc=exc, countdown=10)


@shared_task
def fechar_editais_vencidos():
    """Fecha automaticamente editais abertos cuja última etapa do cronograma já passou."""
    fechados = 0
    for edital in EditalProvisorio.objects.filter(status='aberto').prefetch_related('cronograma'):
        if edital.processo_concluido:
            edital.status = 'encerrado'
            edital.save(update_fields=['status'])
            fechados += 1
            logger.info('Edital %s (%s) fechado automaticamente.', edital.pk, edital.nome_edital)
    return fechados
