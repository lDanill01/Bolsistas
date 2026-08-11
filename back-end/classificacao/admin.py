from django.contrib import admin
from .models import CriterioClassificacao


@admin.register(CriterioClassificacao)
class CriterioClassificacaoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo_criterio', 'peso', 'peso_maximo', 'ativo']
    list_filter = ['ativo', 'tipo_criterio']
