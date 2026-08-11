# Classificação

App responsável pela definição de critérios de pontuação e classificação dos candidatos.

## Modelos

### `CriterioClassificacao`
Critério de pontuação configurável:
- `nome` — Nome descritivo
- `tipo_criterio` — 12 tipos: graduação, mestrado, doutorado, projetos_pesquisa, congressos, resumo_anais, artigo_completo_anais, artigo_nacional, artigo_internacional, livro_patente, minicurso, treinamento
- `descricao` — Descrição do critério
- `peso` — Peso (pontos por unidade)
- `peso_maximo` — Teto de pontuação (para critérios cumulativos como projetos)
- `ativo` — Flag de critério ativo

### `Classificacao`
Pontuação atribuída a uma candidatura:
- `aplicacao` — FK para AplicacaoEdital
- `classificador` — FK para User (quem classificou)
- `pontuacao_total` — Soma das notas × pesos
- `observacoes` — Justificativa/observações

### `ClassificacaoCriterio`
Nota individual por critério dentro de uma classificação:
- `classificacao` — FK para Classificacao
- `criterio` — FK para CriterioClassificacao
- `nota` — Valor da nota para este critério

## Views

### `CriterioListView`
Listagem de critérios de classificação.

### `CriterioCreateView` / `CriterioUpdateView`
CRUD de critérios.

### `ClassificacaoListView`
Listagem de classificações.

### `ClassificacaoCreateView`
Criação de classificação para uma candidatura, com notas por critério.

### `ClassificacaoDetailView`
Visualização detalhada da classificação.

### `CsvImportView`
Template view para importação de dados via CSV.

## URLs

| Path | View | Nome |
|------|------|------|
| `criterios/` | CriterioListView | `criterio_list` |
| `criterios/criar/` | CriterioCreateView | `criterio_create` |
| `criterios/<pk>/editar/` | CriterioUpdateView | `criterio_update` |
| (vazio) | ClassificacaoListView | `classificacao_list` |
| `criar/` | ClassificacaoCreateView | `classificacao_create` |
| `<pk>/` | ClassificacaoDetailView | `classificacao_detail` |
| `importar-csv/` | CsvImportView | `csv_import` |

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | CriterioClassificacao, Classificacao, ClassificacaoCriterio |
| `views.py` | Views de CRUD de critérios e classificações |
| `urls.py` | Rotas da app |
