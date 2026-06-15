from django.contrib import admin
from .models import User, Perfil, Tenant, DocumentoExterno


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'nome_completo', 'is_staff', 'is_active']
    search_fields = ['email', 'nome_completo']


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'telefone', 'unidade', 'tenant']
    list_filter = ['tipo', 'tenant']
    search_fields = ['user__email', 'user__nome_completo', 'telefone']


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['nome', 'dominio', 'ativo']


@admin.register(DocumentoExterno)
class DocumentoExternoAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo', 'tenant']
