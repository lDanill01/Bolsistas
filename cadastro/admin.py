from django.contrib import admin
from .models import CadastroBolsista, CursoSuperior, PosGraduacao, SolicitacaoEdicao


@admin.register(CadastroBolsista)
class CadastroBolsistaAdmin(admin.ModelAdmin):
    list_display = ['user', 'data_nascimento', 'endereco', 'pontuacao_previa', 'tenant', 'created_at']
    list_filter = ['tenant']
    search_fields = ['user__email', 'user__nome_completo', 'endereco']


@admin.register(CursoSuperior)
class CursoSuperiorAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'grau', 'curso', 'instituicao', 'ano_conclusao']
    list_filter = ['grau']
    search_fields = ['bolsista__user__nome_completo', 'curso', 'instituicao']


@admin.register(PosGraduacao)
class PosGraduacaoAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'tipo', 'area', 'instituicao', 'ano_conclusao']
    list_filter = ['tipo']
    search_fields = ['bolsista__user__nome_completo', 'area', 'instituicao']


@admin.register(SolicitacaoEdicao)
class SolicitacaoEdicaoAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'campo', 'valor_original', 'valor_novo', 'status', 'created_at']
    list_filter = ['status', 'campo']
    search_fields = ['bolsista__user__nome_completo', 'campo']
