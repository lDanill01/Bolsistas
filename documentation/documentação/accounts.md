# Accounts

App responsável pela autenticação, gestão de usuários e perfis.

## Modelos

### `User`
Modelo de usuário customizado (herda `AbstractUser`):
- `email` — Campo único usado como identificador de login (USERNAME_FIELD)
- `nome_completo` — Nome completo do usuário
- Sem campo `username` (removido)

Utiliza `UserManager` customizado.

### `Perfil`
Vincula um usuário a um tipo de acesso:
- `user` — OneToOne com `User`
- `tipo` — ADMIN, MANAGER ou COMMON
- `telefone`, `unidade`, `data_nascimento` — Dados complementares

### `DocumentoExterno`
Upload de documentos do usuário (RG, CPF, etc.):
- `user` — FK para User
- `arquivo` — FileField
- `tipo` — RG, CPF ou OUTRO

## Views

### `LandingPageView`
Página inicial (landing page) para usuários não autenticados. Redireciona para home se já autenticado.

### `CustomLoginView`
Tela de login usando email como credencial.

### `RegistroView`
Formulário de cadastro público que cria User e Perfil.

### `HomeView`
Dashboard pós-login com estatísticas contextualizadas por função:
- **ADMIN**: total de usuários, pendentes, editais, aplicações, classificações
- **MANAGER**: editais abertos, pendentes de avaliação
- **COMMON**: editais abertos, aplicações e classificações próprias

### `AprovarUsuarioView`
Aprova um usuário pendente (ativa `is_active`). Suporta HTMX para atualização parcial.

## URLs

| Path | View | Nome |
|------|------|------|
| `/` | LandingPageView | `landing` |
| `/login/` | CustomLoginView | `login` |
| `/registro/` | RegistroView | `registro` |
| `/sair/` | LogoutView | `logout` |
| `/home/` | HomeView | `home` |
| `/usuarios/<pk>/aprovar/` | AprovarUsuarioView | `aprovar_usuario` |

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | User, Perfil, DocumentoExterno |
| `views.py` | Views de autenticação e dashboard |
| `urls.py` | Rotas da app |
