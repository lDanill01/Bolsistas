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
- **Notificacoes** — Notificacoes in-app geradas somente para solicitacoes de edicao de dados de usuarios

## Stack

| Camada | Tecnologia |
|---|---|
| Web | Django 6.0 + HTMX + Bootstrap 5 |
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

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Setup com Docker (recomendado)

```bash
git clone <repo-url>
cd Fork---Bolsistas

cp .env.example .env

docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser

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

## Deploy

### Producao (Azure Container Apps)

O pipeline `azure-pipelines.yml` (Azure DevOps) faz CI (testes + build/push para ACR) e CD:

- Job de migracao (`bolsas-migrate`) roda `python manage.py migrate` antes do deploy das apps
- Deploy de 3 Container Apps: `bolsas-web` (ingress), `bolsas-celery` e `bolsas-beat`
- Segredos via Key Vault / variable group e `secretref` no Container Apps
- Media persistida em Azure Blob Storage (role `Storage Blob Data Contributor` na managed identity, ou `AZURE_CONNECTION_STRING`)

### Legado (Docker Swarm)

`docker-compose.prod.yml` + `deploy.sh` / `deploy/` continuam disponiveis para a infraestrutura atual baseada em Swarm/Traefik.

## Estrutura do Projeto

```
.
├── accounts/          # Model User customizado (email-based auth), Perfil, DocumentoExterno
├── base/              # Mixins, middleware, context processors, utilitarios, media protegida
├── cadastro/          # Cadastro de bolsistas, formacoes, experiencias, anexos, solicitacoes, gestao de documentos
├── classificacao/     # Criterios de pontuacao e avaliacao por criterio
├── config/            # Settings Django (settings.py, urls.py, wsgi.py, celery.py)
├── docker/            # Entrypoints Docker (web + celery)
├── editais/           # Editais, cronograma, candidaturas, avaliacao, resultados
├── notifications/     # Sistema de notificacoes (somente solicitacoes)
├── painel_bolsistas/  # Trilha do bolsista, detalhe e analise por IA
├── static/            # Arquivos estaticos
├── templates/         # Templates Django (componentes de sidebar/paginacao, etc.)
├── documentacao/      # Documentacao tecnica por modulo
├── docs/              # Dados de cursos e universidades
├── azure-pipelines.yml      # Pipeline Azure DevOps (CI/CD Container Apps)
├── docker-compose.yml       # Ambiente de desenvolvimento
├── docker-compose.prod.yml  # Ambiente de producao (Docker Swarm)
├── Dockerfile               # Imagem Docker
├── requirements.txt         # Dependencias Python
└── manage.py                # CLI Django
```

## Comandos Uteis

```bash
# Migracoes
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Celery
docker compose exec celery celery -A config worker -l info

# Logs
docker compose logs -f web

# Shell Django
docker compose exec web python manage.py shell

# Testes
docker compose exec web python manage.py test
```
