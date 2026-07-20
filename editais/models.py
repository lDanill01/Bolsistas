from django.db import models
from django.utils import timezone
from base.models import DataModel
from base.utils import gerar_numero_serie, dias_uteis_entre, adicionar_dias_uteis, proximo_dia_util, proximo_dia_1_ou_15
from accounts.models import User
from cadastro.models import CadastroBolsista


NIVEL_BOLSA_CONFIG = {
    'nivel_1': {
        'qualificacao': [
            ('Ensino Médio', 'Ensino Médio'),
            ('Profissionalizante', 'Profissionalizante'),
            ('Técnico', 'Técnico'),
            ('Graduação em Andamento', 'Graduação em Andamento'),
        ],
        'experiencia': [
            ('Sem Experiência', 'Sem Experiência'),
        ],
        'valor_minimo': 500.00,
        'valor_maximo': 2000.00,
    },
    'nivel_2': {
        'qualificacao': [
            ('Graduação Completa', 'Graduação Completa'),
            ('Tecnólogo', 'Tecnólogo'),
            ('Curso Técnico Completo', 'Curso Técnico Completo'),
        ],
        'experiencia': [
            ('Sem Experiência', 'Sem Experiência'),
            ('1 Ano de Experiência', '1 Ano de Experiência'),
            ('2 Anos ou mais', '2 Anos ou mais'),
        ],
        'experiencia_valores': {
            'Sem Experiência': (2500.00, 4000.00),
            '1 Ano de Experiência': (4500.00, 6500.00),
            '2 Anos ou mais': (7000.00, 10000.00),
        },
    },
    'nivel_3': {
        'qualificacao': [
            ('Mestrado Concluído', 'Mestrado Concluído'),
        ],
        'experiencia': [
            ('Sem Experiência', 'Sem Experiência'),
            ('1 Ano de Experiência', '1 Ano de Experiência'),
            ('2 Anos ou mais', '2 Anos ou mais'),
        ],
        'experiencia_valores': {
            'Sem Experiência': (4500.00, 6000.00),
            '1 Ano de Experiência': (6500.00, 8500.00),
            '2 Anos ou mais': (9000.00, 12000.00),
        },
    },
    'nivel_4': {
        'qualificacao': [
            ('Doutorado Concluído', 'Doutorado Concluído'),
        ],
        'experiencia': [
            ('Sem Experiência', 'Sem Experiência'),
            ('1 Ano de Experiência', '1 Ano de Experiência'),
            ('2 Anos ou mais', '2 Anos ou mais'),
        ],
        'experiencia_valores': {
            'Sem Experiência': (6500.00, 8000.00),
            '1 Ano de Experiência': (8500.00, 10500.00),
            '2 Anos ou mais': (11000.00, 14000.00),
        },
    },
}


class EditalProvisorio(DataModel):
    STATUS_CHOICES = [
        ('em_analise', 'Em Análise'),
        ('aberto', 'Aberto'),
        ('encerrado', 'Encerrado'),
        ('cancelado', 'Cancelado'),
    ]

    MODALIDADE_CHOICES = [
        ('nivel_1', 'Nível 1'),
        ('nivel_2', 'Nível 2'),
        ('nivel_3', 'Nível 3'),
        ('nivel_4', 'Nível 4'),
    ]

    MODALIDADE_ATUACAO_CHOICES = [
        ('presencial', 'Presencial'),
        ('remota', 'Remota'),
    ]

    EXPERIENCIA_CHOICES = [
        ('Sem Experiência', 'Sem Experiência'),
        ('1 Ano de Experiência', '1 Ano de Experiência'),
        ('2 Anos ou mais', '2 Anos ou mais'),
    ]

    MODALIDADE_ENTREVISTA_CHOICES = [
        ('presencial', 'Presencial'),
        ('online', 'Online'),
    ]

    INSTITUTOS_CHOICES = [
        ('isi_biomassa',            'ISI Biomassa - Três Lagoas'),
        ('ist_alimentos',           'IST Alimentos e Bebidas - Dourados'),
        ('ist_eficiencia',          'IST Eficiência Operacional - Campo Grande'),
        ('ist_construcao',          'Faculdade da Construção - Campo Grande'),
    ]

    EVENTO_CHOICES = [
        ('inicio_submissao',        'Início da submissão das candidaturas'),
        ('limite_submissao',        'Data limite para submissão das candidaturas'),
        ('resultado_aptas',         'Resultado das candidaturas aptas (análise documental/curricular)'),
        ('prova_teorica',           'Prova teórica'),
        ('entrevista',              'Entrevista'),
        ('resultado_final',         'Divulgação do Resultado Final'),
        ('outorga',                 'Outorga das bolsas'),
    ]

    nome_edital                     = models.CharField('Nome do Edital', max_length=255, default='')
    area_estudo                     = models.CharField('Área de Estudo', max_length=255, default='')
    detalhes_edital                 = models.TextField('Detalhes do Edital', blank=True, default='')
    nome_instituto                  = models.CharField('Nome do Instituto', max_length=255, choices=INSTITUTOS_CHOICES, help_text='Selecione o Instituto')
    email_solicitante               = models.EmailField('E-mail do Solicitante', help_text='Insira o seu e-mail')
    telefone                        = models.CharField('Telefone', max_length=20)
    endereco                        = models.TextField('Endereço')
    documento_anexo                 = models.FileField('Termo de Parceria e/ou Plano de Projeto (PDF)', upload_to='editais/', blank=True)

    numero_vagas                    = models.PositiveIntegerField('Número de Vagas')
    modalidade_bolsa                = models.CharField('Modalidade da Bolsa', max_length=50, choices=MODALIDADE_CHOICES)
    experiencia                     = models.CharField('Experiência', max_length=50, choices=EXPERIENCIA_CHOICES, blank=True, default='')
    valor_bolsa                     = models.DecimalField('Valor da Bolsa (R$)', max_digits=10, decimal_places=2, default=0)
    valor_total_bolsa               = models.DecimalField('Valor Total da Bolsa (R$)', max_digits=12, decimal_places=2, default=0)
    valor_minimo                    = models.DecimalField('Valor Mínimo (R$)', max_digits=10, decimal_places=2, default=0)
    valor_maximo                    = models.DecimalField('Valor Máximo (R$)', max_digits=10, decimal_places=2, default=0)
    modalidade_atuacao              = models.CharField('Modalidade de Atuação', max_length=50, choices=MODALIDADE_ATUACAO_CHOICES, default='presencial')
    plataforma_tecnologica          = models.CharField('Plataforma Tecnológica', max_length=255)
    vigencia                        = models.PositiveIntegerField('Vigência (dias)', help_text='Mínimo: 15 dias. Máximo: 36 meses (1095 dias).', default=180)
    endereco_atuacao                = models.TextField('Endereço de Atuação', blank=True, default='')

    qualificacao_minima             = models.CharField('Qualificação Mínima', max_length=255)
    detalhes_qualificacao_minima    = models.CharField('Qualificação Mínima em:', max_length=255, blank=True, default='')
    conhecimento_desejavel          = models.TextField('Conhecimento Desejável', blank=True, default='')
    conteudo_prova_teorica          = models.TextField('Conteúdo da Prova Teórica', blank=True, default='')
    modalidade_entrevista           = models.CharField('Modalidade da Entrevista', max_length=20, choices=MODALIDADE_ENTREVISTA_CHOICES, default='presencial')
    criterios_desempate             = models.TextField('Critérios de Desempate', blank=True, default='')
    comentarios                     = models.TextField('Comentários', blank=True, default='')

    numero_serie                    = models.CharField('Número de Série', max_length=4, unique=True, blank=True)
    status                          = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='em_analise')
    criado_por                      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='editais_criados')
    responsavel                     = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='editais_responsavel', verbose_name='Responsável')

    class Meta:
        verbose_name = 'Edital'
        verbose_name_plural = 'Editais'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nome_instituto} - {self.get_modalidade_bolsa_display()}'

    def save(self, *args, **kwargs):
        if not self.numero_serie:
            self.numero_serie = gerar_numero_serie(EditalProvisorio)
        status_anterior = None
        if self.pk:
            try:
                anterior = EditalProvisorio.objects.get(pk=self.pk)
                status_anterior = anterior.status
            except EditalProvisorio.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if status_anterior == 'em_analise' and self.status == 'aberto':
            self.calcular_cronograma()

    EVENTOS_ORDEM = {
        'inicio_submissao': 0,
        'limite_submissao': 1,
        'resultado_aptas': 2,
        'prova_teorica': 3,
        'entrevista': 4,
        'resultado_final': 5,
        'outorga': 6,
    }

    def calcular_cronograma(self):
        data_inicio = proximo_dia_util(timezone.now().date())
        limite = adicionar_dias_uteis(data_inicio, 7)
        resultado_aptas = adicionar_dias_uteis(limite, 1)
        prova_teorica = adicionar_dias_uteis(resultado_aptas, 1)
        entrevista = adicionar_dias_uteis(prova_teorica, 1)
        resultado_final = adicionar_dias_uteis(entrevista, 1)
        base_outorga = adicionar_dias_uteis(data_inicio, 20)
        outorga = proximo_dia_1_ou_15(base_outorga)

        datas = {
            'inicio_submissao': data_inicio,
            'limite_submissao': limite,
            'resultado_aptas': resultado_aptas,
            'prova_teorica': prova_teorica,
            'entrevista': entrevista,
            'resultado_final': resultado_final,
            'outorga': outorga,
        }
        for evento_codigo, data_val in datas.items():
            CronogramaEvento.objects.update_or_create(
                edital=self,
                evento=evento_codigo,
                defaults={
                    'data_evento': data_val,
                    'ordem': self.EVENTOS_ORDEM[evento_codigo],
                },
            )

    @property
    def vigencia_meses(self):
        return max(1, self.vigencia // 30)

    @property
    def total_eventos(self):
        return self.cronograma.count()

    @property
    def total_inscritos(self):
        return self.aplicacoes.count()

    @property
    def data_final(self):
        evento = self.cronograma.filter(
            evento='outorga', data_evento__isnull=False
        ).order_by('data_evento').last()
        return evento.data_evento if evento else None

    @property
    def proxima_etapa(self):
        if self.status != 'aberto':
            return None
        hoje = timezone.now().date()
        evento = self.cronograma.filter(
            data_evento__gte=hoje
        ).order_by('data_evento').first()
        return evento if evento else None

    @property
    def dias_para_proxima_etapa(self):
        prox = self.proxima_etapa
        if not prox or not prox.data_evento:
            return None
        hoje = timezone.now().date()
        return dias_uteis_entre(hoje, prox.data_evento)

    @property
    def nome_proxima_etapa(self):
        prox = self.proxima_etapa
        return prox.get_evento_display() if prox else None


class CronogramaEvento(DataModel):
    edital = models.ForeignKey(EditalProvisorio, on_delete=models.CASCADE, related_name='cronograma')
    evento = models.CharField('Evento', max_length=50, choices=EditalProvisorio.EVENTO_CHOICES)
    data_evento = models.DateField('Data do Evento')
    observacao = models.TextField('Observação', blank=True, default='')
    ordem = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        verbose_name = 'Evento do Cronograma'
        verbose_name_plural = 'Eventos do Cronograma'
        ordering = ['ordem']

    def __str__(self):
        return f'{self.get_evento_display()} - {self.data_evento}'


class AplicacaoEdital(DataModel):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    bolsista = models.ForeignKey(CadastroBolsista, on_delete=models.CASCADE, related_name='aplicacoes')
    edital = models.ForeignKey(EditalProvisorio, on_delete=models.CASCADE, related_name='aplicacoes')
    numero_inscricao = models.CharField('Número de Inscrição', max_length=10, unique=True, blank=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pendente')
    nota = models.DecimalField('Nota da Prova', max_digits=5, decimal_places=2, blank=True, null=True)
    nota_entrevista = models.DecimalField('Nota da Entrevista', max_digits=5, decimal_places=2, blank=True, null=True)
    data_entrevista = models.DateField('Data da Entrevista', null=True, blank=True)
    data_aplicacao = models.DateTimeField('Data de aplicação', auto_now_add=True)

    @property
    def status_prova(self):
        if self.nota is None:
            return None
        return 'aprovado' if self.nota > 6 else 'rejeitado'

    @property
    def status_prova_display(self):
        return 'Apto' if self.status_prova == 'aprovado' else 'Inapto' if self.status_prova == 'rejeitado' else '—'

    @property
    def status_entrevista(self):
        if self.nota_entrevista is None:
            return None
        return 'aprovado' if self.nota_entrevista > 6 else 'rejeitado'

    @property
    def status_entrevista_display(self):
        return 'Apto' if self.status_entrevista == 'aprovado' else 'Inapto' if self.status_entrevista == 'rejeitado' else '—'

    class Meta:
        verbose_name = 'Aplicação em Edital'
        verbose_name_plural = 'Aplicações em Editais'
        unique_together = ('bolsista', 'edital')

    def __str__(self):
        return f'{self.bolsista.user.nome_completo} - {self.edital.nome_edital}'

    def save(self, *args, **kwargs):
        if not self.numero_inscricao and self.bolsista_id and self.edital_id:
            if self.bolsista.numero_serie and self.edital.numero_serie:
                self.numero_inscricao = f'{self.bolsista.numero_serie}-{self.edital.numero_serie}'
        super().save(*args, **kwargs)


class AplicacaoEditalLog(DataModel):
    aplicacao = models.ForeignKey(
        AplicacaoEdital,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Aplicação'
    )
    alterado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_avaliacao',
        verbose_name='Alterado por'
    )

    nota_anterior = models.DecimalField(
        'Nota da Prova Anterior', max_digits=5, decimal_places=2, blank=True, null=True
    )
    nota_nova = models.DecimalField(
        'Nota da Prova Nova', max_digits=5, decimal_places=2, blank=True, null=True
    )

    nota_entrevista_anterior = models.DecimalField(
        'Nota da Entrevista Anterior', max_digits=5, decimal_places=2, blank=True, null=True
    )
    nota_entrevista_nova = models.DecimalField(
        'Nota da Entrevista Nova', max_digits=5, decimal_places=2, blank=True, null=True
    )

    data_entrevista_anterior = models.DateField(
        'Data da Entrevista Anterior', null=True, blank=True
    )
    data_entrevista_nova = models.DateField(
        'Data da Entrevista Nova', null=True, blank=True
    )

    status_anterior = models.CharField(
        'Status Anterior', max_length=20, blank=True, default=''
    )
    status_novo = models.CharField(
        'Status Novo', max_length=20, blank=True, default=''
    )

    class Meta:
        verbose_name = 'Log de Avaliação'
        verbose_name_plural = 'Logs de Avaliação'
        ordering = ['-created_at']

    def __str__(self):
        return f'Log #{self.pk} - {self.aplicacao} em {self.created_at}'
