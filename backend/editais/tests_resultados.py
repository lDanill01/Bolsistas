from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.http import Http404
from django.test import RequestFactory, TestCase

from accounts.models import User
from base.mixins import GROUP_MANAGER
from cadastro.models import CadastroBolsista
from editais.models import AplicacaoEdital, EditalProvisorio
from editais.views import ResultadosDownloadView, ResultadosListView


class ResultadosListViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.gestor = User.objects.create_user(
            email='gestor-resultados@teste.com',
            nome_completo='Gestor de Resultados',
            password='senha123',
        )
        grupo, _ = Group.objects.get_or_create(name=GROUP_MANAGER)
        self.gestor.groups.add(grupo)

        self.candidato_a = self._criar_candidato('Ana Resultado', 'ana-resultado@teste.com')
        self.candidato_b = self._criar_candidato('Bruno Resultado', 'bruno-resultado@teste.com')
        self.edital_a = self._criar_edital('Edital Resultado A', '1111')
        self.edital_b = self._criar_edital('Edital Resultado B', '2222')
        self.aplicacao_a = AplicacaoEdital.objects.create(
            bolsista=self.candidato_a,
            edital=self.edital_a,
            numero_inscricao='ANA-1111',
            nota=Decimal('8.00'),
        )
        self.aplicacao_b = AplicacaoEdital.objects.create(
            bolsista=self.candidato_b,
            edital=self.edital_b,
            numero_inscricao='BRU-2222',
            nota=Decimal('9.00'),
        )

    def _criar_candidato(self, nome, email):
        usuario = User.objects.create_user(
            email=email,
            nome_completo=nome,
            password='senha123',
        )
        return CadastroBolsista.objects.create(
            user=usuario,
            data_nascimento=date(1990, 1, 1),
        )

    def _criar_edital(self, nome, numero_serie):
        return EditalProvisorio.objects.create(
            nome_edital=nome,
            area_estudo='Tecnologia',
            nome_instituto='isi_biomassa',
            email_solicitante='gestor-resultados@teste.com',
            telefone='(67) 99999-9999',
            endereco='Rua dos Resultados',
            numero_vagas=2,
            modalidade_bolsa='nivel_1',
            valor_total_bolsa=Decimal('10000.00'),
            plataforma_tecnologica='Python',
            qualificacao_minima='Ensino Médio',
            conteudo_prova_teorica='Prova objetiva',
            criterios_desempate='Maior nota',
            criado_por=self.gestor,
            numero_serie=numero_serie,
            status='aberto',
        )

    def _renderizar(self, usuario, parametros=None):
        request = self.factory.get('/editais/resultados/', parametros or {})
        request.user = usuario
        response = ResultadosListView.as_view()(request)
        response.render()
        return response

    def test_gestor_ve_apenas_resultados_do_edital_filtrado(self):
        response = self._renderizar(self.gestor, {'edital': self.edital_a.pk})

        self.assertContains(response, 'ANA-1111')
        self.assertNotContains(response, 'BRU-2222')
        self.assertContains(response, 'Edital Resultado A')
        self.assertContains(response, 'Baixar CSV')

    def test_bolsista_nao_ve_resultado_de_outro_edital_pelo_filtro(self):
        response = self._renderizar(
            self.candidato_a.user,
            {'edital': self.edital_b.pk},
        )

        self.assertNotContains(response, 'ANA-1111')
        self.assertNotContains(response, 'BRU-2222')
        self.assertContains(response, 'Nenhum resultado encontrado')

    def test_etapa_nao_liberada_e_identificada_na_tabela(self):
        response = self._renderizar(self.gestor)

        self.assertContains(response, 'Não divulgada')

    def test_bolsista_nao_exporta_resultados_de_outro_edital(self):
        request = self.factory.get(f'/editais/resultados/{self.edital_b.pk}/download/')
        request.user = self.candidato_a.user

        with self.assertRaises(Http404):
            ResultadosDownloadView.as_view()(request, edital_pk=self.edital_b.pk)

    def test_paginacao_preserva_edital_e_visualizacao(self):
        for indice in range(20):
            candidato = self._criar_candidato(
                f'Candidato Pagina {indice}',
                f'pagina-{indice}@teste.com',
            )
            AplicacaoEdital.objects.create(
                bolsista=candidato,
                edital=self.edital_a,
                numero_inscricao=f'PAG-{indice:04d}',
                nota=Decimal('7.00'),
            )

        response = self._renderizar(
            self.gestor,
            {'edital': self.edital_a.pk, 'view': 'final'},
        )

        self.assertContains(
            response,
            f'?view=final&amp;edital={self.edital_a.pk}&page=2',
        )
