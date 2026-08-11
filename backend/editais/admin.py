from django.contrib import admin
from .models import EditalProvisorio, CronogramaEvento, AplicacaoEdital


class CronogramaEventoInline(admin.TabularInline):
    model = CronogramaEvento
    extra = 1
    ordering = ['ordem']
    fields = ['evento', 'data_evento', 'observacao', 'ordem']


@admin.register(EditalProvisorio)
class EditalProvisorioAdmin(admin.ModelAdmin):
    list_display = ['nome_edital', 'numero_serie', 'nome_instituto', 'modalidade_bolsa', 'numero_vagas', 'vigencia', 'status', 'total_eventos', 'created_at']
    list_filter = ['status', 'modalidade_bolsa']
    search_fields = ['nome_edital', 'nome_instituto', 'modalidade_bolsa', 'numero_serie']
    inlines = [CronogramaEventoInline]
    readonly_fields = ['criado_em', 'atualizado_em']
    fieldsets = (
        ('Edital', {
            'fields': ('nome_edital', 'area_estudo', 'detalhes_edital'),
        }),
        ('Instituto', {
            'fields': ('nome_instituto', 'email_solicitante', 'telefone', 'endereco'),
        }),
        ('Configuração da Bolsa', {
            'fields': ('modalidade_bolsa', 'qualificacao_minima', 'detalhes_qualificacao_minima',
                       'experiencia', 'modalidade_atuacao',
                       'plataforma_tecnologica', 'vigencia', 'endereco_atuacao',
                       'numero_vagas', 'valor_bolsa',
                       'valor_minimo', 'valor_maximo'),
        }),
        ('Detalhes Adicionais', {
            'fields': ('modalidade_entrevista', 'conhecimento_desejavel',
                       'conteudo_prova_teorica', 'criterios_desempate', 'comentarios'),
        }),
        ('Metadados', {
            'fields': ('status', 'criado_por'),
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


@admin.register(AplicacaoEdital)
class AplicacaoEditalAdmin(admin.ModelAdmin):
    list_display = ['numero_inscricao', 'bolsista', 'edital', 'status', 'nota', 'data_entrevista', 'data_aplicacao']
    list_filter = ['status', 'edital']
    search_fields = ['numero_inscricao', 'bolsista__user__nome_completo', 'edital__nome_edital']
