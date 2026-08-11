from datetime import date
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from accounts.models import User
from base.mixins import GROUP_VIEW_USER
from cadastro.models import CadastroBolsista, FormacaoAcademica, ExperienciaProfissional
from cadastro.views import SolicitacaoMultiplaView


def _attach_messages(request):
    setattr(request, 'session', 'session')
    setattr(request, '_messages', FallbackStorage(request))


class SolicitacaoMultiplaFlowTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='bol@teste.com', nome_completo='Bolsista', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_VIEW_USER)
        self.user.groups.add(g)
        self.cadastro = CadastroBolsista.objects.create(
            user=self.user, data_nascimento=date(1993, 7, 20), telefone='(67) 99999-9999')

    def _req(self, method, path, data=None):
        req = getattr(self.factory, method)(path, data=data or {})
        req.user = self.user
        _attach_messages(req)
        return req

    def test_context_contem_formsets_reais(self):
        v = SolicitacaoMultiplaView()
        req = self._req('get', '/cadastro/solicitar/')
        v.request = req
        v.kwargs = {}
        ctx = v.get_context_data()
        self.assertIn('formacao_formset', ctx)
        self.assertIn('experiencia_formset', ctx)
        self.assertIn('areas', ctx)
        self.assertIn('cursos_por_area', ctx)
        self.assertIn('instituicoes', ctx)
        self.assertNotIn('data_nascimento', ctx['form'].fields)

    def test_post_salva_nova_graduacao_sem_experiencia(self):
        """Usuario so quer incluir graduacao; experiencia vazia nao deve travar."""
        data = {
            'telefone': '(67) 98888-7777',
            'rua': '', 'numero': '', 'bairro': '', 'cidade': '', 'estado': '',
            'formacoes-TOTAL_FORMS': '1',
            'formacoes-INITIAL_FORMS': '0',
            'formacoes-MIN_NUM_FORMS': '0',
            'formacoes-MAX_NUM_FORMS': '1000',
            'formacoes-0-tipo': 'graduacao',
            'formacoes-0-status': 'concluida',
            'formacoes-0-instituicao': 'UFMS',
            'formacoes-0-area': 'Engenharias',
            'formacoes-0-curso': 'Engenharia Civil',
            'formacoes-0-ano_conclusao': '2022',
            'experiencias-TOTAL_FORMS': '1',
            'experiencias-INITIAL_FORMS': '0',
            'experiencias-MIN_NUM_FORMS': '0',
            'experiencias-MAX_NUM_FORMS': '1000',
            'experiencias-0-area_atuacao': '',
            'experiencias-0-anos_experiencia': '',
            'experiencias-0-anexo': '',
        }
        req = self._req('post', '/cadastro/solicitar/', data)
        v = SolicitacaoMultiplaView()
        v.request = req
        v.kwargs = {}
        r = v.post(req)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(FormacaoAcademica.objects.filter(
            bolsista=self.cadastro, tipo='graduacao').exists())
        self.cadastro.refresh_from_db()
        self.assertEqual(self.cadastro.telefone, '(67) 98888-7777')

    def test_post_atualiza_graduacao_existente(self):
        fa = FormacaoAcademica.objects.create(
            bolsista=self.cadastro, tipo='graduacao', curso='Eng. Mecanica')
        data = {
            'telefone': '',
            'rua': '', 'numero': '', 'bairro': '', 'cidade': '', 'estado': '',
            'formacoes-TOTAL_FORMS': '1',
            'formacoes-INITIAL_FORMS': '1',
            'formacoes-MIN_NUM_FORMS': '0',
            'formacoes-MAX_NUM_FORMS': '1000',
            'formacoes-0-id': str(fa.pk),
            'formacoes-0-tipo': 'graduacao',
            'formacoes-0-status': 'concluida',
            'formacoes-0-instituicao': 'UFMS',
            'formacoes-0-area': 'Engenharias',
            'formacoes-0-curso': 'Engenharia Civil',
            'formacoes-0-ano_conclusao': '2022',
            'experiencias-TOTAL_FORMS': '1',
            'experiencias-INITIAL_FORMS': '0',
            'experiencias-MIN_NUM_FORMS': '0',
            'experiencias-MAX_NUM_FORMS': '1000',
            'experiencias-0-area_atuacao': '',
            'experiencias-0-anos_experiencia': '',
            'experiencias-0-anexo': '',
        }
        req = self._req('post', '/cadastro/solicitar/', data)
        v = SolicitacaoMultiplaView()
        v.request = req
        v.kwargs = {}
        r = v.post(req)
        self.assertEqual(r.status_code, 302)
        fa.refresh_from_db()
        self.assertEqual(fa.curso, 'Engenharia Civil')

    def test_post_salva_nova_experiencia(self):
        data = {
            'telefone': '',
            'rua': '', 'numero': '', 'bairro': '', 'cidade': '', 'estado': '',
            'formacoes-TOTAL_FORMS': '1',
            'formacoes-INITIAL_FORMS': '0',
            'formacoes-MIN_NUM_FORMS': '0',
            'formacoes-MAX_NUM_FORMS': '1000',
            'experiencias-TOTAL_FORMS': '1',
            'experiencias-INITIAL_FORMS': '0',
            'experiencias-MIN_NUM_FORMS': '0',
            'experiencias-MAX_NUM_FORMS': '1000',
            'experiencias-0-area_atuacao': 'Engenharia',
            'experiencias-0-anos_experiencia': '3',
            'experiencias-0-anexo': '',
        }
        req = self._req('post', '/cadastro/solicitar/', data)
        v = SolicitacaoMultiplaView()
        v.request = req
        v.kwargs = {}
        r = v.post(req)
        self.assertEqual(r.status_code, 302)
        self.assertTrue(ExperienciaProfissional.objects.filter(
            bolsista=self.cadastro, area_atuacao='Engenharia').exists())

    def test_get_nao_exige_data_nascimento_no_form(self):
        v = SolicitacaoMultiplaView()
        req = self._req('get', '/cadastro/solicitar/')
        v.request = req
        v.kwargs = {}
        form = v.get_form()
        self.assertNotIn('data_nascimento', form.fields)
        self.assertIn('telefone', form.fields)