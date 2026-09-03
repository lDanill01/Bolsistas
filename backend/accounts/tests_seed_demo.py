from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from accounts.models import User
from cadastro.models import CadastroBolsista, ExperienciaProfissional, FormacaoAcademica
from editais.models import AplicacaoEdital, EditalProvisorio


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_cria_usuarios_perfis_editais_e_aplicacoes(self):
        call_command('seed_demo', stdout=StringIO())

        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(CadastroBolsista.objects.count(), 2)
        self.assertEqual(FormacaoAcademica.objects.count(), 4)
        self.assertEqual(ExperienciaProfissional.objects.count(), 2)
        self.assertTrue(ExperienciaProfissional.objects.filter(cargo='Analista de Dados').exists())
        self.assertEqual(EditalProvisorio.objects.count(), 3)
        self.assertEqual(sum(e.cronograma.count() for e in EditalProvisorio.objects.all()), 21)
        self.assertEqual(AplicacaoEdital.objects.count(), 4)

    def test_seed_demo_pode_ser_executado_novamente_sem_duplicar(self):
        call_command('seed_demo', stdout=StringIO())
        call_command('seed_demo', stdout=StringIO())

        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(EditalProvisorio.objects.count(), 3)
        self.assertEqual(AplicacaoEdital.objects.count(), 4)
