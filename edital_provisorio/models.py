from django.db import models
from base.models import DataModel
from base.managers import TenantManager
from accounts.models import User, Tenant


class EditalProvisorio(DataModel):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('publicado', 'Publicado'),
        ('encerrado', 'Encerrado'),
    ]

    MODALIDADE_CHOICES = [
        ('bolsa_mestrado', 'Bolsa de Mestrado'),
        ('bolsa_doutorado', 'Bolsa de Doutorado'),
        ('bolsa_pos_doutorado', 'Bolsa de Pós-Doutorado'),
        ('bolsa_ic', 'Bolsa de Iniciação Científica'),
        ('bolsa_extensao', 'Bolsa de Extensão'),
        ('bolsa_desenvolvimento', 'Bolsa de Desenvolvimento Tecnológico'),
        ('bolsa_aperfeicoamento', 'Bolsa de Aperfeiçoamento'),
    ]

    EVENTO_CHOICES = [
        ('inicio_submissao', 'Início da submissão das candidaturas'),
        ('limite_submissao', 'Data limite para submissão das candidaturas'),
        ('resultado_aptas', 'Resultado das candidaturas aptas (análise documental/curricular)'),
        ('prova_teorica', 'Prova teórica'),
        ('resultado_prova', 'Resultado da prova teórica'),
        ('envio_documentacao', 'Envio da Documentação Comprobatória'),
        ('entrevista', 'Entrevista'),
        ('resultado_final', 'Divulgação do Resultado Final'),
        ('outorga', 'Outorga das bolsas'),
    ]

    nome_instituto = models.CharField('Nome do Instituto', max_length=255)
    email_solicitante = models.EmailField('E-mail do Solicitante')
    telefone = models.CharField('Telefone', max_length=20)
    endereco = models.TextField('Endereço')

    numero_vagas = models.PositiveIntegerField('Número de Vagas')
    modalidade_bolsa = models.CharField('Modalidade da Bolsa', max_length=50, choices=MODALIDADE_CHOICES)
    plataforma_tecnologica = models.CharField('Plataforma Tecnológica', max_length=255)
    vigencia = models.CharField('Vigência', max_length=255)
    endereco_atuacao = models.TextField('Endereço de Atuação')

    qualificacao_minima = models.TextField('Qualificação Mínima')
    experiencia_minima = models.TextField('Experiência Mínima (Profissional/Acadêmica)')
    conhecimento_desejavel = models.TextField('Conhecimento Desejável', blank=True, default='')
    conteudo_prova_teorica = models.TextField('Conteúdo da Prova Teórica')
    entrevista = models.TextField('Entrevista')
    criterios_desempate = models.TextField('Critérios de Desempate')

    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='rascunho')
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='editais_provisorios_criados')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='editais_provisorios')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Edital Provisório'
        verbose_name_plural = 'Editais Provisórios'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nome_instituto} - {self.get_modalidade_bolsa_display()}'

    @property
    def total_eventos(self):
        return self.cronograma.count()


class CronogramaEvento(DataModel):
    edital = models.ForeignKey(EditalProvisorio, on_delete=models.CASCADE, related_name='cronograma')
    evento = models.CharField('Evento', max_length=50, choices=EditalProvisorio.EVENTO_CHOICES)
    data_referencia = models.CharField('Data de Referência', max_length=255)
    observacao = models.TextField('Observação', blank=True, default='')
    ordem = models.PositiveIntegerField('Ordem', default=0)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='cronogramas_provisorios')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Evento do Cronograma'
        verbose_name_plural = 'Eventos do Cronograma'
        ordering = ['ordem']

    def __str__(self):
        return f'{self.get_evento_display()} - {self.data_referencia}'
