from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from cadastro.models import CadastroBolsista
from .models import EditalProvisorio, CronogramaEvento, AplicacaoEdital


class NumeroSerieTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='teste@teste.com',
            nome_completo='Usuario Teste',
            password='senha123',
        )
        self.bolsista = CadastroBolsista.objects.create(
            user=self.user,
            data_nascimento=date(1990, 1, 1),
        )

    def test_edital_gera_serie_ao_criar(self):
        edital = EditalProvisorio.objects.create(
            nome_edital='Edital Teste',
            area_estudo='TI',
            nome_instituto='fatec_cg',
            email_solicitante='teste@teste.com',
            telefone='(67) 99999-9999',
            endereco='Rua X',
            numero_vagas=5,
            modalidade_bolsa='nivel_1',
            valor_total_bolsa=10000,
            plataforma_tecnologica='Python',
            qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='-',
            criterios_desempate='-',
            criado_por=self.user,
        )
        self.assertEqual(len(edital.numero_serie), 4)
        self.assertTrue(edital.numero_serie.isdigit())

    def test_edital_serie_unica(self):
        edital1 = EditalProvisorio.objects.create(
            nome_edital='A', area_estudo='X',
            nome_instituto='fatec_cg', email_solicitante='a@teste.com',
            telefone='1', endereco='R', numero_vagas=1,
            modalidade_bolsa='nivel_1', valor_total_bolsa=1000,
            plataforma_tecnologica='Z', qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='-', criterios_desempate='-',
            criado_por=self.user,
        )
        edital2 = EditalProvisorio.objects.create(
            nome_edital='B', area_estudo='Y',
            nome_instituto='fatec_cg', email_solicitante='b@teste.com',
            telefone='2', endereco='S', numero_vagas=2,
            modalidade_bolsa='nivel_1', valor_total_bolsa=2000,
            plataforma_tecnologica='W', qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='-', criterios_desempate='-',
            criado_por=self.user,
        )
        self.assertNotEqual(edital1.numero_serie, edital2.numero_serie)


class InscricaoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='candidato@teste.com',
            nome_completo='Candidato Teste',
            password='senha123',
        )
        self.bolsista = CadastroBolsista.objects.create(
            user=self.user,
            data_nascimento=date(1990, 1, 1),
        )
        self.user2 = User.objects.create_user(
            email='gestor@teste.com',
            nome_completo='Gestor Teste',
            password='senha123',
        )
        self.edital = EditalProvisorio.objects.create(
            nome_edital='Edital Inscricao',
            area_estudo='Engenharia',
            nome_instituto='isi_biomassa',
            email_solicitante='gestor@teste.com',
            telefone='(67) 88888-8888',
            endereco='Av Teste',
            numero_vagas=10,
            modalidade_bolsa='nivel_2',
            valor_total_bolsa=50000,
            plataforma_tecnologica='Django',
            qualificacao_minima='Graduação Completa',
            conteudo_prova_teorica='Prova objetiva',
            criterios_desempate='Maior nota',
            criado_por=self.user2,
        )

    def test_inscricao_formato(self):
        aplicacao = AplicacaoEdital.objects.create(
            bolsista=self.bolsista,
            edital=self.edital,
        )
        esperado = f'{self.bolsista.numero_serie}-{self.edital.numero_serie}'
        self.assertEqual(aplicacao.numero_inscricao, esperado)
        self.assertLessEqual(len(aplicacao.numero_inscricao), 10)

    def test_inscricao_unica(self):
        a1 = AplicacaoEdital.objects.create(bolsista=self.bolsista, edital=self.edital)
        user3 = User.objects.create_user(
            email='candidato2@teste.com',
            nome_completo='Candidato Dois',
            password='senha456',
        )
        bolsista2 = CadastroBolsista.objects.create(
            user=user3,
            data_nascimento=date(1992, 5, 10),
        )
        a2 = AplicacaoEdital.objects.create(bolsista=bolsista2, edital=self.edital)
        self.assertNotEqual(a1.numero_inscricao, a2.numero_inscricao)


class CronogramaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='gestor@teste.com',
            nome_completo='Gestor Teste',
            password='senha123',
        )
        self.edital = EditalProvisorio.objects.create(
            nome_edital='Edital Cronograma',
            area_estudo='Biologia',
            nome_instituto='ist_alimentos',
            email_solicitante='gestor@teste.com',
            telefone='(67) 77777-7777',
            endereco='Rua Cronograma',
            numero_vagas=3,
            modalidade_bolsa='nivel_3',
            valor_total_bolsa=30000,
            plataforma_tecnologica='Biotec',
            qualificacao_minima='Mestrado Concluído',
            conteudo_prova_teorica='-',
            criterios_desempate='-',
            criado_por=self.user,
        )

    def _abrir_edital(self):
        """Abre o edital sem disparar calcular_cronograma() (via QuerySet.update)."""
        EditalProvisorio.objects.filter(pk=self.edital.pk).update(status='aberto')
        self.edital.refresh_from_db()

    def test_data_final_outorga(self):
        hoje = timezone.now().date()
        data_outorga = hoje + timedelta(days=60)
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='outorga',
            data_evento=data_outorga,
            ordem=1,
        )
        self.assertEqual(self.edital.data_final, data_outorga)

    def test_data_final_sem_outorga(self):
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='inicio_submissao',
            data_evento=timezone.now().date(),
            ordem=1,
        )
        self.assertIsNone(self.edital.data_final)

    def test_proxima_etapa_futura(self):
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='inicio_submissao',
            data_evento=hoje,
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='entrevista',
            data_evento=hoje + timedelta(days=15),
            ordem=2,
        )
        self._abrir_edital()
        prox = self.edital.proxima_etapa
        self.assertIsNotNone(prox)
        self.assertEqual(prox.evento, 'inicio_submissao')

    def test_proxima_etapa_passada(self):
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='inicio_submissao',
            data_evento=hoje - timedelta(days=30),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='entrevista',
            data_evento=hoje + timedelta(days=15),
            ordem=2,
        )
        self._abrir_edital()
        prox = self.edital.proxima_etapa
        self.assertIsNotNone(prox)
        self.assertEqual(prox.evento, 'entrevista')

    def test_proxima_etapa_sem_eventos(self):
        self.assertIsNone(self.edital.proxima_etapa)

    def test_dias_uteis_positivo(self):
        hoje = timezone.now().date()
        data_evento = hoje + timedelta(days=7)
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='resultado_final',
            data_evento=data_evento,
            ordem=1,
        )
        self._abrir_edital()
        dias = self.edital.dias_para_proxima_etapa
        self.assertIsNotNone(dias)
        self.assertGreaterEqual(dias, 0)

    def test_prazo_submissao_expirado(self):
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='inicio_submissao',
            data_evento=hoje - timedelta(days=30),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='limite_submissao',
            data_evento=hoje - timedelta(days=1),
            ordem=2,
        )
        self._abrir_edital()
        self.assertTrue(self.edital.prazo_submissao_expirado)

    def test_processo_em_andamento_apos_fim_submissao(self):
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='limite_submissao',
            data_evento=hoje - timedelta(days=1),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='resultado_final',
            data_evento=hoje + timedelta(days=30),
            ordem=2,
        )
        self._abrir_edital()
        self.assertTrue(self.edital.prazo_submissao_expirado)
        self.assertFalse(self.edital.processo_concluido)
        self.assertEqual(self.edital.nome_proxima_etapa, 'Divulgação do Resultado Final')

    def test_processo_concluido_apos_ultima_etapa(self):
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='limite_submissao',
            data_evento=hoje - timedelta(days=30),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='resultado_final',
            data_evento=hoje - timedelta(days=1),
            ordem=2,
        )
        self._abrir_edital()
        self.assertTrue(self.edital.processo_concluido)

    def test_fechar_editais_nao_fecha_processo_em_andamento(self):
        from .tasks import fechar_editais_vencidos
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='limite_submissao',
            data_evento=hoje - timedelta(days=1),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='entrevista',
            data_evento=hoje + timedelta(days=15),
            ordem=2,
        )
        self._abrir_edital()
        fechados = fechar_editais_vencidos()
        self.edital.refresh_from_db()
        self.assertEqual(fechados, 0)
        self.assertEqual(self.edital.status, 'aberto')
        self.assertEqual(self.edital.nome_proxima_etapa, 'Entrevista')

    def test_fechar_editais_fecha_processo_concluido(self):
        from .tasks import fechar_editais_vencidos
        hoje = timezone.now().date()
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='limite_submissao',
            data_evento=hoje - timedelta(days=30),
            ordem=1,
        )
        CronogramaEvento.objects.create(
            edital=self.edital,
            evento='resultado_final',
            data_evento=hoje - timedelta(days=1),
            ordem=2,
        )
        self._abrir_edital()
        fechados = fechar_editais_vencidos()
        self.edital.refresh_from_db()
        self.assertEqual(fechados, 1)
        self.assertEqual(self.edital.status, 'encerrado')

    def test_total_inscritos(self):
        self.assertEqual(self.edital.total_inscritos, 0)
        cadastro = CadastroBolsista.objects.create(
            user=User.objects.create_user(
                email='candidato@teste.com',
                nome_completo='Candidato',
                password='senha123',
            ),
            data_nascimento=date(1995, 3, 15),
        )
        AplicacaoEdital.objects.create(bolsista=cadastro, edital=self.edital)
        self.assertEqual(self.edital.total_inscritos, 1)
