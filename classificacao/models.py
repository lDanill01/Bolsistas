from django.db import models
from base.models import DataModel
from base.managers import TenantManager
from accounts.models import User, Tenant
from editais.models import AplicacaoEdital


class CriterioClassificacao(DataModel):
    TIPO_CHOICES = [
        ('graduacao', 'Graduação'),
        ('mestrado', 'Mestrado'),
        ('doutorado', 'Doutorado'),
        ('projetos_pesquisa', 'Participação em Projetos de Pesquisa/Atuação Profissional'),
        ('congressos', 'Participação em Congressos, Feiras, Eventos e Palestras'),
        ('resumo_anais', 'Resumo Publicado em Anais de Eventos'),
        ('artigo_completo_anais', 'Artigo Completo Publicado em Anais de Eventos'),
        ('artigo_nacional', 'Artigo Científico ou Capítulo de Livro Nacional Publicado'),
        ('artigo_internacional', 'Artigo Científico ou Capítulo de Livro Internacional Publicado'),
        ('livro_patente', 'Livro Publicado na Área de Interesse ou Patente Registrada'),
        ('minicurso', 'Participação em Minicurso (até 4 horas) na Área de Interesse'),
        ('treinamento', 'Treinamento (acima de 4 horas) na Área de Interesse'),
    ]

    nome = models.CharField('Nome', max_length=255)
    tipo_criterio = models.CharField('Tipo de critério', max_length=30, choices=TIPO_CHOICES, default='congressos')
    descricao = models.TextField('Descrição', blank=True)
    peso = models.DecimalField('Peso', max_digits=10, decimal_places=2, default=0)
    peso_maximo = models.DecimalField('Peso máximo', max_digits=10, decimal_places=2, default=0, help_text='Usado para critérios com teto de pontuação (ex: Projetos/Pesquisa).')
    ativo = models.BooleanField('Ativo', default=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='criterios')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Critério de Classificação'
        verbose_name_plural = 'Critérios de Classificação'

    def __str__(self):
        return self.nome


class Classificacao(DataModel):
    aplicacao = models.ForeignKey(AplicacaoEdital, on_delete=models.CASCADE, related_name='classificacoes')
    classificador = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classificacoes_feitas')
    pontuacao_total = models.DecimalField('Pontuação total', max_digits=10, decimal_places=2)
    observacoes = models.TextField('Observações', blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='classificacoes')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Classificação'
        verbose_name_plural = 'Classificações'

    def __str__(self):
        return f'{self.aplicacao.bolsista.user.nome_completo} - {self.pontuacao_total} pts'


class ClassificacaoCriterio(DataModel):
    classificacao = models.ForeignKey(Classificacao, on_delete=models.CASCADE, related_name='notas')
    criterio = models.ForeignKey(CriterioClassificacao, on_delete=models.CASCADE, related_name='notas')
    nota = models.DecimalField('Nota', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Nota por Critério'
        verbose_name_plural = 'Notas por Critério'

    def __str__(self):
        return f'{self.criterio.nome}: {self.nota}'
