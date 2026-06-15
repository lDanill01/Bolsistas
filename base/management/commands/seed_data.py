from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from faker import Faker

from accounts.models import User, Perfil, Tenant
from cadastro.models import CadastroBolsista, CursoSuperior, PosGraduacao
from editais.models import Edital, AplicacaoEdital
from classificacao.models import CriterioClassificacao, Classificacao, ClassificacaoCriterio

fake = Faker('pt_BR')


class Command(BaseCommand):
    help = 'Gera dados realistas para demonstracao'

    def handle(self, *args, **options):
        self.stdout.write('Limpando dados existentes...')
        ClassificacaoCriterio.objects.all().delete()
        Classificacao.objects.all().delete()
        CriterioClassificacao.objects.all().delete()
        AplicacaoEdital.objects.all().delete()
        Edital.objects.all().delete()
        CursoSuperior.objects.all().delete()
        PosGraduacao.objects.all().delete()
        CadastroBolsista.objects.all().delete()
        Perfil.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()
        Tenant.objects.all().delete()

        self.stdout.write('Criando tenants...')
        sesi = Tenant.objects.create(nome='SESI', dominio='sesi', ativo=True)
        senai = Tenant.objects.create(nome='SENAI', dominio='senai', ativo=True)

        for tenant in [sesi, senai]:
            self._seed_tenant(tenant)

        self.stdout.write(self.style.SUCCESS('Seed concluido com sucesso!'))

    def _seed_tenant(self, tenant):
        self.stdout.write(f'  Populando tenant: {tenant.nome}...')

        admin = self._criar_usuario('ADMIN', tenant)
        gestores = [self._criar_usuario('MANAGER', tenant) for _ in range(2)]
        bolsistas = [self._criar_usuario('COMMON', tenant) for _ in range(10)]

        cadastros = []
        for user in bolsistas[:6]:
            cad = self._criar_cadastro(user, tenant)
            cadastros.append(cad)

        criterios = self._criar_criterios(tenant)
        editais = self._criar_editais(tenant, admin)

        aplicacoes = []
        for i, cad in enumerate(cadastros):
            edital = editais[i % len(editais)]
            if not AplicacaoEdital.objects.filter(bolsista=cad, edital=edital).exists():
                apl = AplicacaoEdital.objects.create(
                    bolsista=cad,
                    edital=edital,
                    status='pendente' if i < 3 else 'em_analise',
                    tenant=tenant,
                )
                aplicacoes.append(apl)

        for i, apl in enumerate(aplicacoes[:4]):
            self._criar_classificacao(apl, gestores[i % len(gestores)], criterios, tenant)

    def _criar_usuario(self, tipo, tenant):
        primeiro_nome = fake.first_name()
        sobrenome = fake.last_name()
        email = f'{primeiro_nome.lower()}.{sobrenome.lower()}@{tenant.dominio}.com.br'
        user = User.objects.create_user(
            email=email,
            nome_completo=f'{primeiro_nome} {sobrenome}',
            password='123456',
        )
        user.is_active = True
        user.save()
        Perfil.objects.create(
            user=user,
            tipo=tipo,
            telefone=fake.phone_number() if tipo != 'ADMIN' else '',
            unidade=fake.bairro() if tipo != 'ADMIN' else '',
            tenant=tenant,
        )
        return user

    def _criar_cadastro(self, user, tenant):
        cad = CadastroBolsista.objects.create(
            user=user,
            endereco=fake.address(),
            data_nascimento=fake.date_of_birth(minimum_age=18, maximum_age=70),
            tenant=tenant,
        )
        if fake.boolean(chance_of_getting_true=60):
            CursoSuperior.objects.create(
                bolsista=cad,
                instituicao=fake.company(),
                curso=fake.random_element([
                    'Engenharia de Producao', 'Administracao', 'Ciencia da Computacao',
                    'Direito', 'Contabilidade', 'Psicologia',
                ]),
                grau=fake.random_element(['tecnologo', 'bacharelado', 'licenciatura']),
                ano_conclusao=fake.random_int(min=2000, max=2025),
                tenant=tenant,
            )
        if fake.boolean(chance_of_getting_true=40):
            PosGraduacao.objects.create(
                bolsista=cad,
                tipo=fake.random_element(['pos_graduacao', 'mba', 'especializacao', 'mestrado']),
                instituicao=fake.company(),
                area=fake.random_element([
                    'Gestao de Projetos', 'Data Science', 'Educacao',
                    'Engenharia de Software', 'Marketing Digital',
                ]),
                ano_conclusao=fake.random_int(min=2010, max=2025),
                tenant=tenant,
            )
        # Seed some boolean criteria randomly
        cad.participacao_projetos_anos = fake.random_int(min=0, max=15) if fake.boolean(chance_of_getting_true=50) else 0
        cad.participacao_congressos = fake.boolean(chance_of_getting_true=40)
        cad.resumo_anais = fake.boolean(chance_of_getting_true=30)
        cad.artigo_completo_anais = fake.boolean(chance_of_getting_true=25)
        cad.artigo_cientifico_nacional = fake.boolean(chance_of_getting_true=20)
        cad.artigo_cientifico_internacional = fake.boolean(chance_of_getting_true=10)
        cad.livro_patente = fake.boolean(chance_of_getting_true=5)
        cad.participacao_minicurso = fake.boolean(chance_of_getting_true=35)
        cad.treinamento = fake.boolean(chance_of_getting_true=30)
        cad.save()
        return cad

    def _criar_criterios(self, tenant):
        dados = [
            ('Graduação', 'graduacao', 'Pontuacao por possuir graduacao', None, 0),
            ('Mestrado', 'mestrado', 'Pontuacao por possuir mestrado', None, 0),
            ('Doutorado', 'doutorado', 'Pontuacao por possuir doutorado', 50, 0),
            ('Participacao em Projetos de Pesquisa', 'projetos_pesquisa', '10 pontos por ano de trabalho, maximo 100 pontos', 10, 100),
            ('Participacao em Congressos/Feiras/Eventos', 'congressos', 'Participacao em congressos, feiras, eventos e palestras', 2, 0),
            ('Resumo em Anais de Eventos', 'resumo_anais', 'Resumo publicado em anais de eventos', 2, 0),
            ('Artigo Completo em Anais de Eventos', 'artigo_completo_anais', 'Artigo completo publicado em anais de eventos', 4, 0),
            ('Artigo Cientifico Nacional', 'artigo_nacional', 'Artigo cientifico ou capitulo de livro nacional publicado', 10, 0),
            ('Artigo Cientifico Internacional', 'artigo_internacional', 'Artigo cientifico ou capitulo de livro internacional publicado', 15, 0),
            ('Livro/Patente', 'livro_patente', 'Livro publicado na area de interesse ou patente registrada', 20, 0),
            ('Participacao em Minicurso', 'minicurso', 'Participacao em minicurso (ate 4 horas) na area de interesse', 2, 0),
            ('Treinamento', 'treinamento', 'Treinamento (acima de 4 horas) na area de interesse', 5, 0),
        ]
        criterios = []
        for nome, tipo_criterio, desc, peso, peso_maximo in dados:
            c = CriterioClassificacao.objects.create(
                nome=nome,
                tipo_criterio=tipo_criterio,
                descricao=desc,
                peso=peso or 0,
                peso_maximo=peso_maximo,
                ativo=True,
                tenant=tenant,
            )
            criterios.append(c)
        return criterios

    def _criar_editais(self, tenant, admin):
        dados = [
            ('Bolsa de Iniciacao Cientifica', 'Programa de iniciacao cientifica para estudantes de graduacao.', 'Estar matriculado em curso superior.'),
            ('Bolsa de Mestrado', 'Auxilio para alunos de mestrado em engenharia.', 'Ter sido aprovado em programa de mestrado.'),
            ('Bolsa de Doutorado', 'Auxilio para alunos de doutorado.', 'Ter sido aprovado em programa de doutorado.'),
        ]
        now = timezone.now()
        editais = []
        for nome, desc, req in dados:
            dias_atras = fake.random_int(min=5, max=30)
            dias_frente = fake.random_int(min=15, max=60)
            edital = Edital.objects.create(
                nome=nome,
                descricao=desc,
                requisitos=req,
                data_abertura=now - timezone.timedelta(days=dias_atras),
                data_fechamento=now + timezone.timedelta(days=dias_frente),
                status='aberto',
                criado_por=admin,
                tenant=tenant,
            )
            editais.append(edital)
        return editais

    def _criar_classificacao(self, aplicacao, gestor, criterios, tenant):
        classificacao = Classificacao.objects.create(
            aplicacao=aplicacao,
            classificador=gestor,
            pontuacao_total=0,
            observacoes=fake.sentence(nb_words=10),
            tenant=tenant,
        )
        pontuacao_total = 0.0
        for criterio in criterios:
            nota = fake.random_int(min=0, max=10)
            ClassificacaoCriterio.objects.create(
                classificacao=classificacao,
                criterio=criterio,
                nota=nota,
            )
            pontuacao_total += nota * float(criterio.peso)
        classificacao.pontuacao_total = pontuacao_total
        classificacao.save(update_fields=['pontuacao_total'])
