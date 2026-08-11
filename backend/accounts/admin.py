from django.contrib import admin
from .models import User, Perfil


class PerfilInline(admin.TabularInline):
    model = Perfil
    can_delete = False
    extra = 0
    fields = ['telefone', 'unidade', 'data_nascimento']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'nome_completo', 'is_staff', 'is_active']
    search_fields = ['email', 'nome_completo']
    filter_horizontal = ['groups', 'user_permissions']
    inlines = [PerfilInline]
