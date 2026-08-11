from datetime import date
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, DocumentoExterno
from base.mixins import GROUP_MANAGER
from cadastro.models import CadastroBolsista, AnexoComprobatorio, ExperienciaProfissional
from cadastro.views import GestaoDocumentosView


class GestaoDocumentosTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.gestor = User.objects.create_user(
            email='gestor@teste.com', nome_completo='Gestor', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_MANAGER)
        self.gestor.groups.add(g)

        self.view_user = User.objects.create_user(
            email='view@teste.com', nome_completo='View', password='senha123')

        self.bolsista_user = User.objects.create_user(
            email='bol@teste.com', nome_completo='Bolsista A', password='senha123')
        self.bolsista = CadastroBolsista.objects.create(
            user=self.bolsista_user, data_nascimento=date(1995, 3, 15))

        pdf = SimpleUploadedFile('doc.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        AnexoComprobatorio.objects.create(
            bolsista=self.bolsista, tipo='rg_cpf', anexo=pdf)
        ExperienciaProfissional.objects.create(
            bolsista=self.bolsista, area_atuacao='TI', anos_experiencia=2, anexo=pdf)
        DocumentoExterno.objects.create(user=self.bolsista_user, tipo='CPF', arquivo=pdf)

    def _req(self, path, user):
        req = self.factory.get(path)
        req.user = user
        return req

    def _render(self, path, user):
        r = GestaoDocumentosView.as_view()(self._req(path, user))
        r.render()
        return r.content.decode('utf-8')

    @override_settings(DEBUG=True)
    def test_pagina_renderiza_documentos_para_gestor(self):
        html = self._render('/cadastro/documentos/', self.gestor)
        self.assertIn('Documento de Identificação (RG/CPF)', html)
        self.assertIn('Comprovante de Experiência Profissional', html)
        self.assertIn('CPF', html)

    @override_settings(DEBUG=True)
    def test_filtro_por_tipo(self):
        html = self._render('/cadastro/documentos/?tipo=CPF', self.gestor)
        self.assertIn('/media/documentos/', html)
        self.assertNotIn('/media/anexos/', html)
        self.assertNotIn('/media/experiencias/', html)

    @override_settings(DEBUG=True)
    def test_filtro_por_usuario(self):
        outro = User.objects.create_user(
            email='outro@teste.com', nome_completo='Outro', password='senha123')
        CadastroBolsista.objects.create(
            user=outro, data_nascimento=date(1992, 1, 1))
        html = self._render(f'/cadastro/documentos/?usuario={self.bolsista_user.pk}', self.gestor)
        self.assertIn('Bolsista A', html)
        self.assertNotIn('>Outro<', html)

    @override_settings(DEBUG=True)
    def test_filtro_por_periodo(self):
        html = self._render('/cadastro/documentos/?data_inicio=2999-01-01', self.gestor)
        self.assertIn('Nenhum documento encontrado', html)

    def test_pagina_restrita_a_gestores(self):
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            GestaoDocumentosView.as_view()(self._req('/cadastro/documentos/', self.view_user))
