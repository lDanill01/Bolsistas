# Editais

App responsável pela criação e gestão completa de editais (antigo edital provisório), incluindo cronograma e candidaturas.

## Constantes

### `NIVEL_BOLSA_CONFIG`
Dicionário que define 4 níveis de bolsa com suas qualificações, experiências e faixas de valor:
- **Nível 1**: Ensino Médio/Técnico/Graduação em Andamento — R$ 500 a R$ 2.000
- **Nível 2**: Graduação Completa/Tecnólogo — R$ 2.500 a R$ 10.000
- **Nível 3**: Mestrado — R$ 4.500 a R$ 12.000
- **Nível 4**: Doutorado — R$ 6.500 a R$ 14.000

## Modelos

### `EditalProvisorio`
Modelo principal do edital com estrutura completa:
- **Dados do Edital**: `nome_edital`, `area_estudo`, `detalhes_edital`
- **Instituto**: `nome_instituto` (7 opções: ISI Biomassa, IST Alimentos, IST Construção, FATEC CG, DR), `email_solicitante`, `telefone`, `endereco`
- **Configuração da Bolsa**: `modalidade_bolsa` (4 níveis), `qualificacao_minima`, `detalhes_qualificacao_minima`, `experiencia` (níveis de experiência que afetam o valor da bolsa), `modalidade_atuacao` (presencial/remota), `plataforma_tecnologica`, `vigencia` (dias, 15-1095), `endereco_atuacao`, `numero_vagas`, `valor_bolsa` (selecionado do range conforme nível+experiência), `valor_total_bolsa`, `valor_minimo`, `valor_maximo`
- **Detalhes Adicionais**: `modalidade_entrevista` (Presencial/Online), `conhecimento_desejavel`, `conteudo_prova_teorica`, `criterios_desempate`
- **Status**: Aberto, Encerrado, Em Análise, Cancelado
- **Metadados**: `criado_por` (FK User)

Propriedades computadas:
- `total_eventos` — Quantidade de eventos no cronograma

### `CronogramaEvento`
Eventos do cronograma do edital:
- `edital` — FK para EditalProvisorio
- `evento` — 7 tipos (início submissão, limite submissão, resultado aptas, prova teórica, entrevista, resultado final, outorga)
- `data_evento` — Data do evento
- `observacao`, `ordem`

### `AplicacaoEdital`
Candidatura de um bolsista a um edital:
- `bolsista` — FK para CadastroBolsista
- `edital` — FK para EditalProvisorio
- `status` — Pendente, Em Análise, Aprovado, Rejeitado
- `data_aplicacao` — Data/hora automática
- `unique_together` = (bolsista, edital) — Um bolsista só pode se candidatar uma vez

## Views

### `EditalProvisorioListView`
Listagem paginada com busca por instituto e filtro por status.

### `EditalProvisorioCreateView`
Criação com formulário principal + formset inline de Cronograma. Validações:
- Vigência entre 15 e 1095 dias
- Endereço de atuação obrigatório para modalidade remota
- Datas dos eventos devem ser estritamente crescentes
- Valor da bolsa deve estar dentro do range do nível e experiência selecionados

### `EditalProvisorioUpdateView`
Edição com o mesmo formset e validações da criação.

### `EditalProvisorioDetailView`
Visualização completa com todas as seções, cronograma (timeline visual) e configuração da bolsa.

### `EditalProvisorioDeleteView`
Exclusão com tela de confirmação.

### `edital_pdf_view`
Geração de PDF do edital usando xhtml2pdf (pisa).

### `AplicarEditalView`
Candidatura de bolsista a um edital. Dispara classificação automática baseada nos critérios ativos.

## Forms

### `EditalProvisorioForm`
Formulário principal com 19 campos. Atualiza dinamicamente as opções de `qualificacao_minima` conforme a `modalidade_bolsa` selecionada. Define `valor_minimo`/`valor_maximo` automaticamente pelo `NIVEL_BOLSA_CONFIG`.

### `CronogramaEventoForm`
Valida que evento e data sejam preenchidos juntos.

### Formset
- `CronogramaEventoFormSet` — Valida que as datas dos eventos sejam estritamente crescentes e que exista o evento de outorga

## Template Tags

### `br_filters`
- `br_money` — Formata valor numérico como moeda brasileira (R$ 1.234,56)

## URLs

| Path | View | Nome |
|------|------|------|
| `/` | EditalProvisorioListView | `edital_list` |
| `criar/` | EditalProvisorioCreateView | `edital_create` |
| `<pk>/` | EditalProvisorioDetailView | `edital_detail` |
| `<pk>/pdf/` | edital_pdf_view | `edital_pdf` |
| `<pk>/editar/` | EditalProvisorioUpdateView | `edital_update` |
| `<pk>/excluir/` | EditalProvisorioDeleteView | `edital_delete` |
| `<pk>/aplicar/` | AplicarEditalView | `aplicar_edital` |

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `models.py` | EditalProvisorio, CronogramaEvento, AplicacaoEdital, NIVEL_BOLSA_CONFIG |
| `views.py` | Views de CRUD, PDF e candidaturas |
| `forms.py` | Formulários e formsets inline |
| `urls.py` | Rotas da app |
| `admin.py` | Admin com inlines |
| `templatetags/br_filters.py` | Filtro de formatação monetária |
