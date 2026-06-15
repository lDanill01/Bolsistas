from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from base.models import DataModel
from base.managers import TenantManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = None
    last_name = None
    email = models.EmailField('Email', unique=True)
    nome_completo = models.CharField('Nome completo', max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome_completo']

    objects = UserManager()

    def __str__(self):
        return self.nome_completo or self.email


class Tenant(DataModel):
    nome = models.CharField('Nome', max_length=255)
    dominio = models.CharField('Domínio', max_length=255, unique=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.nome


class Perfil(DataModel):
    TIPO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MANAGER', 'Gerente'),
        ('COMMON', 'Comum'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='COMMON')
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    unidade = models.CharField('Unidade', max_length=255, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfis')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'{self.user} - {self.get_tipo_display()}'


class DocumentoExterno(DataModel):
    TIPO_CHOICES = [
        ('RG', 'RG'),
        ('CPF', 'CPF'),
        ('OUTRO', 'Outro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField('Arquivo', upload_to='documentos/')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)
    tenant = models.ForeignKey(Tenant, on_delete=models.SET_NULL, null=True, blank=True, related_name='documentos')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Documento Externo'
        verbose_name_plural = 'Documentos Externos'

    def __str__(self):
        return f'{self.user} - {self.get_tipo_display()}'
