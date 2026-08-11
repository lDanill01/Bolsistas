from django.contrib import admin
from .models import CadastroBolsista, FormacaoAcademica, ExperienciaProfissional, AnexoComprobatorio, SolicitacaoEdicao


class FormacaoAcademicaInline(admin.TabularInline):
    model = FormacaoAcademica
    extra = 1


class ExperienciaProfissionalInline(admin.TabularInline):
    model = ExperienciaProfissional
    extra = 1


class AnexoComprobatorioInline(admin.TabularInline):
    model = AnexoComprobatorio
    extra = 1


@admin.register(CadastroBolsista)
class CadastroBolsistaAdmin(admin.ModelAdmin):
    list_display = ['numero_serie', 'user', 'telefone', 'data_nascimento', 'created_at']
    search_fields = ['numero_serie', 'user__nome_completo', 'user__email']
    inlines = [FormacaoAcademicaInline, ExperienciaProfissionalInline, AnexoComprobatorioInline]


@admin.register(SolicitacaoEdicao)
class SolicitacaoEdicaoAdmin(admin.ModelAdmin):
    list_display = ['bolsista', 'campo', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['bolsista__user__nome_completo', 'campo']
