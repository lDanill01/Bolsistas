from django.contrib import admin
from .models import EditalProvisorio, CronogramaEvento


class CronogramaEventoInline(admin.TabularInline):
    model = CronogramaEvento
    extra = 1
    ordering = ['ordem']


@admin.register(EditalProvisorio)
class EditalProvisorioAdmin(admin.ModelAdmin):
    list_display = ['nome_instituto', 'modalidade_bolsa', 'numero_vagas', 'vigencia', 'status', 'total_eventos', 'created_at']
    list_filter = ['status', 'modalidade_bolsa']
    search_fields = ['nome_instituto', 'modalidade_bolsa']
    inlines = [CronogramaEventoInline]
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Instituto', {
            'fields': ('nome_instituto', 'email_solicitante', 'telefone', 'endereco'),
        }),
        ('Bolsas', {
            'fields': ('numero_vagas', 'modalidade_bolsa', 'plataforma_tecnologica', 'vigencia', 'endereco_atuacao'),
        }),
        ('Requisitos', {
            'fields': ('qualificacao_minima', 'experiencia_minima', 'conhecimento_desejavel',
                       'conteudo_prova_teorica', 'entrevista', 'criterios_desempate'),
        }),
        ('Metadados', {
            'fields': ('status', 'criado_por', 'tenant'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        super().save_model(request, obj, form, change)

    def criado_em(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    criado_em.short_description = 'Criado em'

    def atualizado_em(self, obj):
        return obj.updated_at.strftime('%d/%m/%Y %H:%M')
    atualizado_em.short_description = 'Atualizado em'
