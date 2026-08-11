from datetime import date
from django.test import TestCase
from accounts.models import User
from .models import CadastroBolsista


class CadastroSerieTests(TestCase):
    def test_cadastro_gera_serie_ao_criar(self):
        user = User.objects.create_user(
            email='bolsista@teste.com',
            nome_completo='Bolsista Serie',
            password='senha123',
        )
        cadastro = CadastroBolsista.objects.create(
            user=user,
            data_nascimento=date(1993, 7, 20),
        )
        self.assertEqual(len(cadastro.numero_serie), 4)
        self.assertTrue(cadastro.numero_serie.isdigit())

    def test_cadastro_serie_unica(self):
        u1 = User.objects.create_user(
            email='u1@teste.com',
            nome_completo='Usuario Um',
            password='senha123',
        )
        u2 = User.objects.create_user(
            email='u2@teste.com',
            nome_completo='Usuario Dois',
            password='senha456',
        )
        c1 = CadastroBolsista.objects.create(user=u1, data_nascimento=date(1990, 1, 1))
        c2 = CadastroBolsista.objects.create(user=u2, data_nascimento=date(1991, 2, 2))
        self.assertNotEqual(c1.numero_serie, c2.numero_serie)

    def test_cadastro_serie_nao_muda_ao_atualizar(self):
        user = User.objects.create_user(
            email='fixo@teste.com',
            nome_completo='Fixo',
            password='senha123',
        )
        cadastro = CadastroBolsista.objects.create(
            user=user,
            data_nascimento=date(1994, 4, 4),
        )
        serie_original = cadastro.numero_serie
        cadastro.telefone = '(67) 12345-6789'
        cadastro.save()
        self.assertEqual(cadastro.numero_serie, serie_original)
