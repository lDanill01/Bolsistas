import random
from decimal import Decimal
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils import timezone

from faker import Faker

from accounts.models import User, Perfil
from cadastro.models import (
    CadastroBolsista, FormacaoAcademica, ExperienciaProfissional,
    SolicitacaoEdicao,
)
from cadastro.utils import calcular_pontuacao_previa
from editais.models import (
    EditalProvisorio, CronogramaEvento, DistribuicaoBolsa,
    AplicacaoEdital, NIVEL_BOLSA_CONFIG,
)
from classificacao.models import CriterioClassificacao, AvaliacaoBolsista
from notifications.models import Notificacao
from base.mixins import GROUP_MANAGER, GROUP_VIEW_USER, GROUP_EXECUTE_USER

fake = Faker('pt_BR')

CRITERIOS_PADRAO = [
    ('graduacao',              'Graduação',                              10.00, 0),
    ('mestrado',               'Mestrado',                               15.00, 0),
    ('doutorado',              'Doutorado',                              25.00, 0),
    ('projetos_pesquisa',      'Projetos de Pesquisa/Atuação',           5.00, 30.00),
    ('congressos',             'Congressos, Feiras e Eventos',           5.00, 0),
    ('resumo_anais',           'Resumo Publicado em Anais',              3.00, 0),
    ('artigo_completo_anais',  'Artigo Completo em Anais',               5.00, 0),
    ('artigo_nacional',        'Artigo Científico/Capítulo Nacional',    8.00, 0),
    ('artigo_internacional',   'Artigo Científico/Capítulo Internacional', 12.00, 0),
    ('livro_patente',          'Livro ou Patente Registrada',            10.00, 0),
    ('minicurso',              'Minicurso (até 4h)',                     2.00, 0),
    ('treinamento',            'Treinamento (acima de 4h)',              4.00, 0),
]

INSTITUICOES = [
    'Universidade de São Paulo', 'UNICAMP', 'UFMS',
    'Universidade Federal do Rio de Janeiro', 'UFMG',
    'Universidade de Brasília', 'UFSC', 'UFPR',
    'PUC-SP', 'Mackenzie', 'UNESP',
]

AREAS_ESTUDO = [
    'Ciência da Computação', 'Engenharia de Produção', 'Biotecnologia',
    'Engenharia Elétrica', 'Administração', 'Química',
    'Ciências Biológicas', 'Física', 'Matemática',
    'Engenharia Civil', 'Farmácia', 'Agronomia',
    'Medicina Veterinária', 'Nutrição', 'Direito',
]

PLATAFORMAS = [
    'Python, Django, PostgreSQL', 'Java, Spring Boot, Oracle',
    'React, Node.js, MongoDB', 'C#, .NET, SQL Server',
    'AWS, Docker, Kubernetes', 'Flutter, Firebase',
    'TensorFlow, PyTorch, CUDA', 'PHP, Laravel, MySQL',
]

NOMES_EDITAIS = [
    'Edital de Inovação Tecnológica',
    'Bolsas de Pesquisa em Biotecnologia',
    'Programa de Desenvolvimento Científico',
    'Edital de Soluções Sustentáveis',
    'Bolsas de Extensão Tecnológica',
    'Programa de Iniciação Científica Avançada',
    'Edital de Pesquisa Aplicada',
    'Bolsas para Projetos de Infraestrutura Digital',
]


def _faixa_valores_nivel(nivel_config):
    """Extrai os valores minimo e maximo de um nivel, considerando experiencia_valores."""
    experiencia_valores = nivel_config.get('experiencia_valores', {})
    if experiencia_valores:
        todas_faixas = list(experiencia_valores.values())
        val_min = min(f[0] for f in todas_faixas)
        val_max = max(f[1] for f in todas_faixas)
    else:
        val_min = nivel_config.get('valor_minimo', 500)
        val_max = nivel_config.get('valor_maximo', 2000)
    return Decimal(str(val_min)), Decimal(str(val_max))


class Command(BaseCommand):
    help = 'Gera dados fake para alimentar a base do projeto'

    def add_arguments(self, parser):
        parser.add_argument('--bolsistas', type=int, default=15,
                            help='Quantidade de bolsistas (default: 15)')
        parser.add_argument('--editais', type=int, default=6,
                            help='Quantidade de editais (default: 6)')
        parser.add_argument('--aplicacoes-por-edital', type=int, default=6,
                            help='Aplicações por edital aberto (default: 6)')
        parser.add_argument('--senha', type=str, default='senha123',
                            help='Senha padrão para todos os usuários (default: senha123)')
        parser.add_argument('--limpar', action='store_true',
                            help='Remove todos os dados antes de gerar')
        parser.add_argument('--seed', type=int, default=None,
                            help='Seed para reproducibilidade (default: aleatorio)')
        parser.add_argument('--datas-espalhadas', action='store_true', default=True,
                            help='Espalha created_at/updated_at nos ultimos 12 meses (default: True)')
        parser.add_argument('--sem-datas-espalhadas', action='store_true',
                            help='Desativa o espalhamento de datas')

    def handle(self, *args, **opcoes):
        if opcoes['limpar']:
            self._limpar_dados()

        seed = opcoes['seed']
        if seed is not None:
            random.seed(seed)
            fake.seed_instance(seed)

        self.senha = opcoes['senha']
        self.qtd_bolsistas = opcoes['bolsistas']
        self.qtd_editais = opcoes['editais']
        self.qtd_aplicacoes = opcoes['aplicacoes_por_edital']
        self.datas_espalhadas = opcoes['datas_espalhadas'] and not opcoes['sem_datas_espalhadas']

        self.stdout.write(self.style.WARNING('=== GERANDO DADOS FAKE ==='))
        self.stdout.write(f'Bolsistas: {self.qtd_bolsistas} | '
                          f'Editais: {self.qtd_editais} | '
                          f'Aplicações/edital: {self.qtd_aplicacoes}')

        grupos = self._criar_grupos()
        superuser = self._criar_superuser()
        managers = self._criar_usuarios('manager', 3, [GROUP_MANAGER])
        executores = self._criar_usuarios('executor', 3, [GROUP_EXECUTE_USER])
        bolsista_users = self._criar_usuarios('bolsista', self.qtd_bolsistas, [GROUP_VIEW_USER])
        todos_users = [superuser] + managers + executores + bolsista_users

        self._criar_perfis(todos_users, managers)

        self._criar_criterios()
        bolsistas = self._criar_bolsistas(bolsista_users)

        editais = self._criar_editais(managers)
        self._criar_aplicacoes(bolsistas, editais)
        self._criar_solicitacoes(bolsistas, managers)
        self._criar_avaliacoes(bolsistas, editais, managers)
        self._criar_notificacoes(todos_users, bolsistas, managers)
        self._calcular_pontuacoes(bolsistas)

        # Espalha datas dos registros dependentes
        self._espalhar_datas(FormacaoAcademica.objects.all())
        self._espalhar_datas(ExperienciaProfissional.objects.all())
        self._espalhar_datas(AplicacaoEdital.objects.all())
        self._espalhar_datas(AvaliacaoBolsista.objects.all())
        self._espalhar_datas(Notificacao.objects.all())
        self._espalhar_datas(SolicitacaoEdicao.objects.all())

        total = self._contar_registros()
        self.stdout.write(self.style.SUCCESS(
            f'\n=== DADOS GERADOS COM SUCESSO ===\n'
            f'Total de registros: {total}\n'
            f'Usuários de teste: admin@email.com / {self.senha}\n'
            f'Demais usuários: {self.senha} como senha\n'
        ))

    # ----------------------------------------------------------------
    # FASE 0: Limpeza
    # ----------------------------------------------------------------
    def _limpar_dados(self):
        self.stdout.write('Limpando dados existentes...')
        modelos = [
            Notificacao, AvaliacaoBolsista, AplicacaoEdital,
            DistribuicaoBolsa, CronogramaEvento, EditalProvisorio,
            SolicitacaoEdicao, ExperienciaProfissional, FormacaoAcademica,
            CadastroBolsista, CriterioClassificacao,
            Perfil, User,
        ]
        for m in modelos:
            m.objects.all().delete()
        self.stdout.write('Dados removidos.')

    def _contar_registros(self):
        return (
            User.objects.count()
            + Perfil.objects.count()
            + CadastroBolsista.objects.count()
            + FormacaoAcademica.objects.count()
            + ExperienciaProfissional.objects.count()
            + CriterioClassificacao.objects.count()
            + EditalProvisorio.objects.count()
            + CronogramaEvento.objects.count()
            + DistribuicaoBolsa.objects.count()
            + AplicacaoEdital.objects.count()
            + AvaliacaoBolsista.objects.count()
            + Notificacao.objects.count()
            + SolicitacaoEdicao.objects.count()
        )

    def _espalhar_datas(self, queryset, dias=365):
        """Sobrescreve created_at/updated_at espalhando nos ultimos N dias."""
        if not self.datas_espalhadas:
            return
        agora = timezone.now()
        objetos = list(queryset)
        for obj in objetos:
            offset_criacao = timedelta(
                days=random.randint(0, dias),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            offset_update = timedelta(days=random.randint(0, min(30, dias)))
            obj.created_at = agora - offset_criacao
            obj.updated_at = agora - offset_criacao + offset_update
        # bulk_update em lotes para nao estourar parametros
        for i in range(0, len(objetos), 500):
            lote = objetos[i:i + 500]
            type(objetos[0]).objects.bulk_update(lote, ['created_at', 'updated_at'])

    # ----------------------------------------------------------------
    # FASE 1: Grupos e Usuários
    # ----------------------------------------------------------------
    def _criar_grupos(self):
        grupos = {}
        for nome in [GROUP_MANAGER, GROUP_VIEW_USER, GROUP_EXECUTE_USER]:
            g, _ = Group.objects.get_or_create(name=nome)
            grupos[nome] = g
        self.stdout.write(f'  Grupos: {len(grupos)} criados/verificados')
        return grupos

    def _criar_superuser(self):
        u, created = User.objects.get_or_create(
            email='admin@email.com',
            defaults={
                'nome_completo': 'Administrador do Sistema',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        if created:
            u.set_password(self.senha)
            u.save()
        self.stdout.write(f'  Superuser: {u.email}')
        return u

    def _criar_usuarios(self, prefixo, qtd, grupos_nomes):
        users = []
        for i in range(1, qtd + 1):
            nome = fake.name()
            email = f'{prefixo}{i}@email.com'
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'nome_completo': nome,
                    'is_active': True,
                },
            )
            if created:
                u.set_password(self.senha)
                u.save()
            for gn in grupos_nomes:
                g = Group.objects.get(name=gn)
                u.groups.add(g)
            users.append(u)
        self.stdout.write(f'  Usuários {prefixo}: {qtd} criados/verificados')
        return users

    # ----------------------------------------------------------------
    # FASE 2: Perfis
    # ----------------------------------------------------------------
    def _criar_perfis(self, users, managers):
        institutos = [c[1] for c in EditalProvisorio.INSTITUTOS_CHOICES]
        for u in users:
            p, created = Perfil.objects.get_or_create(user=u)
            p.telefone = fake.cellphone_number()
            if u.is_superuser or u.groups.filter(name=GROUP_MANAGER).exists():
                p.unidade = random.choice(institutos)
            else:
                p.unidade = fake.company()
            p.data_nascimento = fake.date_of_birth(minimum_age=25, maximum_age=60)
            p.save()
        self.stdout.write(f'  Perfis: {len(users)} criados/atualizados')

    # ----------------------------------------------------------------
    # FASE 3: Critérios de Classificação
    # ----------------------------------------------------------------
    def _criar_criterios(self):
        for tipo, nome, peso, peso_maximo in CRITERIOS_PADRAO:
            CriterioClassificacao.objects.get_or_create(
                tipo_criterio=tipo,
                defaults={
                    'nome': nome,
                    'descricao': f'Critério de pontuação para {nome.lower()}.',
                    'peso': Decimal(str(peso)),
                    'peso_maximo': Decimal(str(peso_maximo)),
                    'ativo': True,
                },
            )
        self.stdout.write(f'  Critérios: {len(CRITERIOS_PADRAO)} criados/verificados')

    # ----------------------------------------------------------------
    # FASE 4: Cadastro de Bolsistas
    # ----------------------------------------------------------------
    def _criar_bolsistas(self, users):
        bolsistas = []
        for u in users:
            b, created = CadastroBolsista.objects.get_or_create(
                user=u,
                defaults={
                    'telefone': fake.cellphone_number(),
                    'data_nascimento': fake.date_of_birth(minimum_age=18, maximum_age=55),
                    'rua': fake.street_name(),
                    'numero': str(random.randint(1, 9999)),
                    'bairro': fake.bairro(),
                    'cidade': fake.city(),
                    'estado': random.choice([
                        'MS', 'SP', 'RJ', 'MG', 'PR', 'SC', 'RS', 'DF',
                    ]),
                    'participacao_projetos_anos': random.randint(0, 10),
                    'participacao_congressos': random.random() > 0.4,
                    'resumo_anais': random.random() > 0.5,
                    'artigo_completo_anais': random.random() > 0.6,
                    'artigo_cientifico_nacional': random.random() > 0.7,
                    'artigo_cientifico_internacional': random.random() > 0.85,
                    'livro_patente': random.random() > 0.9,
                    'participacao_minicurso': random.random() > 0.5,
                    'treinamento': random.random() > 0.6,
                },
            )
            if created:
                # ~10% dos bolsistas sem formacao/experiencia (caso-limite)
                if random.random() > 0.1:
                    self._criar_formacoes(b)
                if random.random() > 0.1:
                    self._criar_experiencias(b)
            bolsistas.append(b)

        self._espalhar_datas(CadastroBolsista.objects.filter(pk__in=[b.pk for b in bolsistas]))
        self.stdout.write(f'  Bolsistas: {len(bolsistas)} criados/verificados')
        return bolsistas

    def _criar_formacoes(self, bolsista):
        tipos_basicos = ['ensino_medio', 'graduacao', 'curso_tecnico']
        tipos_avancados = [
            'especializacao', 'mba', 'mestrado', 'doutorado',
            'pos_graduacao', 'pos_doutorado',
        ]

        basico = random.choice(tipos_basicos)
        area = random.choice(AREAS_ESTUDO)
        instituicao = random.choice(INSTITUICOES)
        FormacaoAcademica.objects.create(
            bolsista=bolsista,
            tipo=basico,
            status='concluida',
            instituicao=instituicao,
            curso=fake.sentence(nb_words=3)[:50].rstrip('.'),
            area=area,
            ano_conclusao=random.randint(2005, 2020),
        )

        for _ in range(random.randint(1, 2)):
            avancado = random.choice(tipos_avancados)
            FormacaoAcademica.objects.create(
                bolsista=bolsista,
                tipo=avancado,
                status=random.choice(['concluida', 'em_andamento']),
                instituicao=random.choice(INSTITUICOES),
                curso=fake.sentence(nb_words=4)[:50].rstrip('.'),
                area=area if random.random() > 0.3 else random.choice(AREAS_ESTUDO),
                ano_conclusao=random.randint(2010, 2026)
                if random.random() > 0.3 else None,
            )

    def _criar_experiencias(self, bolsista):
        for _ in range(random.randint(1, 3)):
            ExperienciaProfissional.objects.create(
                bolsista=bolsista,
                area_atuacao=random.choice(AREAS_ESTUDO),
                anos_experiencia=random.randint(1, 8),
            )
        bolsista.sincronizar_anos_experiencia()

    # ----------------------------------------------------------------
    # FASE 5: Editais
    # ----------------------------------------------------------------
    def _criar_editais(self, managers):
        editais = []
        status_pool = ['aberto', 'aberto', 'aberto', 'encerrado', 'em_analise', 'cancelado']

        niveis = list(NIVEL_BOLSA_CONFIG.keys())

        for i in range(self.qtd_editais):
            nivel = random.choice(niveis)
            nivel_config = NIVEL_BOLSA_CONFIG[nivel]
            qualificacao_opts = [q[0] for q in nivel_config['qualificacao']]
            experiencia_opts = nivel_config.get('experiencia', [('Sem Experiência', 'Sem Experiência')])
            val_min, val_max = _faixa_valores_nivel(nivel_config)

            criador = random.choice(managers)
            status = status_pool[i % len(status_pool)] if i < len(status_pool) else 'aberto'

            nome = NOMES_EDITAIS[i % len(NOMES_EDITAIS)]
            instituto = EditalProvisorio.INSTITUTOS_CHOICES[i % len(EditalProvisorio.INSTITUTOS_CHOICES)][1]

            vagas = random.randint(3, 10)
            valor_unitario_ref = random.uniform(float(val_min), float(val_max))
            valor_total = Decimal(str(round(valor_unitario_ref * vagas * 1.3, 2)))

            edital = EditalProvisorio.objects.create(
                nome_edital=f'{nome} {2024 + i} — {instituto}',
                area_estudo=random.choice(AREAS_ESTUDO),
                detalhes_edital=fake.paragraph(nb_sentences=3),
                nome_instituto=EditalProvisorio.INSTITUTOS_CHOICES[i % len(EditalProvisorio.INSTITUTOS_CHOICES)][0],
                email_solicitante=criador.email,
                telefone=fake.cellphone_number(),
                endereco=fake.address(),
                numero_vagas=vagas,
                modalidade_bolsa=nivel,
                valor_total_bolsa=valor_total,
                valor_minimo=val_min,
                valor_maximo=val_max,
                modalidade_atuacao=random.choice(['presencial', 'remota']),
                plataforma_tecnologica=random.choice(PLATAFORMAS),
                vigencia=random.choice([90, 180, 360]),
                endereco_atuacao=fake.address(),
                qualificacao_minima=random.choice(qualificacao_opts),
                detalhes_qualificacao_minima=random.choice(AREAS_ESTUDO),
                conhecimento_desejavel=fake.paragraph(nb_sentences=2),
                conteudo_prova_teorica=fake.paragraph(nb_sentences=3),
                entrevista=fake.paragraph(nb_sentences=2),
                criterios_desempate=fake.paragraph(nb_sentences=2),
                status=status,
                criado_por=criador,
            )

            self._criar_cronograma(edital, base_data=date.today())
            self._criar_distribuicao(edital, experiencia_opts, nivel_config)
            editais.append(edital)

        self._espalhar_datas(EditalProvisorio.objects.filter(pk__in=[e.pk for e in editais]), dias=730)
        self._espalhar_datas(CronogramaEvento.objects.filter(edital__in=editais), dias=730)
        self._espalhar_datas(DistribuicaoBolsa.objects.filter(edital__in=editais), dias=730)

        self.stdout.write(f'  Editais: {len(editais)} criados')
        return editais

    def _criar_cronograma(self, edital, base_data=None):
        eventos = list(EditalProvisorio.EVENTO_CHOICES)
        selecionados = sorted(eventos, key=lambda x: x[0])[:random.randint(5, len(eventos))]
        base = base_data if base_data else date.today()
        if random.random() > 0.5:
            base = base - timedelta(days=random.randint(60, 365))
        else:
            base = base + timedelta(days=random.randint(30, 180))
        for idx, (codigo, nome) in enumerate(selecionados):
            dias_offset = idx * random.randint(10, 30)
            data_ref = (base + timedelta(days=dias_offset)).strftime('%d/%m/%Y')
            data_evento = base + timedelta(days=dias_offset)
            CronogramaEvento.objects.create(
                edital=edital,
                evento=codigo,
                data_referencia=data_ref,
                data_evento=data_evento,
                observacao=fake.sentence(nb_words=6) if random.random() > 0.5 else '',
                ordem=idx,
            )

    def _criar_distribuicao(self, edital, experiencia_opts, nivel_config):
        experiencias = [e[0] for e in experiencia_opts]
        experiencia_valores = nivel_config.get('experiencia_valores', {})
        val_min, val_max = _faixa_valores_nivel(nivel_config)
        vagas_restantes = edital.numero_vagas
        for exp in experiencias:
            if vagas_restantes <= 0:
                break
            qtd = random.randint(1, min(vagas_restantes, 5))
            vagas_restantes -= qtd
            faixa = experiencia_valores.get(exp, (val_min, val_max))
            valor = Decimal(str(round(random.uniform(float(faixa[0]), float(faixa[1])), 2)))
            DistribuicaoBolsa.objects.create(
                edital=edital,
                experiencia=exp,
                quantidade=qtd,
                valor_unitario=valor,
            )

    # ----------------------------------------------------------------
    # FASE 6: Aplicações em Editais
    # ----------------------------------------------------------------
    def _criar_aplicacoes(self, bolsistas, editais):
        count = 0
        editais_abertos = [e for e in editais if e.status == 'aberto']
        status_app = ['pendente', 'em_analise', 'aprovado', 'rejeitado']
        pesos_status = [0.35, 0.3, 0.25, 0.1]

        for edital in editais_abertos:
            # ~15% dos editais abertos ficam sem aplicações (caso-limite)
            if random.random() < 0.15:
                continue
            qtd = random.randint(1, min(self.qtd_aplicacoes, len(bolsistas)))
            candidatos = random.sample(bolsistas, qtd)
            for bolsista in candidatos:
                _, created = AplicacaoEdital.objects.get_or_create(
                    bolsista=bolsista,
                    edital=edital,
                    defaults={
                        'status': random.choices(status_app, weights=pesos_status)[0],
                    },
                )
                if created:
                    count += 1

        self.stdout.write(f'  Aplicações: {count} criadas')

    # ----------------------------------------------------------------
    # FASE 6b: Solicitações de Edição
    # ----------------------------------------------------------------
    def _criar_solicitacoes(self, bolsistas, managers):
        count = 0
        campos = ['telefone', 'cidade', 'rua', 'bairro', 'numero', 'estado']
        status_pool = ['pendente', 'aprovado', 'rejeitado']
        pesos = [0.5, 0.3, 0.2]
        if not bolsistas or not managers:
            self.stdout.write('  Solicitações: 0 criadas')
            return
        for _ in range(random.randint(3, max(3, len(bolsistas) // 2))):
            b = random.choice(bolsistas)
            m = random.choice(managers)
            s, created = SolicitacaoEdicao.objects.get_or_create(
                bolsista=b,
                campo=random.choice(campos),
                defaults={
                    'valor_original': getattr(b, random.choice(campos), '') or fake.word(),
                    'valor_novo': fake.sentence(nb_words=4),
                    'status': random.choices(status_pool, weights=pesos)[0],
                    'revisado_por': m if random.random() > 0.5 else None,
                },
            )
            if created:
                count += 1
        self.stdout.write(f'  Solicitações: {count} criadas')

    # ----------------------------------------------------------------
    # FASE 7: Avaliações
    # ----------------------------------------------------------------
    def _criar_avaliacoes(self, bolsistas, editais, managers):
        count = 0
        criterios = list(CriterioClassificacao.objects.filter(ativo=True))

        aplicacoes_avaliaveis = AplicacaoEdital.objects.filter(
            status__in=['em_analise', 'aprovado', 'rejeitado'],
        ).select_related('bolsista')

        for app in aplicacoes_avaliaveis:
            avaliador = random.choice(managers)
            criterios_para_avaliar = random.sample(
                criterios,
                min(random.randint(3, 8), len(criterios)),
            )
            for criterio in criterios_para_avaliar:
                if criterio.peso_maximo > 0:
                    # ~10% das avaliações cumulativas com 0 pontos
                    if random.random() < 0.1:
                        pontos = Decimal('0')
                    else:
                        pontos = Decimal(str(
                            round(random.uniform(0.5, float(criterio.peso_maximo)), 2)
                        ))
                else:
                    # ~20% dos critérios binários não atendidos (0 pontos)
                    if random.random() < 0.2:
                        pontos = Decimal('0')
                    else:
                        pontos = criterio.peso
                _, created = AvaliacaoBolsista.objects.get_or_create(
                    bolsista=app.bolsista,
                    criterio=criterio,
                    defaults={
                        'pontos': pontos,
                        'avaliado_por': avaliador,
                        'observacao': fake.sentence(nb_words=8)
                        if random.random() > 0.5 else '',
                    },
                )
                if created:
                    count += 1

        self.stdout.write(f'  Avaliações: {count} criadas')

    # ----------------------------------------------------------------
    # FASE 8: Notificações
    # ----------------------------------------------------------------
    def _criar_notificacoes(self, todos_users, bolsistas, managers):
        count = 0
        lido_opcoes = [True] * 6 + [False] * 4

        for b in bolsistas:
            if random.random() > 0.5:
                Notificacao.objects.create(
                    destinatario=b.user,
                    titulo='Cadastro criado com sucesso',
                    mensagem='Seu cadastro de bolsista foi registrado.',
                    tipo='cadastro',
                    lido=random.choice(lido_opcoes),
                )
                count += 1

        for m in managers:
            for _ in range(random.randint(0, 2)):
                b = random.choice(bolsistas)
                campo = random.choice(['telefone', 'cidade', 'rua'])
                Notificacao.objects.create(
                    destinatario=m,
                    titulo='Nova solicitação de edição',
                    mensagem=f'{b.user.nome_completo} solicitou edição do campo "{campo}".',
                    tipo='solicitacao',
                    lido=random.choice(lido_opcoes),
                )
                count += 1

            for _ in range(random.randint(0, 1)):
                Notificacao.objects.create(
                    destinatario=m,
                    titulo=fake.sentence(nb_words=5).rstrip('.'),
                    mensagem=fake.sentence(nb_words=12),
                    tipo='sistema',
                    lido=random.choice(lido_opcoes),
                )
                count += 1

        self.stdout.write(f'  Notificações: {count} criadas')

    # ----------------------------------------------------------------
    # FASE 9: Cálculo de Pontuação
    # ----------------------------------------------------------------
    def _calcular_pontuacoes(self, bolsistas):
        criterios = list(CriterioClassificacao.objects.filter(ativo=True))
        for b in bolsistas:
            tem_manual = AvaliacaoBolsista.objects.filter(bolsista=b).exists()
            if not tem_manual:
                _, pontuacao = calcular_pontuacao_previa(b, criterios)
                b.pontuacao_previa = Decimal(str(pontuacao))
                b.save(update_fields=['pontuacao_previa'])
        self.stdout.write(f'  Pontuações calculadas para bolsistas sem avaliação manual')
