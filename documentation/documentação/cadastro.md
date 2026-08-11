# Cadastro

App responsável pelo cadastro de bolsistas, formação acadêmica e solicitações de edição.

## Modelos

### `CadastroBolsista`
Dados do candidato a bolsista:
- `user` — OneToOne com `User`
- `telefone` — Telefone de contato
- `data_nascimento` — Data de nascimento (>= 18 anos)
- `rua`, `numero`, `bairro`, `cidade`, `estado` — Endereço estruturado
- `curriculo` — Upload de currículo (FileField)
- `foto` — Upload de foto (ImageField)
- Campos booleanos de critérios acadêmicos/profissionais:
  - `participacao_projetos_anos` — Anos de experiência
  - `participacao_congressos`, `resumo_anais`, `artigo_completo_anais`
  - `artigo_cientifico_nacional`, `artigo_cientifico_internacional`
  - `livro_patente`, `participacao_minicurso`, `treinamento`
- `pontuacao_previa` — Pontuação calculada automaticamente

### `FormacaoAcademica`
Formação acadêmica unificada (substitui CursoSuperior e PosGraduacao):
- `bolsista` — FK para CadastroBolsista
- `tipo` — Ensino Médio, Graduação, Curso Técnico, Especialização, Pós-Graduação, MBA, Mestrado, Doutorado, Pós-Doutorado
- `status` — Em Andamento ou Concluída (não se aplica a Ensino Médio)
- `instituicao` — Nome da instituição
- `curso` — Nome do curso (opcional)
- `area` — Área de concentração (opcional)
- `ano_conclusao` — Ano de conclusão (opcional)

### `SolicitacaoEdicao`
Solicitações de alteração de dados que requerem aprovação:
- `bolsista` — FK para CadastroBolsista
- `campo` — Nome do campo a ser editado
- `valor_original`, `valor_novo` — Valores antes/depois
- `status` — Pendente, Aprovado, Rejeitado
- `revisado_por` — FK para User (gestor que revisou)
- `data_revisao` — Data da revisão

## Views

### `CadastroCreateView`
Criação do cadastro com formulário estruturado em seções: Dados Pessoais, Endereço, Dados Acadêmicos (formset de FormacaoAcademica), Outras Informações.

### `BolsistaCreateView`
Criação de um novo bolsista (usuário + cadastro) por gestores (`Manager`), executores (`ExecuteUser`) ou superusuários. Gera uma senha aleatória e redireciona para o detalhe do cadastro criado.

### `CadastroDetailView`
Visualização do cadastro com seções organizadas.

### `CadastroUpdateView`
Edição do cadastro por gestor.

### `CadastroListView`
Listagem de cadastros (gestores).

### `formacao_add` / `formacao_remove`
Views HTMX para adicionar/remover formações acadêmicas. Recalcula pontuação.

### `SolicitacaoCreateView`, `SolicitacaoListView`, `SolicitacaoMultiplaView`, `SolicitacaoRevisarView`
Fluxo de solicitações de edição e revisão por gestores.

### `AdminDashboardView`
Dashboard administrativo com estatísticas gerais.

## Utilitários

### `calcular_pontuacao_previa`
Calcula pontuação com base nos critérios ativos e nas formações acadêmicas do bolsista.

## URLs

| Path | View | Nome |
|------|------|------|
| `criar/` | CadastroCreateView | `cadastro_create` |
| `novo/` | BolsistaCreateView | `bolsista_create` |
| (vazio) | CadastroDetailView | `cadastro_detail` |
| `<pk>/` | CadastroDetailView | `cadastro_detail_pk` |
| `<pk>/editar/` | CadastroUpdateView | `cadastro_update_pk` |
| `<pk>/formacao/add/` | formacao_add | `formacao_add` |
| `<pk>/formacao/<pk>/remove/` | formacao_remove | `formacao_remove` |
| `lista/` | CadastroListView | `cadastro_list` |
| `solicitar/` | SolicitacaoMultiplaView | `solicitacao_criar` |
| `solicitacoes/` | SolicitacaoListView | `solicitacao_list` |
| `solicitacoes/<pk>/revisar/` | SolicitacaoRevisarView | `solicitacao_revisar` |
| `admin/` | AdminDashboardView | `admin_dashboard` |

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | CadastroBolsista, FormacaoAcademica, SolicitacaoEdicao |
| `views.py` | Views de CRUD, formações via HTMX, solicitações e dashboard |
| `urls.py` | Rotas da app |
| `utils.py` | `calcular_pontuacao_previa` |
