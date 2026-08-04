import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache

from cadastro.models import CadastroBolsista
from editais.models import EditalProvisorio

from . import ai_service

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def resumir_bolsista_task(self, bolsista_id, user_id):
    try:
        bolsista = CadastroBolsista.objects.select_related('user').get(pk=bolsista_id)
        resultado = ai_service.resumir_bolsista(bolsista)
        cache.set(f'task_result:{self.request.id}', resultado, timeout=3600)
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
        return resultado
    except Exception as exc:
        logger.exception('Erro na task analisar_bolsista')
        raise self.retry(exc=exc, countdown=10)
