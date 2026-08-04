# AGENTS.md

## graphify (knowledge graph)

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Stack

- Single Django 6 project (`config/`), apps: `accounts`, `base`, `cadastro`, `classificacao`, `editais`, `notifications`, `painel_bolsistas`. Custom `accounts.User` uses email login (`USERNAME_FIELD='email'`).
- Permissions via `base/mixins.py` group mixins; group constants: `GROUP_MANAGER='Manager'`, `GROUP_EXECUTE_USER='ExecuteUser'`, `GROUP_VIEW_USER='ViewUser'`. Templates get `is_manager`/`is_execute_user`/`is_view_user` from `base/context_processors.perfil_context`.
- Celery autodiscovers tasks in `editais/tasks.py` and `painel_bolsistas/tasks.py`; beat schedule is in `config/settings.py` (`CELERY_BEAT_SCHEDULE`).
- Media: `FileSystemStorage` by default; switches to Azure Blob only when `AZURE_ACCOUNT_NAME` + `AZURE_CONTAINER` are set (config/settings.py). `base/views.py:media_protegida` uses `default_storage` (works for both).
- Notifications are generated ONLY for `SolicitacaoEdicao` (`notifications/signals.py`). Do not re-add notifications for cadastro, avaliação, or AI-summary completion — that was intentionally removed.

## Commands

- Tests use Django's runner (`python manage.py test ...`); there is no pytest/tox. **You must override DB/cache env vars** because `config/settings.py` reads `.env` (which points to Postgres at host `db`):
  - PowerShell: `$env:SECRET_KEY='x'; $env:DB_ENGINE='django.db.backends.sqlite3'; $env:DB_NAME='db.sqlite3'; $env:DB_HOST=''; $env:CACHE_URL='dummycache://'; $env:CELERY_BROKER_URL='memory://'; python manage.py test <label>`
  - Linux/macOS: `SECRET_KEY=x DB_ENGINE=django.db.backends.sqlite3 DB_NAME=db.sqlite3 DB_HOST='' CACHE_URL=dummycache:// CELERY_BROKER_URL=memory:// python manage.py test <label>`
- `base.tests.DiasUteisTests` has 3 pre-existing failures (holiday/date-dependent); they are NOT regressions from your changes. The rest of the suite should pass.
- Follow the existing test pattern: `RequestFactory` + `View.as_view()(req)` + `r.render()` (see `editais/tests_avaliacao_lote.py`). Avoid the test `Client` locally — it hits a Django 4.2 `Context.__copy__` bug on this machine.
- Docker dev: `docker compose up -d`. The web entrypoint (`docker/entrypoint.sh`) runs `migrate` + `collectstatic` on start.
- After code edits, stale bytecode in the dev container can cause confusing errors (e.g. `AttributeError`/missing column that exists). Clear it and restart: `docker compose exec web python -c "import shutil,pathlib;[shutil.rmtree(p,ignore_errors=True) for p in pathlib.Path('/app').rglob('__pycache__')]"` then `docker compose restart web`.
- Use full `python manage.py migrate` (not per-app) — `editais` migrations depend on `accounts`/`cadastro` state.
- `makemigrations` can bundle a spurious `AlterField status` on `editalprovisorio` (pre-existing label drift `Fechado` vs `Encerrado` in migration 0001). Inspect generated migrations and drop unrelated ops before committing them.

## Conventions / gotchas

- UI text is PT-BR; README/docs are mostly ASCII (no accents).
- Shared layout: `templates/base.html` includes `templates/components/sidebar.html`. Sidebar links are group-gated and get `active` via `request.resolver_match.url_name` — match that pattern for new pages.
- htmx 2 is loaded in `base.html`; per-page JS goes in `{% block extra_js %}` or inside partials. The batch evaluation form (`templates/editais/partials/tabela_avaliacao.html`) is a single `<form>` — do not nest another `<form>` inside it (use buttons + fetch).
- New management pages: gate with `ManagerOrExecuteRequiredMixin` (solicitações uses `ManagerRequiredMixin`) and add the sidebar link under the "Gestão" section.
- Many model files end with a trailing blank line that must be preserved (a previous edit removed one and broke the file).

## Deploy

- Azure DevOps target: `azure-pipelines.yml` — CI (tests + Docker build/push to ACR), CD deploys `bolsas-web`/`bolsas-celery`/`bolsas-beat` to Azure Container Apps and runs a `bolsas-migrate` migration job before the apps.
- Legacy prod (current fallback): Docker Swarm via `docker-compose.prod.yml` + `deploy.sh` / `deploy/`.
- Secrets: settings `read_secret()` prefers `NAME_FILE` env (Docker Secrets / ACA `secretref`) over plain env.
