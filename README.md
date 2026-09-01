# Bolsas SENAI-MS

Sistema de gestao de bolsas de estudo para os institutos SENAI de Mato Grosso do Sul. Plataforma completa para criacao de editais, cadastro de candidatos, avaliacao, classificacao e acompanhamento de bolsistas.

## Funcionalidades

- **Editais** — Criacao, edicao, validacao e publicacao de editais com modalidades (nivel 1 a 4), requisitos de qualificacao, valores escalonados e cronograma de etapas (prova, entrevista, resultado)
- **Candidaturas** — Cadastro completo de bolsistas (dados pessoais, formacao, documentos comprobatorios), inscricao em editais e acompanhamento de status
- **Avaliacao** — Pagina de avaliacao por edital com nota de prova, data e nota de entrevista, bloqueadas conforme a disponibilidade do cronograma, anexo de documento do resultado e exclusao de candidaturas
- **Classificacao** — Criterios de pontuacao customizaveis (publicacoes, eventos, cursos) e avaliacao por criterio
- **IA** — Analise de editais e compatibilidade de candidatos via IA (Groq / Llama 3.3), com processamento assincrono (Celery)
- **Trilha do Bolsista** — Historico completo de candidaturas, notas, avaliacoes e acoes de IA por candidato
- **Gestao de Documentos** — Consulta de todos os documentos fornecidos, com filtro por tipo, usuario e data de envio
- **Resultados** — Listagem e download (CSV) dos resultados por edital
- **Permissoes** — Controle de acesso por grupos (SuperUser, Manager, ExecuteUser, ViewUser)
- **PDF** — Geracao de editais em PDF (xhtml2pdf)
- **Notificacoes** — Notificacoes in-app geradas somente para solicitacoes de edicao de dados de usuarios (`notifications/signals.py`)

## Stack

| Camada | Tecnologia |
|---|---|
| Web | Django 6.0 + HTMX 2 + Bootstrap 5 |
| Tarefas | Celery + RabbitMQ |
| Cache | Redis |
| DB | PostgreSQL 16 |
| IA | Groq API (Llama 3.3 70B, OpenAI-compatible) |
| Media | FileSystem (dev) / Azure Blob Storage (producao, via django-storages) |
| Infra (dev) | Docker + Docker Compose |
| Infra (prod) | Azure Container Apps via Azure DevOps (`azure-pipelines.yml`) |
| Legado (prod) | Docker Swarm + Traefik (`docker-compose.prod.yml`) |

## Pre-requisitos

- Python 3.12+
- Docker e Docker Compose (opcional, para desenvolvimento containerizado)
- PostgreSQL (ja incluso no docker-compose)
- RabbitMQ e Redis (ja inclusos no docker-compose)

## Setup Local (sem Docker)

```bash
git clone <repo-url>
cd Fork---Bolsistas

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows

pip install -r requirements.txt

cp .env.example .env
# Edite .env com suas credenciais (SECRET_KEY, DB_*, etc.)

python backend/manage.py migrate
python backend/manage.py createsuperuser
python backend/manage.py runserver
```

## Setup com Docker (recomendado)

```bash
git clone <repo-url>
cd Fork---Bolsistas

cp .env.example .env

docker compose up -d
docker compose exec web python backend/manage.py migrate
docker compose exec web python backend/manage.py createsuperuser

# Acesse http://bolsas.localhost
```

### Servicos Docker

| Servico | Porta | Descricao |
|---|---|---|
| web | 8000 | Django (runserver em dev / gunicorn em prod) |
| celery | — | Worker para tarefas assincronas (IA) |
| celery-beat | — | Agendador de tarefas periodicas |
| db | 5432 | PostgreSQL |
| redis | 6379 | Cache e backend de resultados Celery |
| rabbitmq | 5672 / 15672 | Broker de mensagens Celery |
| traefik | 80 / 8080 | Proxy reverso (dashboard em :8080) |

## Variaveis de Ambiente

| Variavel | Obrigatoria | Padrao | Descricao |
|---|---|---|---|
| `SECRET_KEY` | Sim | — | Chave secreta Django |
| `DEBUG` | Nao | `False` | Modo debug |
| `ALLOWED_HOSTS` | Nao | `localhost,127.0.0.1` | Hosts permitidos |
| `DB_ENGINE` | Nao | `sqlite3` | Engine do banco |
| `DB_NAME` | Nao | `db.sqlite3` | Nome do banco |
| `DB_HOST` | Nao | — | Host do PostgreSQL |
| `DB_USER` | Nao | — | Usuario do PostgreSQL |
| `DB_PASSWORD` | Nao | — | Senha do PostgreSQL |
| `CELERY_BROKER_URL` | Nao | `amqp://guest:guest@rabbitmq:5672//` | URL do broker |
| `CACHE_URL` | Nao | `redis://redis:6379/1` | URL do cache Redis |
| `GROQ_API_KEY` | Nao | — | Chave da API Groq para IA |
| `IA_ASYNC` | Nao | `False` | Processar IA de forma assincrona |
| `EMAIL_HOST` | Nao | `smtp.gmail.com` | Servidor SMTP |
| `AZURE_ACCOUNT_NAME` | Nao | — | Conta do Azure Blob Storage (media em producao) |
| `AZURE_CONTAINER` | Nao | — | Container do Azure Blob Storage |
| `AZURE_CONNECTION_STRING` | Nao | — | Credencial do storage (ou `AZURE_ACCOUNT_KEY`; se ausentes, usa managed identity) |

Segredos sensiveis podem ser injetados via Docker Secrets usando o sufixo `_FILE` (ex.: `SECRET_KEY_FILE=/run/secrets/secret_key`).

## Grupos de Usuario

| Grupo | Permissoes |
|---|---|
| **SuperUser** | Acesso total: admin Django, editais, avaliacao, gestao de documentos, solicitacoes |
| **Manager** | Criar/editar/validar editais, avaliar candidatos, trilha, gestao de documentos, revisar solicitacoes |
| **ExecuteUser** | Acesso operacional: avaliacao, trilha, gestao de documentos |
| **ViewUser** | Visualizar editais, candidatar-se, ver propria compatibilidade via IA |

Constantes de grupo (`base/mixins.py`): `GROUP_MANAGER='Manager'`, `GROUP_EXECUTE_USER='ExecuteUser'`, `GROUP_VIEW_USER='ViewUser'`. Os templates recebem `is_manager` / `is_execute_user` / `is_view_user` via `base/context_processors.perfil_context`.

## Design System / Frontend

- **Templates** em `frontend/templates/`; assets estaticos em `frontend/static/` (`app.css`, `sidebar.css`).
- **htmx 2** e Bootstrap 5 sao carregados em `base.html`; JS por pagina vai em `{% block extra_js %}` ou dentro de partials.
- **Layout compartilhado**: `base.html` inclui `frontend/templates/components/sidebar.html`. Os links da sidebar sao agrupados por permissao e recebem `active` via `request.resolver_match.url_name`.
- **Sidebar**: usa variaveis CSS em `:root` (ex.: `--sidebar-bg`, `--sidebar-text`). Fundo azul (`--sidebar-bg: #0E2C63`) com texto/icones brancos; itens ativos com indicador branco.
- **Footer**: fixo no rodape via `body` flex column (`min-height:100vh`) + `mt-auto` no `<footer>`, funcionando nos layouts autenticado e publico.
- **Media protegida**: `base/views.py:media_protegida` usa `default_storage` (FileSystem em dev, Azure Blob em prod quando `AZURE_ACCOUNT_NAME` + `AZURE_CONTAINER` estiverem definidos).
- **Texto de UI** em PT-BR; documentacao/README em ASCII (sem acentos).

## Knowledge Graph (graphify)

O projeto mantem um knowledge graph em `graphify-out/` com god nodes, estrutura de comunidades e relacoes entre arquivos.

- `graphify query "<pergunta>"` — subgrafo focado (mais leve que ler o repo inteiro)
- `graphify path "<A>" "<B>"` — relacao entre dois arquivos/conceitos
- `graphify explain "<conceito>"` — conceito isolado
- `graphify update .` — atualiza o grafo apos editar codigo (AST-only, sem custo de API)

Use `/graphify` para invocar o fluxo completo. Arquivos de grafo "sujos" apos hooks sao esperados e nao impedem o uso.

## Convencoes de Desenvolvimento

- **Testes**: usam o runner do Django (`python backend/manage.py test ...`) — nao ha pytest/tox. E necessario sobrescrever as env vars de DB/cache porque `settings.py` le `.env` (Postgres no host `db`):

  PowerShell:
  ```powershell
  $env:SECRET_KEY='x'; $env:DB_ENGINE='django.db.backends.sqlite3'; $env:DB_NAME='db.sqlite3'; $env:DB_HOST=''; $env:CACHE_URL='dummycache://'; $env:CELERY_BROKER_URL='memory://'
  python backend/manage.py test <label>
  ```
  Linux/macOS:
  ```bash
  SECRET_KEY=x DB_ENGINE=django.db.backends.sqlite3 DB_NAME=db.sqlite3 DB_HOST='' CACHE_URL=dummycache:// CELERY_BROKER_URL=memory:// python backend/manage.py test <label>
  ```

  - `base.tests.DiasUteisTests` tem 3 falhas pre-existentes (dependem de feriado/data) — nao sao regressoes.
  - Padrao de teste: `RequestFactory` + `View.as_view()(req)` + `r.render()`. Evite `Client` localmente (bug de `Context.__copy__` no Django 4.2 desta maquina).
- **Migracoes**: rode `python backend/manage.py migrate` completo (as migrations de `editais` dependem de estado de `accounts`/`cadastro`). `makemigrations` pode agrupar um `AlterField status` espurio em `editalprovisorio` (deriva de label `Fechado` vs `Encerrado` na migration 0001) — inspecione e remova ops nao relacionadas antes de commitar.
- **Dev container**: o entrypoint (`docker/entrypoint.sh`) roda `migrate` + `collectstatic` na subida. Apos editar codigo, bytecode stale pode causar erros confusos — limpe e reinicie:
  ```bash
  docker compose exec web python -c "import shutil,pathlib;[shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('/app').rglob('__pycache__')]"
  docker compose restart web
  ```
- **Notificacoes**: geradas ONLY para `SolicitacaoEdicao`. Nao re-adicione notificacoes para cadastro, avaliacao ou conclusao de resumo de IA (removido intencionalmente).
- **Arquivos de modelo**: muitos terminam com linha em branco final que deve ser preservada.

## Deploy

### Producao (Azure Container Apps)

O pipeline `infrastructure/azure-pipelines.yml` (Azure DevOps) faz CI (testes + build/push para ACR) e CD:

- Job de migracao (`bolsas-migrate`) roda `python backend/manage.py migrate` antes do deploy das apps
- Deploy de 3 Container Apps: `bolsas-web` (ingress), `bolsas-celery` e `bolsas-beat`
- Segredos via Key Vault / variable group e `secretref` no Container Apps
- Media persistida em Azure Blob Storage (role `Storage Blob Data Contributor` na managed identity, ou `AZURE_CONNECTION_STRING`)

### Legado (Docker Swarm)

`docker-compose.prod.yml` + `infrastructure/deploy.sh` / `infrastructure/deploy/` continuam disponiveis para a infraestrutura atual baseada em Swarm/Traefik.

## Estrutura do Projeto

```
.
├── backend/                    # Codigo Django (apps, config, manage.py)
│   ├── accounts/               # Model User customizado (email-based auth)
│   ├── base/                   # Mixins, middleware, context processors, utilitarios
│   ├── cadastro/               # Cadastro de bolsistas, formacoes, experiencias, solicitacoes
│   ├── classificacao/          # Criterios de pontuacao e avaliacao
│   ├── config/                 # Settings Django (settings.py, urls.py, wsgi.py, celery.py)
│   ├── editais/                # Editais, cronograma, candidaturas, avaliacao, resultados
│   ├── notifications/          # Sistema de notificacoes
│   ├── painel_bolsistas/       # Trilha do bolsista, detalhe e analise por IA
│   └── manage.py               # CLI Django
├── frontend/                   # Interface web
│   ├── templates/              # Templates Django (HTML)
│   └── static/                 # CSS, JS
├── infrastructure/             # CI/CD e deploy
│   ├── azure-pipelines.yml     # Pipeline Azure DevOps (CI/CD Container Apps)
│   ├── deploy.sh               # Script de deploy Docker Swarm
│   ├── deploy/                 # Scripts auxiliares de deploy
│   └── .secrets/               # Docker Secrets (valores reais)
├── documentation/              # Documentacao e dados
│   ├── docs/                   # Dados de cursos e universidades
│   └── documentação/           # Documentacao tecnica por modulo
├── graphify-out/               # Knowledge graph (graphify)
├── docker/                     # Entrypoints Docker (web + celery)
├── Dockerfile                  # Imagem Docker
├── docker-compose.yml          # Ambiente de desenvolvimento
├── docker-compose.prod.yml     # Ambiente de producao (Docker Swarm)
├── requirements.txt            # Dependencias Python
└── README.md
```

## Comandos Uteis

```bash
# Migracoes
docker compose exec web python backend/manage.py makemigrations
docker compose exec web python backend/manage.py migrate

# Collectstatic (apos editar CSS/JS)
docker compose exec web python backend/manage.py collectstatic --noinput
docker compose restart web

# Celery
docker compose exec celery celery -A config worker -l info

# Logs
docker compose logs -f web

# Shell Django
docker compose exec web python backend/manage.py shell

# Testes (requer override de env vars — ver secao Convencoes de Desenvolvimento)
docker compose exec web python backend/manage.py test

# Knowledge graph
graphify update .
```
