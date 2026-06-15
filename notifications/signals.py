from django.db.models.signals import post_save
from django.dispatch import receiver

from cadastro.models import CadastroBolsista, SolicitacaoEdicao
from accounts.models import User
from classificacao.models import Classificacao
from .models import Notificacao


@receiver(post_save, sender=CadastroBolsista)
def notificar_cadastro(sender, instance, created, **kwargs):
    if created:
        Notificacao.objects.create(
            destinatario=instance.user,
            titulo='Cadastro realizado',
            mensagem='Seu cadastro de bolsista foi criado com sucesso.',
            tipo='cadastro',
            tenant=instance.tenant,
        )


@receiver(post_save, sender=Classificacao)
def notificar_classificacao(sender, instance, **kwargs):
    if instance.pontuacao_total > 0:
        bolsista = instance.aplicacao.bolsista.user
        edital = instance.aplicacao.edital.nome
        Notificacao.objects.create(
            destinatario=bolsista,
            titulo='Classificação publicada',
            mensagem=f'Sua classificação no edital "{edital}" foi publicada. '
                     f'Pontuação total: {instance.pontuacao_total} pts.',
            tipo='classificacao',
            tenant=instance.tenant,
        )


@receiver(post_save, sender=SolicitacaoEdicao)
def notificar_solicitacao(sender, instance, created, **kwargs):
    if created and instance.status == 'pendente':
        gestores = User.objects.filter(
            perfil__tenant=instance.tenant,
            perfil__tipo__in=['ADMIN', 'MANAGER'],
            is_active=True,
        )
        for gestor in gestores:
            Notificacao.objects.create(
                destinatario=gestor,
                titulo='Nova solicitação de edição',
                mensagem=f'{instance.bolsista.user.nome_completo} solicitou edição do campo "{instance.campo}".',
                tipo='solicitacao',
                tenant=instance.tenant,
            )

    elif instance.status == 'aprovado':
        Notificacao.objects.create(
            destinatario=instance.bolsista.user,
            titulo='Solicitação aprovada',
            mensagem=f'Sua solicitação de edição do campo "{instance.campo}" foi aprovada.',
            tipo='solicitacao',
            tenant=instance.tenant,
        )
    elif instance.status == 'rejeitado':
        Notificacao.objects.create(
            destinatario=instance.bolsista.user,
            titulo='Solicitação rejeitada',
            mensagem=f'Sua solicitação de edição do campo "{instance.campo}" foi rejeitada.',
            tipo='solicitacao',
            tenant=instance.tenant,
        )
