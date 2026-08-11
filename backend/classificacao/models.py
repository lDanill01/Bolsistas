from django.db import models
from base.models import DataModel
from cadastro.models import CadastroBolsista
from accounts.models import User


class CriterioClassificacao(DataModel):
    TIPO_CHOICES = [
        
        ('graduacao'                , 'Graduação'),
        ('mestrado'                 , 'Mestrado'),
        ('doutorado'                , 'Doutorado'),
        ('projetos_pesquisa'        , 'Participação em Projetos de Pesquisa/Atuação Profissional'),
        ('congressos'               , 'Participação em Congressos, Feiras, Eventos e Palestras'),
        ('resumo_anais'             , 'Resumo Publicado em Anais de Eventos'),
        ('artigo_completo_anais'    , 'Artigo Completo Publicado em Anais de Eventos'),
        ('artigo_nacional'          , 'Artigo Científico ou Capítulo de Livro Nacional Publicado'),
        ('artigo_internacional'     , 'Artigo Científico ou Capítulo de Livro Internacional Publicado'),
        ('livro_patente'            , 'Livro Publicado na Área de Interesse ou Patente Registrada'),
        ('minicurso'                , 'Participação em Minicurso (até 4 horas) na Área de Interesse'),
        ('treinamento'              , 'Treinamento (acima de 4 horas) na Área de Interesse'),
    ]

    nome = models.CharField('Nome', max_length=255)
    tipo_criterio = models.CharField('Tipo de critério', max_length=30, choices=TIPO_CHOICES, default='congressos')
    descricao = models.TextField('Descrição', blank=True)
    peso = models.DecimalField('Peso', max_digits=10, decimal_places=2, default=0)
    peso_maximo = models.DecimalField('Peso máximo', max_digits=10, decimal_places=2, default=0, help_text='Usado para critérios com teto de pontuação (ex: Projetos/Pesquisa).')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Critério de Classificação'
        verbose_name_plural = 'Critérios de Classificação'

    def __str__(self):
        return self.nome


class AvaliacaoBolsista(DataModel):
    bolsista = models.ForeignKey(
        CadastroBolsista,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        verbose_name='Bolsista',
    )
    criterio = models.ForeignKey(
        CriterioClassificacao,
        on_delete=models.CASCADE,
        related_name='avaliacoes',
        verbose_name='Critério',
    )
    pontos = models.DecimalField('Pontos', max_digits=10, decimal_places=2, default=0)
    avaliado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='avaliacoes_realizadas',
        verbose_name='Avaliado por',
    )
    observacao = models.TextField('Observação', blank=True)

    class Meta:
        verbose_name = 'Avaliação de Bolsista'
        verbose_name_plural = 'Avaliações de Bolsistas'
        unique_together = ('bolsista', 'criterio')

    def __str__(self):
        return f'{self.bolsista} - {self.criterio}: {self.pontos} pts'
