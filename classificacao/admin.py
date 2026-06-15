from django.contrib import admin
from .models import CriterioClassificacao, Classificacao, ClassificacaoCriterio


@admin.register(CriterioClassificacao)
class CriterioClassificacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_criterio', 'peso', 'peso_maximo', 'ativo', 'tenant']
    list_filter = ['ativo', 'tipo_criterio']


@admin.register(Classificacao)
class ClassificacaoAdmin(admin.ModelAdmin):
    list_display = ['aplicacao', 'classificador', 'pontuacao_total']


@admin.register(ClassificacaoCriterio)
class ClassificacaoCriterioAdmin(admin.ModelAdmin):
    list_display = ['classificacao', 'criterio', 'nota']
