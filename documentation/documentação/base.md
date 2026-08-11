# Base

App fundamental do projeto que fornece a infraestrutura compartilhada por todas as outras apps.

## Modelos

### `DataModel`
Modelo abstrato base com campos de auditoria:
- `created_at` — Data/hora de criação (auto)
- `updated_at` — Data/hora de última atualização (auto)

Todos os modelos das demais apps herdam deste modelo.

## Middleware

### `LoginRequiredMiddleware`
Redireciona usuários não autenticados para a página de login. Possui uma lista de paths públicos permitidos: `/`, `/login/`, `/registro/`, `/admin/`, `/static/`, `/media/`.

## Mixins

### `RoleRequiredMixin`
Restringe acesso baseado no tipo de perfil (`tipo`) do usuário.

### `ManagerRequiredMixin`
Restringe acesso a usuários com perfil `ADMIN` ou `MANAGER`.

### `AdminRequiredMixin`
Restringe acesso apenas a usuários com perfil `ADMIN`.

## Views

### `media_protegida`
View que serve arquivos de mídia com controle de acesso, validando se o usuário tem permissão para acessar o arquivo solicitado. Bloqueia path traversal.

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | `DataModel` (base abstrata) |
| `middleware.py` | `LoginRequiredMiddleware` |
| `mixins.py` | Mixins de controle de acesso |
| `views.py` | `media_protegida` |
