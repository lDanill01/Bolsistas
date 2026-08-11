from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from base.models import DataModel


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


class Perfil(DataModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    unidade = models.CharField('Unidade', max_length=255, blank=True)
    data_nascimento = models.DateField('Data de nascimento', null=True, blank=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return str(self.user)


class DocumentoExterno(DataModel):
    TIPO_CHOICES = [
        ('RG', 'RG'),
        ('CPF', 'CPF'),
        ('OUTRO', 'Outro'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos')
    arquivo = models.FileField('Arquivo', upload_to='documentos/')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES)

    class Meta:
        verbose_name = 'Documento Externo'
        verbose_name_plural = 'Documentos Externos'

    def __str__(self):
        return f'{self.user} - {self.get_tipo_display()}'
