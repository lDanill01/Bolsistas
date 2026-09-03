from datetime import date
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from accounts.models import User
from cadastro.models import CadastroBolsista, ExperienciaProfissional, FormacaoAcademica
from editais.models import AplicacaoEdital, EditalProvisorio


USERS = [
    ('bolsista.ana@example.com', 'Ana Souza', 'Bolsista@123', 'ViewUser'),
    ('bolsista.carlos@example.com', 'Carlos Oliveira', 'Bolsista@123', 'ViewUser'),
    ('executor.maria@example.com', 'Maria Santos', 'Executor@123', 'ExecuteUser'),
    ('manager.joao@example.com', 'João Silva', 'Manager@123', 'Manager'),
]


class Command(BaseCommand):
    help = 'Cria dados de demonstração para testar os perfis e rotas da aplicação.'

    def handle(self, *args, **options):
        users = {}
        for email, nome, senha, grupo in USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'nome_completo': nome, 'is_active': True},
            )
            user.nome_completo = nome
            user.set_password(senha)
            user.save(update_fields=['nome_completo', 'password', 'is_active'])
            user.groups.set([Group.objects.get(name=grupo)])
            users[email] = user

        bolsistas = self._create_bolsistas(users)
        manager = users['manager.joao@example.com']
        editais = self._create_editais(manager)
        self._create_aplicacoes(bolsistas, editais)
        self._write_credentials()
        self.stdout.write(self.style.SUCCESS('Seed de demonstração criado/atualizado com sucesso.'))

    def _create_bolsistas(self, users):
        data = [
            (users['bolsista.ana@example.com'], date(1998, 4, 12), 'CG', 'MS', 'Tecnologia'),
            (users['bolsista.carlos@example.com'], date(1995, 9, 23), 'Dourados', 'MS', 'Engenharia'),
        ]
        result = []
        for user, nascimento, cidade, estado, area in data:
            cadastro, _ = CadastroBolsista.objects.update_or_create(
                user=user,
                defaults={
                    'telefone': '(67) 99999-0000', 'data_nascimento': nascimento,
                    'rua': 'Rua das Flores', 'numero': '100', 'bairro': 'Centro',
                    'cidade': cidade, 'estado': estado, 'participacao_projetos_anos': 3,
                    'participacao_congressos': True, 'resumo_anais': True,
                    'artigo_completo_anais': area == 'Engenharia',
                    'participacao_minicurso': True, 'treinamento': True,
                    'pontuacao_previa': Decimal('7.50'),
                },
            )
            FormacaoAcademica.objects.update_or_create(
                bolsista=cadastro, tipo='graduacao',
                defaults={'status': 'concluida', 'instituicao': 'UFMS', 'curso': area, 'area': area, 'ano_conclusao': 2022},
            )
            FormacaoAcademica.objects.update_or_create(
                bolsista=cadastro, tipo='curso_tecnico',
                defaults={'status': 'concluida', 'instituicao': 'SENAI-MS', 'curso': 'Informática', 'area': 'Tecnologia', 'ano_conclusao': 2018},
            )
            ExperienciaProfissional.objects.update_or_create(
                bolsista=cadastro, area_atuacao=area,
                defaults={'anos_experiencia': 3},
            )
            result.append(cadastro)
        return result

    def _create_editais(self, manager):
        base = {
            'area_estudo': 'Tecnologia e Inovação', 'detalhes_edital': 'Edital de demonstração para testes visuais.',
            'nome_instituto': 'ist_eficiencia', 'email_solicitante': manager.email,
            'telefone': '(67) 3000-0000', 'endereco': 'Av. Afonso Pena, 1000', 'numero_vagas': 3,
            'modalidade_bolsa': 'nivel_2', 'experiencia': '1 Ano de Experiência', 'valor_bolsa': Decimal('4500'),
            'valor_total_bolsa': Decimal('54000'), 'valor_minimo': Decimal('4500'), 'valor_maximo': Decimal('6500'),
            'modalidade_atuacao': 'presencial', 'plataforma_tecnologica': 'Python e Django', 'vigencia': 180,
            'endereco_atuacao': 'Campo Grande - MS', 'qualificacao_minima': 'Graduação Completa',
            'detalhes_qualificacao_minima': 'Tecnologia, Engenharia ou áreas relacionadas', 'conhecimento_desejavel': 'Desenvolvimento web',
            'conteudo_prova_teorica': 'Lógica e programação', 'modalidade_entrevista': 'online',
            'criterios_desempate': 'Maior nota na entrevista', 'criado_por': manager, 'responsavel': manager,
        }
        specs = [('Bolsa de Tecnologia - Aberto', 'aberto'), ('Bolsa de Tecnologia - Em Análise', 'em_analise'), ('Bolsa de Tecnologia - Encerrado', 'encerrado')]
        editais = [EditalProvisorio.objects.update_or_create(nome_edital=nome, defaults={**base, 'status': status})[0] for nome, status in specs]
        for edital in editais:
            if not edital.cronograma.exists():
                edital.calcular_cronograma()
        return editais

    def _create_aplicacoes(self, bolsistas, editais):
        for i, cadastro in enumerate(bolsistas):
            for j, edital in enumerate(editais[:2]):
                AplicacaoEdital.objects.update_or_create(
                    bolsista=cadastro, edital=edital,
                    defaults={'status': 'aprovado' if j == 0 else 'em_analise', 'nota': Decimal('8.50') if j == 0 else None, 'nota_entrevista': Decimal('9.00') if j == 0 else None},
                )

    def _write_credentials(self):
        path = Path('documentation/demo-users.md')
        path.write_text('# Usuários de demonstração\n\nUso local.\n\n| Perfil | E-mail | Senha |\n|---|---|---|\n' + ''.join(f'| {g} | {e} | {s} |\n' for e, _, s, g in USERS), encoding='utf-8')
