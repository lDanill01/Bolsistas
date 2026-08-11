from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from accounts.models import User
from base.mixins import GROUP_VIEW_USER, GROUP_MANAGER
from cadastro.models import CadastroBolsista, FormacaoAcademica
from cadastro.views import CadastroDetailView


class CadastroDetailViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='bol@teste.com', nome_completo='Bolsista', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_VIEW_USER)
        self.user.groups.add(g)
        self.cadastro = CadastroBolsista.objects.create(
            user=self.user, data_nascimento=date(1993, 7, 20))
        FormacaoAcademica.objects.create(
            bolsista=self.cadastro, tipo='graduacao', curso='Engenharia')

    def _req(self, method, path):
        req = getattr(self.factory, method)(path)
        req.user = self.user
        return req

    def test_usuario_comum_nao_ve_botoes_de_formacao(self):
        v = CadastroDetailView()
        req = self._req('get', '/cadastro/')
        v.request = req
        v.kwargs = {}
        v.object = self.cadastro
        ctx = v.get_context_data()
        self.assertFalse(ctx['can_edit'])

    def test_gestor_ve_botoes_de_formacao(self):
        manager = User.objects.create_user(
            email='gestor@teste.com', nome_completo='Gestor', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_MANAGER)
        manager.groups.add(g)
        req = self._req('get', f'/cadastro/{self.cadastro.pk}/')
        req.user = manager
        v = CadastroDetailView()
        v.request = req
        v.kwargs = {'pk': self.cadastro.pk}
        v.object = self.cadastro
        ctx = v.get_context_data()
        self.assertTrue(ctx['can_edit'])