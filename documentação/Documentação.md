# Documentação — Bolsas SENAI-MS

## Nome do Projeto

**Bolsas SENAI-MS** (alternativamente referido como Portal da Inovação ou Projeto Bolsistas).

---

## Plataforma Tecnológica

Aplicação web responsiva, entregue via navegador, com arquitetura em três camadas (front-end, back-end e persistência). O sistema é conteinerizado e implantado sobre infraestrutura Docker, utilizando proxy reverso com terminação TLS automática.

---

## Tecnologias Utilizadas

### Back-end

| Tecnologia               | Versão          | Finalidade                                   |
|--------------------------|-----------------|----------------------------------------------|
| Python                   | 3.12+           | Linguagem de programação principal           |
| Django                   | 6.0             | Framework web                                |
| Celery                   | —               | Fila de tarefas assíncronas                  |
| RabbitMQ                 | 3               | Broker de mensagens do Celery                |
| Redis                    | 7               | Cache e backend de resultados do Celery      |
| django-celery-beat       | —               | Agendador de tarefas periódicas              |
| django-environ           | —               | Gerenciamento de variáveis de ambiente       |
| django-htmx              | —               | Integração HTMX com formulários Django       |
| openai (>=1.0)           | —               | SDK compatível com Groq API (Llama 3.3 70B)  |
| xhtml2pdf                | —               | Geração de documentos PDF                    |
| gunicorn                 | —               | Servidor WSGI para produção                  |
| whitenoise               | —               | Serviço de arquivos estáticos                |
| Pillow                   | —               | Processamento de imagens                     |
| django-storages          | —               | Suporte a armazenamento em nuvem (S3)        |
| psycopg2-binary          | —               | Adaptador PostgreSQL para Python             |

### Front-end

| Tecnologia  | Finalidade                                  |
|-------------|---------------------------------------------|
| HTML5 / CSS3| Estrutura e estilização das páginas         |
| Bootstrap 5 | Framework CSS responsivo                    |
| HTMX        | Interatividade dinâmica sem JavaScript      |

### Persistência

| Tecnologia  | Ambiente           |
|-------------|--------------------|
| PostgreSQL 16| Produção e desenvolvimento (Docker) |
| SQLite      | Desenvolvimento local sem Docker    |

### Infraestrutura

| Tecnologia        | Finalidade                                         |
|-------------------|-----------------------------------------------------|
| Docker            | Conteinerização dos serviços                       |
| Docker Compose    | Orquestração local (desenvolvimento)               |
| Docker Swarm      | Orquestração em produção (cluster)                 |
| Traefik v3        | Proxy reverso com certificados Let's Encrypt       |
| Cloudflare DNS    | Desafio DNS para emissão de certificados TLS       |

---

## Objetivo

Consolidar em uma plataforma digital única os processos de criação, publicação e gestão de editais de bolsas de estudo, bem como o cadastro e a avaliação de candidatos, para os institutos SENAI do estado de Mato Grosso do Sul (SESIMS).

O sistema visa substituir processos manuais e descentralizados por fluxos automatizados e rastreáveis, provendo suporte à tomada de decisão por meio de análises baseadas em inteligência artificial.

---

## Método de Desenvolvimento

O projeto foi concebido e executado segundo metodologia iterativa e incremental, estruturada em dez sprints sequenciais:

| Sprint   | Escopo                                                      |
|----------|-------------------------------------------------------------|
| Sprint 0 | Configuração do ambiente e fundação do projeto              |
| Sprint 1 | Autenticação e modelo de usuários customizado               |
| Sprint 2 | Sistema de permissões e segurança (RBAC)                    |
| Sprint 3 | Cadastro completo de candidatos (bolsistas)                 |
| Sprint 4 | Módulo de editais (criação, edição e publicação)            |
| Sprint 5 | Módulo de inscrições e aplicações                           |
| Sprint 6 | Módulo de classificação e pontuação de candidatos           |
| Sprint 7 | Sistema de notificações e tarefas assíncronas (Celery)      |
| Sprint 8 | Dashboards e painéis de acompanhamento                     |
| Sprint 9 | Refinamento de interface e experiência do usuário           |
| Sprint 10| Testes finais, ajustes e entrega                            |

### Padrões de Código

- Linguagem de programação e documentação em português
- Nomenclatura de variáveis, campos e modelos em português
- Conformidade com PEP8
- Views baseadas em classes (Class-Based Views)
- Configuração unificada em arquivo único (`settings.py`)
- Gerenciamento de dependências via `requirements.txt`

### Definição de Pronto (Definition of Done)

- Código funcional, sem erros críticos
- Adesão aos padrões estabelecidos
- Integração com os fluxos do sistema
- Dependências atualizadas em `requirements.txt`

---

## Aplicabilidade

O sistema aplica-se à gestão integral de programas de bolsas de estudo e fomento à pesquisa no âmbito dos institutos SENAI-MS, atendendo aos seguintes cenários:

- **Publicação de editais** — Criação de chamadas públicas com especificações detalhadas de requisitos, valores escalonados e cronograma de etapas
- **Captação de candidatos** — Registro estruturado de dados pessoais, formação acadêmica, experiência profissional e documentos comprobatórios
- **Processo seletivo** — Inscrição de candidatos, análise curricular, aplicação de provas e entrevistas, com registro de pontuações
- **Avaliação comparativa** — Classificação de candidatos com base em critérios configuráveis e suporte à decisão via inteligência artificial
- **Acompanhamento de bolsistas** — Monitoramento longitudinal de cada bolsista ao longo de sua trajetória ("Trilha do Bolsista")

---

## Possibilidades de Implementação

### Curto Prazo

1. **Armazenamento em nuvem (S3)** — Migrar o armazenamento de arquivos de mídia para Amazon S3 ou compatível, utilizando o módulo `django-storages` já presente no projeto
2. **Templates de e-mail HTML** — Substituir o backend de console por envio real de e-mails transacionais com formatação HTML
3. **Portal público de editais** — Expor uma página de acesso público com editais abertos, dispensando autenticação para consulta
4. **Exportação de relatórios PDF enriquecidos** — Gerar relatórios com gráficos e tabelas de desempenho dos candidatos utilizando bibliotecas como `matplotlib` ou `plotly`

### Médio Prazo

5. **Autenticação de dois fatores (2FA)** — Adicionar camada extra de segurança para perfis administrativos
6. **Operações em lote** — Permitir importação de candidatos via CSV e processamento em lote de inscrições e avaliações
7. **API REST** — Expor endpoints via Django REST Framework para consumo por aplicações móveis ou integrações externas
8. **Trilha de auditoria expandida** — Estender o modelo de log de alterações para todos os modelos do sistema

### Longo Prazo

9. **Suporte multitenant** — Adaptar a arquitetura para atender múltiplas instituições de ensino em uma única instância
10. **Provedores adicionais de IA** — Expandir a camada de IA para suportar OpenAI, Google Gemini e Anthropic Claude
11. **Workflow automatizado de etapas** — Implementar máquina de estados com transições automáticas e notificações vinculadas

---

## Capacidades

### Autenticação e Controle de Acesso

- Autenticação baseada em e-mail (sem nome de usuário)
- Modelo de usuário customizado com dados de perfil integrados
- Quatro grupos de acesso com permissões granulares: SuperUser, Manager, ExecuteUser e ViewUser
- Middleware de autenticação obrigatória com lista de exceções para rotas públicas

### Gestão de Editais

- Criação de editais com quatro níveis escalonados de bolsa (Nível 1 a 4)
- Configuração de requisitos de qualificação, experiência e valores por nível
- Cronograma automático com sete tipos de eventos
- Fluxo de status: em análise → aberto → encerrado/cancelado
- Encerramento automático via tarefa agendada (Celery Beat)
- Exportação do edital em formato PDF

### Cadastro de Candidatos

- Formulário completo com dados pessoais, endereço e contatos
- Registro de múltiplas formações acadêmicas (formset dinâmico)
- Registro de experiências profissionais
- Upload de documentos comprobatórios (currículo, RG, comprovante de residência)
- Indicadores booleanos de produção acadêmica (congressos, publicações, cursos, projetos)
- Fluxo de solicitação de edição cadastral com aprovação de gestor

### Inscrições e Avaliações

- Candidatura a editais abertos com validação de unicidade
- Registro de pontuações de prova teórica e entrevista
- Fluxo de status: pendente → em análise → aprovado/rejeitado
- Log de auditoria das alterações de avaliação (`AplicacaoEditalLog`)

### Classificação de Candidatos

- Critérios de pontuação configuráveis (12 tipos disponíveis)
- Pesos e limites máximos ajustáveis por critério
- Avaliação individual por candidato com rastreamento do avaliador
- Tipos de critério: graduação, mestrado, doutorado, projetos, publicações, congressos, cursos, entre outros

### Inteligência Artificial

- Sumarização de editais e perfis de candidatos
- Análise de compatibilidade entre candidatos e editais com gráficos de radar
- Sugestão automatizada de pontuações por critério com base no perfil do candidato
- Heurística de fallback para operação sem conectividade com a API de IA
- Processamento síncrono ou assíncrono (configurável via variável de ambiente)

### Painéis de Controle (Dashboards)

- Visão segmentada por perfil de usuário com métricas pertinentes
- Indicadores de total de candidatos, editais, inscrições e taxas de aprovação
- Listagem filtrável de candidatos com exportação CSV
- Trilha do Bolsista: histórico completo de cada candidato com pontuações e status

### Notificações

- Notificações in-app com indicador de leitura
- Integração com tarefas assíncronas (Celery) para envio de e-mails
- Componente visual de alerta (sino) com contagem de não lidas

### Infraestrutura e Implantação

- Ambiente de desenvolvimento conteinerizado (7 serviços via Docker Compose)
- Ambiente de produção com Docker Swarm, réplicas e health checks
- Proxy reverso Traefik com certificados SSL automáticos (Let's Encrypt)
- Segredos gerenciados via Docker Secrets
- Endpoint de health check para balanceamento de carga

---

## Estrutura do Projeto

```
bolsistas/
├── accounts/              # Autenticação e modelo User customizado
├── base/                  # Infraestrutura compartilhada (mixins, middleware, utilitários)
├── cadastro/              # Cadastro de bolsistas, formações e documentos
├── classificacao/         # Critérios de pontuação e avaliação de candidatos
├── config/                # Configurações Django (settings, urls, celery)
├── editais/               # Editais, cronogramas, inscrições e análises de IA
├── notifications/         # Sistema de notificações in-app
├── painel_bolsistas/      # Dashboards e acompanhamento
├── templates/             # Templates Django
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── media/                 # Arquivos enviados por usuários
├── docker/                # Scripts de entrada para contêineres
├── deploy/                # Scripts de implantação
├── documentação/          # Documentação por módulo
├── docker-compose.yml             # Ambiente de desenvolvimento
├── docker-compose.prod.yml        # Ambiente de produção (Swarm)
├── Dockerfile                     # Imagem Docker
├── requirements.txt               # Dependências Python
└── manage.py                      # CLI Django
```
