# PLANO DE DESENVOLVIMENTO — PORTAL DA INOVAÇÃO (DJANGO)

## VISÃO GERAL

Plataforma SaaS para gestão de bolsistas, editais e classificação de candidatos.
Stack: Python + Django, PostgreSQL, Bootstrap 5, HTMX, Celery + Redis.

---

## ESTRUTURA FINAL DO PROJETO

```
bolsas/
├── .env
├── requirements.txt
├── manage.py
├── config/                  ← app principal Django (settings, urls, wsgi, celery)
├── base/                    ← model abstrato, mixins, utils compartilhados
├── accounts/                ← usuarios, autenticacao, roles
├── cadastro/                ← registro + dados pessoais/curriculo + solicitacoes edicao
├── editais/                 ← editais abertos e aplicacoes/inscricoes
├── classificacao/           ← pontuacao e avaliacao dos bolsistas
├── notifications/           ← e-mails e alertas in-app
├── dashboard/               ← visao gerencial, kanban, resumos
├── templates/
│   ├── base.html
│   ├── components/
│   ├── accounts/
│   ├── cadastro/
│   ├── editais/
│   ├── classificacao/
│   └── dashboard/
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── media/                   ← uploads
```

---

## DECISÕES DE ARQUITETURA

| Aspecto | Decisão |
|---|---|
| Login | Email como USERNAME_FIELD (sem username) |
| Model abstrato | `DataModel` com created_at + updated_at |
| Uploads | Media protegida via view com verificação de permissão |
| Edição de COMMON | Fluxo SolicitacaoEdicao (aprovação pelo MANAGER) |
| Classificação | Critérios flexíveis (model CriterioClassificacao editável por MANAGER) |
| E-mail | SMTP nativo Django + Celery para assíncrono |
| Apps na raiz | Sim, conforme instrucoes.md e PRD.md |
| Cadastro | App único (registro + dados bolsista + solicitação edição) |
| Idioma/fuso | pt-BR, America/Campo_Grande |

---

## DESIGN DOS MODELS

### base/models.py — DataModel (abstrato)

```python
class DataModel(models.Model):
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        abstract = True
```

### accounts/models.py — User + Perfil + DocumentoExterno

**User (AbstractUser)**
- email (USERNAME_FIELD, unique=True)
- nome_completo (CharField)
- REMOVER campo username
- REMOVER campo first_name, last_name

**Perfil (OneToOne → User)**
- user (OneToOneField → User)
- tipo (CharField, choices: ADMIN/MANAGER/COMMON)
- telefone (CharField)
- unidade (CharField, blank=True)

**DocumentoExterno**
- user (ForeignKey → User)
- arquivo (FileField)
- tipo (CharField, choices: RG/CPF/outro)

### cadastro/models.py — CadastroBolsista + Cursos + PosGrad + SolicitacaoEdicao

**CadastroBolsista**
- user (OneToOneField → User)
- endereco (TextField)
- data_nascimento (DateField, validador >= 18 anos)
- grau_academico (CharField, choices: fundamental/medio/superior/pos/mestrado/doutorado/pos_doutorado)
- curriculo (FileField, blank=True)
- foto (ImageField, blank=True)

**CursoSuperior**
- bolsista (ForeignKey → CadastroBolsista)
- instituicao (CharField)
- curso (CharField)
- grau (CharField)
- ano_conclusao (IntegerField, blank=True, null=True)

**PosGraduacao**
- bolsista (ForeignKey → CadastroBolsista)
- tipo (CharField, choices: pos_graduacao/mba/mestrado/doutorado/pos_doutorado)
- instituicao (CharField)
- area (CharField)
- ano_conclusao (IntegerField, blank=True, null=True)

**SolicitacaoEdicao**
- bolsista (ForeignKey → CadastroBolsista)
- campo (CharField) — nome do campo a ser editado
- valor_original (TextField)
- valor_novo (TextField)
- status (CharField, choices: pendente/aprovado/rejeitado, default=pendente)
- revisado_por (ForeignKey → User, blank=True, null=True)
- data_revisao (DateTimeField, blank=True, null=True)

### editais/models.py — Edital + AplicacaoEdital

**Edital**
- nome (CharField)
- descricao (TextField)
- requisitos (TextField)
- data_abertura (DateTimeField)
- data_fechamento (DateTimeField)
- status (CharField, choices: aberto/fechado/encerrado, default=aberto)
- criado_por (ForeignKey → User)

**AplicacaoEdital**
- bolsista (ForeignKey → CadastroBolsista)
- edital (ForeignKey → Edital)
- status (CharField, choices: pendente/em_analise/aprovado/rejeitado, default=pendente)
- data_aplicacao (DateTimeField, auto_now_add=True)
- UNIQUE_TOGETHER: (bolsista, edital)

### classificacao/models.py — Criterio + Classificacao + ClassificacaoCriterio

**CriterioClassificacao**
- nome (CharField)
- descricao (TextField, blank=True)
- peso (DecimalField)
- ativo (BooleanField, default=True)

**Classificacao**
- aplicacao (ForeignKey → AplicacaoEdital)
- classificador (ForeignKey → User)
- pontuacao_total (DecimalField)
- observacoes (TextField, blank=True)

**ClassificacaoCriterio**
- classificacao (ForeignKey → Classificacao)
- criterio (ForeignKey → CriterioClassificacao)
- nota (DecimalField)

### notifications/models.py — Notificacao

**Notificacao**
- destinatario (ForeignKey → User)
- titulo (CharField)
- mensagem (TextField)
- lido (BooleanField, default=False)
- tipo (CharField, choices: sistema/email/classificacao/cadastro)

---

## SPRINT 0 — SETUP E FUNDAÇÃO

### Atividades
1. Criar repositório git
2. Criar ambiente virtual Python
3. Instalar Django + dependências iniciais:
   - django
   - psycopg2-binary
   - python-decouple
   - django-htmx
   - Pillow
   - django-celery-beat
   - redis
   - celery
   - django-storages
4. `django-admin startproject config .`
5. Criar apps: `base`, `accounts`
6. Configurar `.env` com SECRET_KEY, DB, EMAIL, DEBUG
7. Integrar `python-decouple` no `settings.py`
8. Configurar PostgreSQL no settings
9. TIME_ZONE = 'America/Campo_Grande', LANGUAGE_CODE = 'pt-br'
10. AUTH_USER_MODEL = 'accounts.User'
11. Criar `base/models.py` com `DataModel` abstrato (created_at, updated_at)
12. Atualizar `requirements.txt`

### Entregável
- Projeto Django rodando com PostgreSQL
- Model abstrato base funcional
- Configurações de ambiente isoladas no .env

---

## SPRINT 1 — AUTENTICAÇÃO E ROLES

### Atividades
1. **User customizado** (AbstractUser): email como USERNAME_FIELD, sem username
2. **Perfil**: tipo (ADMIN/MANAGER/COMMON), telefone, unidade
3. **DocumentoExterno**: upload de RG/CPF para usuários externos
4. **Tela de registro**: nome, email, telefone, tipo(colaborador/bolsista/externo)
   - Se colaborador/bolsista → campo unidade (digitável)
   - Se externo → upload obrigatório de RG/CPF
5. **Tela de login** (email + senha)
6. **Landing page** (apresentação + botões login/cadastro)
7. **Middleware de proteção**: redirecionar não-logados para login
8. **Grupo padrão** para novos usuários: COMMON
9. **Mixins em base/mixins.py**: RoleRequiredMixin, ManagerRequiredMixin

### Entregável
- Sistema de login/cadastro funcional
- Roles definidos e protegidos
- Landing page acessível
- Usuários redirecionados após login

---

## SPRINT 2 — PERMISSÕES E SEGURANÇA

### Atividades
1. **RoleRequiredMixin**, **ManagerRequiredMixin**, **AdminRequiredMixin**: proteger views por role
2. **Proteção de media files**: view privada que verifica permissão do usuário
3. **urls.py**: rota media protegida (`/media/<path:path>`)
4. Middleware de proteção a arquivos/media: acesso somente por usuários com permissão
5. Revisar permissões nas views criadas nas sprints anteriores

### Entregável
- Acesso restrito por role
- Media files protegidos por permissão
- Views sensíveis protegidas por mixins

---

## SPRINT 3 — CADASTRO DE BOLSISTAS + SOLICITAÇÃO DE EDIÇÃO

### Atividades
1. **CadastroBolsista** model: endereco, data_nascimento(validador >=18), grau_academico, foto
2. **CursoSuperior** model: FK para bolsista, multi-instâncias
3. **PosGraduacao** model: FK para bolsista, tipo + instituição + área
4. **Upload de currículo** (FileField)
5. **SolicitacaoEdicao** model + views:
   - COMMON solicita edição de campo → MANAGER aprova/rejeita
6. **CBVs**: CreateView, DetailView, UpdateView (COMMON redireciona para solicitação)
7. Templates com Bootstrap 5 + HTMX para formulários dinâmicos (cursos/pós)

### Entregável
- CRUD de Bolsista funcional
- Upload de currículo, documentos e foto
- Fluxo de solicitação de edição implementado
- Forms dinâmicos com HTMX

---

## SPRINT 4 — EDITAIS

### Atividades
1. **Edital** model: nome, descrição, requisitos, datas, status
2. **Permissões**: MANAGER cria/edita, COMMON visualiza
3. **Views**: EditalListView, EditalDetailView, EditalCreateView, EditalUpdateView
4. Listagem com filtros (status, data)

### Entregável
- Sistema de editais com CRUD para MANAGER
- Listagem pública para COMMON
- Filtros e busca funcionais

---

## SPRINT 5 — APLICAÇÕES EM EDITAIS

### Atividades
1. **AplicacaoEdital** model: bolsista, edital, status, data
2. Validação: não permitir duplicidade (unique_together bolsista+edital)
3. **Views**: aplicar, acompanhar, cancelar
4. **Status flow**: pendente → em_analise → aprovado/rejeitado
5. Notificação in-app ao se inscrever

### Entregável
- Candidatura a editais funcional
- Acompanhamento de status pelo bolsista
- Prevenção de inscrição duplicada

---

## SPRINT 6 — CLASSIFICAÇÃO

### Atividades
1. **CriterioClassificacao** model: nome, descrição, peso, ativo (placeholder versátil)
2. **Classificacao** model: aplicacao(FK), classificador(User), pontuacao_total
3. **ClassificacaoCriterio** model: classificacao(FK), criterio(FK), nota
4. **Views**: MANAGER classifica bolsistas inscritos em editais
5. **Envio de e-mail** com resultado ao bolsista classificado

### Entregável
- Sistema de pontuação com critérios configuráveis
- Apenas MANAGER pode classificar
- Notificação automática ao bolsista

---

## SPRINT 7 — NOTIFICAÇÕES (CELERY)

### Atividades
1. Configurar Celery + Redis no `config/celery.py`
2. **Tasks assíncronas** para envio de e-mail
3. **Notificacao** model (in-app)
4. E-mails: resultado de classificação, confirmação de cadastro, aprovação de solicitação
5. Integração com e-mail nativo do Django (SMTP via .env)

### Entregável
- Celery + Redis configurados e funcionais
- Notificações in-app e por e-mail
- Tasks assíncronas para e-mails

---

## SPRINT 8 — DASHBOARD

### Atividades
1. **Dashboard ADMIN**: resumo geral (total usuários, editais, aplicações, classificações)
2. **Dashboard MANAGER**: editais abertos, aplicações pendentes, classificações a fazer
3. **Dashboard COMMON**: meus dados, editais aplicados, resultado classificação
4. Cards informativos, contadores

### Entregável
- Dashboard com visões por role
- Cards com contadores e resumos

---

## SPRINT 9 — UI/UX E FRONTEND

### Atividades
1. **base.html**: navbar, footer, estrutura responsiva
2. Paleta azul/branco, Bootstrap 5
3. Templates organizados por app
4. **HTMX**: formulários dinâmicos (cursos, pós), atualizações parciais
5. Componentes reutilizáveis (cards, alerts, tables)

### Entregável
- Interface responsiva e padronizada
- UX fluida com HTMX
- Componentes reutilizáveis

---

## SPRINT 10 — HARDENING E FINALIZAÇÃO

### Atividades
1. Revisar permissões por role
2. Validar acesso a media files
3. Configurar S3 para produção (django-storages)
4. Otimizar queries (select_related, prefetch_related)
5. Revisão geral de segurança

### Entregável
- Sistema pronto para produção
- Segurança revisada
- Performance otimizada

---

## ORDEM DE PRIORIDADE CRÍTICA

1. **Autenticação** — base de tudo
2. **Permissões/Segurança** — controle de acesso
3. **Cadastro** — core do sistema
4. **Editais** — funcionalidade principal
5. **Aplicações** — fluxo de candidatura
6. **Classificação** — critério de avaliação
7. **Notificações** — comunicação assíncrona

---

## RISCOS PRINCIPAIS

| Risco | Mitigação |
|---|---|
| Complexidade na modelagem | Manter models simples, evitar over-engineering |
| Falhas de permissão | Mixins dedicados (RoleRequiredMixin) |
| Uploads inseguros | View protegida de media + validação de tipo |
| SolicitaçãoEdição complexa | Fluxo direto: solicitar → aprovar/rejeitar |

---

## DEFINIÇÃO DE PRONTO (DoD)

Cada sprint deve entregar:
- Código funcional e executável
- Sem erros críticos
- Seguindo padrões definidos (PEP8, aspas simples, português, CBVs)
- Integrado ao fluxo do sistema
- requirements.txt atualizado

---

## REGRAS TÉCNICAS OBRIGATÓRIAS

- Login via e-mail (não username)
- Aspas simples no código
- Nomes em português do Brasil
- Class Based Views sempre que possível
- Timezone: America/Campo_Grande
- Idioma da interface: pt-BR
- Sem testes automatizados
- Um único settings.py
- Credenciais no .env
- Apps na raiz do projeto
- Models com created_at e updated_at
- Interface azul e branco com Bootstrap 5
- HTMX para interações reativas
- Sempre priorizar simplicidade + escalabilidade
