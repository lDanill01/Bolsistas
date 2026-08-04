from datetime import date, timedelta
from decimal import Decimal
import json
import re
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User
from base.mixins import GROUP_MANAGER
from cadastro.models import CadastroBolsista
from editais.models import EditalProvisorio, CronogramaEvento, AplicacaoEdital, AplicacaoEditalLog
from editais.views import (
    SalvarAvaliacoesLoteView, EditarAvaliacaoView, AplicacaoEditalListView,
    AvaliacaoListView, ExcluirCandidaturaView, AnexarDocumentoResultadoView,
)


class SalvarAvaliacoesLoteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.gestor = User.objects.create_user(
            email='gestor@teste.com', nome_completo='Gestor', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_MANAGER)
        self.gestor.groups.add(g)

        self.bolsista = CadastroBolsista.objects.create(
            user=User.objects.create_user(
                email='bol@teste.com', nome_completo='Bolsista', password='senha123'),
            data_nascimento=date(1990, 1, 1),
        )

        self.edital = EditalProvisorio.objects.create(
            nome_edital='Edital Avaliacao',
            area_estudo='TI',
            nome_instituto='isi_biomassa',
            email_solicitante='gestor@teste.com',
            telefone='(67) 99999-9999',
            endereco='Rua X',
            numero_vagas=5,
            modalidade_bolsa='nivel_1',
            valor_total_bolsa=10000,
            plataforma_tecnologica='Python',
            qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='-',
            criterios_desempate='-',
            criado_por=self.gestor,
        )

        self.aplicacao = AplicacaoEdital.objects.create(
            bolsista=self.bolsista, edital=self.edital)

        hoje = date.today()
        for ordem, (evento, dias) in enumerate([
            ('prova_teorica', -1),
            ('entrevista', -1),
            ('resultado_final', -1),
        ]):
            CronogramaEvento.objects.create(
                edital=self.edital,
                evento=evento,
                data_evento=hoje + timedelta(days=dias),
                ordem=ordem,
            )

    def _req(self, method, path, data=None):
        req = getattr(self.factory, method)(path, data=data or {})
        req.user = self.gestor
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))
        return req

    def test_salva_nota_prova_entrevista_e_status(self):
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '8,5',
            f'data_entrevista_{self.aplicacao.pk}': '2026-07-25',
            f'nota_entrevista_{self.aplicacao.pk}': '7,0',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('8.5'))
        self.assertEqual(self.aplicacao.nota_entrevista, Decimal('7.0'))
        self.assertEqual(self.aplicacao.data_entrevista, date(2026, 7, 25))
        self.assertEqual(self.aplicacao.status, 'aprovado')

    def test_rejeita_se_uma_das_notas_baixa(self):
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '8,0',
            f'nota_entrevista_{self.aplicacao.pk}': '6,0',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.status, 'rejeitado')

    def test_status_prova_display(self):
        self.aplicacao.nota = Decimal('7.5')
        self.aplicacao.save()
        self.assertEqual(self.aplicacao.status_prova_display, 'Apto')

        self.aplicacao.nota = Decimal('6')
        self.aplicacao.save()
        self.assertEqual(self.aplicacao.status_prova_display, 'Inapto')

    def test_status_entrevista_display(self):
        self.aplicacao.nota_entrevista = Decimal('8')
        self.aplicacao.save()
        self.assertEqual(self.aplicacao.status_entrevista_display, 'Apto')

        self.aplicacao.nota_entrevista = Decimal('5')
        self.aplicacao.save()
        self.assertEqual(self.aplicacao.status_entrevista_display, 'Inapto')

    def test_salva_apenas_etapa_preservando_dados_existentes(self):
        self.aplicacao.nota = Decimal('7.0')
        self.aplicacao.data_entrevista = date(2026, 7, 25)
        self.aplicacao.save()

        # Envia apenas a nota da entrevista, deixando prova/data em branco
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_entrevista_{self.aplicacao.pk}': '8,0',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('7.0'))  # preservado
        self.assertEqual(self.aplicacao.data_entrevista, date(2026, 7, 25))  # preservado
        self.assertEqual(self.aplicacao.nota_entrevista, Decimal('8.0'))  # atualizado
        self.assertEqual(self.aplicacao.status, 'aprovado')

    def test_cria_log_de_auditoria_no_salvamento_em_lote(self):
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '8,5',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        v(req)

        log = AplicacaoEditalLog.objects.filter(aplicacao=self.aplicacao).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.nota_anterior, None)
        self.assertEqual(log.nota_nova, Decimal('8.5'))
        self.assertEqual(log.alterado_por, self.gestor)

    def test_editar_avaliacao_individual_atualiza_e_registra_log(self):
        self.aplicacao.nota = Decimal('6.5')
        self.aplicacao.save()

        data = {
            'nota': '9.0',
            'nota_entrevista': '',
            'data_entrevista': '2026-08-10',
            'status': '',
        }
        req = self._req('post', f'/editais/aplicacoes/{self.aplicacao.pk}/editar-avaliacao/', data)
        v = EditarAvaliacaoView.as_view()
        r = v(req, pk=self.aplicacao.pk)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('9.0'))
        self.assertEqual(self.aplicacao.data_entrevista, date(2026, 8, 10))
        self.assertEqual(self.aplicacao.status, 'aprovado')

        log = AplicacaoEditalLog.objects.filter(aplicacao=self.aplicacao).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.nota_anterior, Decimal('6.5'))
        self.assertEqual(log.nota_nova, Decimal('9.0'))

    def test_carregar_modal_editar_avaliacao(self):
        req = self._req('get', f'/editais/aplicacoes/{self.aplicacao.pk}/editar-avaliacao/')
        v = EditarAvaliacaoView.as_view()
        r = v(req, pk=self.aplicacao.pk)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Editar Avaliação')
        self.assertContains(r, self.aplicacao.bolsista.user.nome_completo)

    @override_settings(DEBUG=True)
    def test_renderiza_input_vazio_quando_nota_none(self):
        self.aplicacao.nota = None
        self.aplicacao.nota_entrevista = None
        self.aplicacao.data_entrevista = None
        self.aplicacao.save()

        req = self._req('get', f'/editais/{self.edital.pk}/candidatos/')
        v = AplicacaoEditalListView.as_view()
        r = v(req, edital_pk=self.edital.pk)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, f'name="nota_prova_{self.aplicacao.pk}"')
        # O valor do input deve estar vazio quando a nota é None
        html = r.content.decode('utf-8')
        import re
        match = re.search(rf'<input[^>]*name="nota_prova_{self.aplicacao.pk}"[^>]*>', html)
        self.assertIsNotNone(match)
        self.assertNotIn('value="0.00"', match.group(0))

    @override_settings(DEBUG=True)
    def test_campos_preenchidos_ficam_readonly(self):
        self.aplicacao.nota = Decimal('7.5')
        self.aplicacao.nota_entrevista = Decimal('8')
        self.aplicacao.data_entrevista = date(2026, 8, 10)
        self.aplicacao.save()

        req = self._req('get', f'/editais/{self.edital.pk}/candidatos/')
        v = AplicacaoEditalListView.as_view()
        r = v(req, edital_pk=self.edital.pk)
        self.assertEqual(r.status_code, 200)
        r.render()
        html = r.content.decode('utf-8')
        import re

        for campo in ['nota_prova', 'nota_entrevista', 'data_entrevista']:
            match = re.search(rf'<input[^>]*name="{campo}_{self.aplicacao.pk}"[^>]*>', html)
            self.assertIsNotNone(match, msg=f'Input {campo} não encontrado')
            self.assertIn('readonly', match.group(0), msg=f'Input {campo} deveria estar readonly')

    def test_salvar_etapa_atual_ajax_preserva_nota(self):
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '7,5',
            f'nota_entrevista_{self.aplicacao.pk}': '',
            f'data_entrevista_{self.aplicacao.pk}': '2026-08-15',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        req.headers = {'X-Requested-With': 'XMLHttpRequest'}
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 200)
        resposta = json.loads(r.content)
        self.assertEqual(resposta['atualizadas'], 1)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('7.5'))
        self.assertEqual(self.aplicacao.data_entrevista, date(2026, 8, 15))
        self.assertEqual(self.aplicacao.status, 'aprovado')

    def test_salvar_form_completo_preserva_nota(self):
        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '8',
            f'nota_entrevista_{self.aplicacao.pk}': '',
            f'data_entrevista_{self.aplicacao.pk}': '',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('8'))
        self.assertEqual(self.aplicacao.status, 'aprovado')

    def test_nota_prova_inapto_bloqueia_etapas_seguintes(self):
        self.aplicacao.nota_entrevista = Decimal('8')
        self.aplicacao.data_entrevista = date(2026, 8, 10)
        self.aplicacao.save()

        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '5',
            f'nota_entrevista_{self.aplicacao.pk}': '9',
            f'data_entrevista_{self.aplicacao.pk}': '2026-08-20',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('5'))
        self.assertIsNone(self.aplicacao.nota_entrevista)
        self.assertIsNone(self.aplicacao.data_entrevista)
        self.assertEqual(self.aplicacao.status, 'rejeitado')

    def test_salvar_multiplos_candidatos_persiste_notas(self):
        bolsista2 = CadastroBolsista.objects.create(
            user=User.objects.create_user(
                email='bol2multi@teste.com', nome_completo='Bolsista 2', password='senha123'),
            data_nascimento=date(1990, 1, 1),
        )
        aplicacao2 = AplicacaoEdital.objects.create(bolsista=bolsista2, edital=self.edital)

        data = {
            'edital_pk': str(self.edital.pk),
            f'nota_prova_{self.aplicacao.pk}': '7',
            f'nota_entrevista_{self.aplicacao.pk}': '',
            f'data_entrevista_{self.aplicacao.pk}': '',
            f'nota_prova_{aplicacao2.pk}': '8,5',
            f'nota_entrevista_{aplicacao2.pk}': '7,0',
            f'data_entrevista_{aplicacao2.pk}': '2026-08-15',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        aplicacao2.refresh_from_db()
        self.assertEqual(self.aplicacao.nota, Decimal('7'))
        self.assertEqual(self.aplicacao.status, 'aprovado')
        self.assertEqual(aplicacao2.nota, Decimal('8.5'))
        self.assertEqual(aplicacao2.nota_entrevista, Decimal('7.0'))
        self.assertEqual(aplicacao2.data_entrevista, date(2026, 8, 15))
        self.assertEqual(aplicacao2.status, 'aprovado')

    def test_salvar_com_success_url_redireciona(self):
        success_url = f'/editais/avaliacao/?edital={self.edital.pk}'
        data = {
            'edital_pk': str(self.edital.pk),
            'success_url': success_url,
            f'nota_prova_{self.aplicacao.pk}': '8,5',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, success_url)

    def test_salvar_com_success_url_ajax(self):
        success_url = f'/editais/avaliacao/?edital={self.edital.pk}'
        data = {
            'edital_pk': str(self.edital.pk),
            'success_url': success_url,
            f'nota_prova_{self.aplicacao.pk}': '8,5',
        }
        req = self._req('post', '/editais/aplicacoes/salvar-avaliacoes/', data)
        req.headers = {'X-Requested-With': 'XMLHttpRequest'}
        v = SalvarAvaliacoesLoteView.as_view()
        r = v(req)
        self.assertEqual(r.status_code, 200)
        resposta = json.loads(r.content)
        self.assertEqual(resposta['redirect_url'], success_url)


class AvaliacaoPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.gestor = User.objects.create_user(
            email='gestor@teste.com', nome_completo='Gestor', password='senha123')
        g, _ = Group.objects.get_or_create(name=GROUP_MANAGER)
        self.gestor.groups.add(g)

        self.bolsista = CadastroBolsista.objects.create(
            user=User.objects.create_user(
                email='bol@teste.com', nome_completo='Bolsista', password='senha123'),
            data_nascimento=date(1990, 1, 1),
        )

        self.edital = EditalProvisorio.objects.create(
            nome_edital='Edital Avaliacao Pagina',
            area_estudo='TI',
            nome_instituto='isi_biomassa',
            email_solicitante='gestor@teste.com',
            telefone='(67) 99999-9999',
            endereco='Rua X',
            numero_vagas=5,
            modalidade_bolsa='nivel_1',
            valor_total_bolsa=10000,
            plataforma_tecnologica='Python',
            qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='-',
            criterios_desempate='-',
            criado_por=self.gestor,
        )

        self.aplicacao = AplicacaoEdital.objects.create(
            bolsista=self.bolsista, edital=self.edital)

    def _criar_cronograma(self, dias):
        hoje = date.today()
        for ordem, (evento, d) in enumerate(dias.items()):
            CronogramaEvento.objects.create(
                edital=self.edital,
                evento=evento,
                data_evento=hoje + timedelta(days=d),
                ordem=ordem,
            )

    def _req(self, method, path, data=None):
        req = getattr(self.factory, method)(path, data=data or {})
        req.user = self.gestor
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))
        return req

    @override_settings(DEBUG=True)
    def test_pagina_avaliacao_renderiza_candidatos(self):
        self._criar_cronograma({'prova_teorica': -1, 'entrevista': -1, 'resultado_final': -1})
        req = self._req('get', f'/editais/avaliacao/?edital={self.edital.pk}')
        r = AvaliacaoListView.as_view()(req)
        self.assertEqual(r.status_code, 200)
        r.render()
        html = r.content.decode('utf-8')
        self.assertIn(self.aplicacao.bolsista.user.nome_completo, html)
        self.assertIn(f'name="nota_prova_{self.aplicacao.pk}"', html)
        self.assertIn(f'name="data_entrevista_{self.aplicacao.pk}"', html)
        self.assertIn(f'name="nota_entrevista_{self.aplicacao.pk}"', html)

    @override_settings(DEBUG=True)
    def test_etapas_liberadas_campos_nao_disabled(self):
        self._criar_cronograma({'prova_teorica': -1, 'entrevista': -1, 'resultado_final': -1})
        req = self._req('get', f'/editais/avaliacao/?edital={self.edital.pk}')
        r = AvaliacaoListView.as_view()(req)
        r.render()
        html = r.content.decode('utf-8')
        match = re.search(rf'<input[^>]*name="nota_prova_{self.aplicacao.pk}"[^>]*>', html)
        self.assertIsNotNone(match)
        self.assertNotIn('disabled', match.group(0))

    @override_settings(DEBUG=True)
    def test_etapa_nao_liberada_campo_disabled(self):
        # prova teórica ainda no futuro -> nota da prova bloqueada
        self._criar_cronograma({'prova_teorica': 5, 'entrevista': 5, 'resultado_final': 5})
        req = self._req('get', f'/editais/avaliacao/?edital={self.edital.pk}')
        r = AvaliacaoListView.as_view()(req)
        r.render()
        html = r.content.decode('utf-8')
        match = re.search(rf'<input[^>]*name="nota_prova_{self.aplicacao.pk}"[^>]*>', html)
        self.assertIsNotNone(match)
        self.assertIn('disabled', match.group(0))

    @override_settings(DEBUG=True)
    def test_pagina_sem_edital_nao_quebra(self):
        req = self._req('get', '/editais/avaliacao/')
        r = AvaliacaoListView.as_view()(req)
        self.assertEqual(r.status_code, 200)
        r.render()
        self.assertIn('Selecione um edital', r.content.decode('utf-8'))

    @override_settings(DEBUG=True)
    def test_pagina_exige_gestor(self):
        view_user = User.objects.create_user(
            email='view@teste.com', nome_completo='View', password='senha123')
        req = self._req('get', f'/editais/avaliacao/?edital={self.edital.pk}')
        req.user = view_user
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            AvaliacaoListView.as_view()(req)

    @override_settings(DEBUG=True)
    def test_pagina_exibe_coluna_resultado_e_acoes_de_gestor(self):
        self._criar_cronograma({'prova_teorica': -1, 'entrevista': -1, 'resultado_final': -1})
        self.aplicacao.nota = Decimal('8')
        self.aplicacao.nota_entrevista = Decimal('7')
        self.aplicacao.save()

        req = self._req('get', f'/editais/avaliacao/?edital={self.edital.pk}')
        r = AvaliacaoListView.as_view()(req)
        r.render()
        html = r.content.decode('utf-8')
        self.assertIn('Aprovado', html)
        self.assertIn('btn-excluir-candidatura', html)
        self.assertIn('btn-upload-resultado', html)

    def test_excluir_candidatura_gestor(self):
        success_url = f'/editais/avaliacao/?edital={self.edital.pk}'
        req = self._req('post', f'/editais/aplicacoes/{self.aplicacao.pk}/excluir/',
                        {'success_url': success_url})
        r = ExcluirCandidaturaView.as_view()(req, pk=self.aplicacao.pk)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, success_url)
        self.assertFalse(AplicacaoEdital.objects.filter(pk=self.aplicacao.pk).exists())

    def test_anexar_documento_resultado(self):
        arquivo = SimpleUploadedFile('resultado.pdf', b'%PDF-1.4 fake', content_type='application/pdf')
        req = self._req('post', f'/editais/aplicacoes/{self.aplicacao.pk}/anexar-documento/',
                        {'documento_resultado': arquivo})
        r = AnexarDocumentoResultadoView.as_view()(req, pk=self.aplicacao.pk)
        self.assertEqual(r.status_code, 302)

        self.aplicacao.refresh_from_db()
        self.assertIsNotNone(self.aplicacao.documento_resultado)
        self.assertTrue(self.aplicacao.documento_resultado.name.startswith('avaliacoes/resultado'))

    @override_settings(DEBUG=True)
    def test_modal_documento_renderiza(self):
        req = self._req('get', f'/editais/aplicacoes/{self.aplicacao.pk}/anexar-documento/')
        r = AnexarDocumentoResultadoView.as_view()(req, pk=self.aplicacao.pk)
        self.assertEqual(r.status_code, 200)
        html = r.content.decode('utf-8')
        self.assertIn('Documento do Resultado', html)
        self.assertIn(self.aplicacao.bolsista.user.nome_completo, html)
