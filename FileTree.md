# File Tree: Bolsistas

**Generated:** 8/11/2026, 11:06:06 AM
**Root Path:** `c:\Users\danillo.araujo\OneDrive - SESIMS\Projetos\Bolsistas`

```
├── 📁 .opencode
│   ├── 📁 plugins
│   │   └── 📄 graphify.js
│   ├── ⚙️ .gitignore
│   ├── ⚙️ opencode.json
│   ├── ⚙️ package-lock.json
│   └── ⚙️ package.json
├── 📁 .secrets
│   ├── 📄 cf_dns_api_token.txt
│   ├── 📄 db_password.txt
│   ├── 📄 groq_api_key.txt
│   ├── 📄 rabbitmq_password.txt
│   └── 📄 secret_key.txt
├── 📁 backend
│   ├── 📁 accounts
│   │   ├── 📁 migrations
│   │   │   ├── 🐍 0001_initial.py
│   │   │   ├── 🐍 0002_create_groups.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 views.py
│   ├── 📁 base
│   │   ├── 📁 migrations
│   │   │   └── 🐍 __init__.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 ai_client.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 context_processors.py
│   │   ├── 🐍 middleware.py
│   │   ├── 🐍 mixins.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 utils.py
│   │   └── 🐍 views.py
│   ├── 📁 cadastro
│   │   ├── 📁 management
│   │   │   ├── 📁 commands
│   │   │   │   └── 🐍 __init__.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 📁 migrations
│   │   │   ├── 🐍 0001_initial.py
│   │   │   ├── 🐍 0002_formacaoacademica_instituicao.py
│   │   │   ├── 🐍 0003_cadastro_numero_serie.py
│   │   │   ├── 🐍 0004_alter_cadastrobolsista_curriculo.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 cursos.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 tests_cadastro_detail.py
│   │   ├── 🐍 tests_gestao_documentos.py
│   │   ├── 🐍 tests_solicitacao_flow.py
│   │   ├── 🐍 urls.py
│   │   ├── 🐍 utils.py
│   │   └── 🐍 views.py
│   ├── 📁 classificacao
│   │   ├── 📁 migrations
│   │   │   ├── 🐍 0001_initial.py
│   │   │   ├── 🐍 0002_avaliacaobolsista.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 views.py
│   ├── 📁 config
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 asgi.py
│   │   ├── 🐍 celery.py
│   │   ├── 🐍 settings.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 wsgi.py
│   ├── 📁 editais
│   │   ├── 📁 migrations
│   │   │   ├── 🐍 0001_initial.py
│   │   │   ├── 🐍 0002_numero_serie_data_evento_inscricao.py
│   │   │   ├── 🐍 0003_data_entrevista_aplicacao.py
│   │   │   ├── 🐍 0004_remove_cronogramaevento_data_referencia_and_more.py
│   │   │   ├── 🐍 0005_remove_editalprovisorio_entrevista_and_more.py
│   │   │   ├── 🐍 0006_editalprovisorio_comentarios.py
│   │   │   ├── 🐍 0007_add_responsavel_field.py
│   │   │   ├── 🐍 0008_migrate_rascunho_status.py
│   │   │   ├── 🐍 0009_aplicacaoedital_nota_entrevista_and_more.py
│   │   │   ├── 🐍 0010_aplicacaoeditallog.py
│   │   │   ├── 🐍 0011_aplicacaoedital_documento_resultado_and_more.py
│   │   │   ├── 🐍 0012_editalprovisorio_deleted_at_and_more.py
│   │   │   ├── 🐍 0013_alter_editalprovisorio_status.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 📁 templatetags
│   │   │   ├── 🐍 __init__.py
│   │   │   └── 🐍 br_filters.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 ai_service.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 forms.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 tasks.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 tests_avaliacao_lote.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 views.py
│   ├── 📁 notifications
│   │   ├── 📁 migrations
│   │   │   ├── 🐍 0001_initial.py
│   │   │   └── 🐍 __init__.py
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 admin.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 models.py
│   │   ├── 🐍 signals.py
│   │   ├── 🐍 tests.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 views.py
│   ├── 📁 painel_bolsistas
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 ai_service.py
│   │   ├── 🐍 apps.py
│   │   ├── 🐍 tasks.py
│   │   ├── 🐍 urls.py
│   │   └── 🐍 views.py
│   └── 🐍 manage.py
├── 📁 docker
│   ├── 📄 entrypoint-celery.sh
│   └── 📄 entrypoint.sh
├── 📁 documentation
│   ├── 📁 docs
│   │   ├── 📁 universidades
│   │   │   ├── ⚙️ ies_brasil_parte_01.json
│   │   │   ├── ⚙️ ies_brasil_parte_02.json
│   │   │   ├── ⚙️ ies_brasil_parte_03.json
│   │   │   ├── ⚙️ ies_brasil_parte_04.json
│   │   │   ├── ⚙️ ies_brasil_parte_05.json
│   │   │   ├── ⚙️ ies_brasil_parte_06.json
│   │   │   ├── ⚙️ ies_brasil_parte_07.json
│   │   │   ├── ⚙️ ies_brasil_parte_08.json
│   │   │   ├── ⚙️ ies_brasil_parte_09.json
│   │   │   └── ⚙️ ies_brasil_parte_10.json
│   │   ├── ⚙️ lista_cursos.json
│   │   └── 📝 users.md
│   └── 📁 documentação
│       ├── 📝 Documentação.md
│       ├── 📝 PLANO_DESENVOLVIMENTO.md
│       ├── 📝 PRD.md
│       ├── 📝 accounts.md
│       ├── 📝 base.md
│       ├── 📝 cadastro.md
│       ├── 📝 classificacao.md
│       ├── 📝 editais.md
│       └── 📝 notifications.md
├── 📁 frontend
│   ├── 📁 static
│   │   ├── 📁 css
│   │   │   ├── 🎨 app.css
│   │   │   └── 🎨 sidebar.css
│   │   └── 📁 js
│   │       └── 📄 sidebar.js
│   └── 📁 templates
│       ├── 📁 accounts
│       │   ├── 📁 partials
│       │   │   └── 🌐 usuario_row.html
│       │   ├── 🌐 landing.html
│       │   ├── 🌐 login.html
│       │   ├── 🌐 password_change.html
│       │   ├── 🌐 password_change_done.html
│       │   ├── 🌐 password_reset.html
│       │   ├── 🌐 password_reset_complete.html
│       │   ├── 🌐 password_reset_confirm.html
│       │   ├── 🌐 password_reset_done.html
│       │   ├── 🌐 password_reset_email.html
│       │   ├── 📄 password_reset_subject.txt
│       │   └── 🌐 registro.html
│       ├── 📁 base
│       │   └── 🌐 home.html
│       ├── 📁 cadastro
│       │   ├── 📁 partials
│       │   │   ├── 🌐 formacao_section.html
│       │   │   └── 🌐 solicitacao_row.html
│       │   ├── 🌐 bolsista_form.html
│       │   ├── 🌐 cadastro_detail.html
│       │   ├── 🌐 cadastro_form.html
│       │   ├── 🌐 gestao_documentos.html
│       │   ├── 🌐 minhas_candidaturas.html
│       │   ├── 🌐 solicitacao_form.html
│       │   ├── 🌐 solicitacao_list.html
│       │   └── 🌐 solicitacao_multipla.html
│       ├── 📁 components
│       │   ├── 🌐 empty_state.html
│       │   ├── 🌐 pagination.html
│       │   └── 🌐 sidebar.html
│       ├── 📁 editais
│       │   ├── 📁 partials
│       │   │   ├── 🌐 analise_edital.html
│       │   │   ├── 🌐 avaliacao_documento_modal.html
│       │   │   ├── 🌐 avaliacao_edit_modal.html
│       │   │   ├── 🌐 compatibilidade_viewuser.html
│       │   │   ├── 🌐 resumo_edital.html
│       │   │   ├── 🌐 tabela_avaliacao.html
│       │   │   └── 🌐 task_running.html
│       │   ├── 🌐 aplicacao_edital_list.html
│       │   ├── 🌐 avaliacao.html
│       │   ├── 🌐 edital_confirm_delete.html
│       │   ├── 🌐 edital_detail.html
│       │   ├── 🌐 edital_excluidos_list.html
│       │   ├── 🌐 edital_form.html
│       │   ├── 🌐 edital_list.html
│       │   ├── 🌐 edital_pdf.html
│       │   └── 🌐 resultados.html
│       ├── 📁 notifications
│       │   ├── 📁 partials
│       │   │   ├── 🌐 bell.html
│       │   │   └── 🌐 notificacao_item.html
│       │   └── 🌐 notificacao_list.html
│       ├── 📁 painel
│       │   ├── 📁 partials
│       │   │   ├── 🌐 analise_bolsista.html
│       │   │   ├── 🌐 resumo_bolsista.html
│       │   │   └── 🌐 task_running.html
│       │   ├── 🌐 detalhe_bolsista.html
│       │   └── 🌐 trilha_bolsistas.html
│       └── 🌐 base.html
├── 📁 infrastructure
│   ├── 📁 .secrets.example
│   │   ├── 📄 cf_dns_api_token.txt
│   │   ├── 📄 db_password.txt
│   │   ├── 📄 google_api_key.txt
│   │   ├── 📄 groq_api_key.txt
│   │   ├── 📄 openai_api_key.txt
│   │   ├── 📄 rabbitmq_password.txt
│   │   └── 📄 secret_key.txt
│   ├── 📁 deploy
│   │   ├── 📄 stack-deploy.ps1
│   │   └── 📄 stack-deploy.sh
│   ├── ⚙️ azure-pipelines.yml
│   └── 📄 deploy.sh
├── ⚙️ .dockerignore
├── ⚙️ .env.example
├── ⚙️ .env.prod.example
├── ⚙️ .gitattributes
├── ⚙️ .gitignore
├── 📝 AGENTS.md
├── 🐳 Dockerfile
├── 📄 LICENSE
├── 📝 README.md
├── ⚙️ docker-compose.prod.yml
├── ⚙️ docker-compose.yml
└── 📄 requirements.txt
```

---
*Generated by FileTree Pro Extension*