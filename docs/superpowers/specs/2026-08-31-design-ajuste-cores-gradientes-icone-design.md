# Design: Ajuste de Cores, Gradientes e Ícone Sidebar — Híbrido C+A

**Data:** 2026-08-31  
**Autor:** Brainstorming com usuário  
**Status:** Aprovado por seções (5/5)  
**Preview:** `design/preview-abordagens.html` (3 abordagens, escolhida C + secundário de A)  
**Escopo:** Apenas frontend estático (CSS/tokens + HTML leve). Sem lógica Python/migrações.

---

## 1. Objetivo

Corrigir insatisfação visual:

- **Cores muito saturadas** — laranja #E84910 dominante e gradientes pesados (sidebar `linear-gradient(180deg,#0E2C63→#123675)`, `card-dark` `135deg`, thumb gradiente, topbar faixa 4 cores) geram fadiga.
- **Ícone desproporcional** — logo PNG `1755×485` exibido a `28px` com `background:#fff; padding:4px 8px; border-radius:6px; box-shadow` em `frontend/static/css/sidebar.css:51-58` estica e polui.

Solução escolhida: **Híbrido C+A** — base **C Minimal neutro** (fundo neutro, sidebar clara, tudo flat, laranja só no CTA) + **secundário sólido azul de A** (`#164194`).

Critério de sucesso: cores sóbrias flat, zero gradientes pesados, logo proporcional 20-22px sem caixa, verificado em `/`, `/login`, `/registro`, sidebar `active` e `collectstatic`.

---

## 2. Sistema Visual — Tokens

Mantém `frontend/static/css/fonts-senai.css` (Neo Sans Pro + `--blue-*`, `--orange-*`, `--n-*`, `--shadow-*`) mas uso muda:

| Token | Valor | Uso |
|-------|-------|-----|
| `--bg-body` | `#F7F9FB` (n-50) | fundo geral (`app.css:18`) |
| `--bg-card` | `#FFFFFF` | cards |
| `--border-color` | `#E3E7ED` (n-200) | bordas |
| `--text-main` | `#131C2E` (n-900) | texto |
| `--text-muted` | `#5A667D` (n-600) | secundário |
| `--blue-900` | `#0E2C63` | títulos `h1/h2`, active text |
| `--blue-700` (secundário A) | `#164194` | `.btn-secondary` sólido |
| `--orange-500` | `#E84910` | APENAS `.btn-primary` + `sidebar active indicator` (1 CTA/tela) |
| `--shadow` | `sm` apenas (`0 1px 2px rgba(19,28,46,.06)`) | remove `shadow-md` de cards hover |

Regras:

- Remover todos `linear-gradient` pesados: `sidebar.css:23`, `app.css:96` (card-dark), `app.css:102` (thumb), `sidebar.css:151` (topbar 4 cores).
- Topbar faixa vira linha única `3px` `#E84910` (`sidebar.css:146-152`).
- Shadows: apenas `shadow-sm`; hover `translateY` reduzido ou removido.

---

## 3. Layout

### Sidebar (`frontend/static/css/sidebar.css` + `frontend/templates/components/sidebar.html`)

- Fundo: `#F7F9FB` (clara, C) em vez de `linear-gradient`. `border-right:1px solid #E3E7ED`.
- Texto: `#3B475F` (`n-700`), section `#7C879C` (`.sidebar-section`).
- Active: `background:#E4EFFB` (`blue-100`), `border-left:3px solid #E84910`, `color:#0E2C63`, `font-weight:700`.
- Brand: remover `background:#fff; border-radius:6px; padding:4px 8px; box-shadow:0 1px 4px rgba(0,0,0,.2)` de `.brand-logo`. Novo: `height:20-22px; width:auto; object-fit:contain; display:block; flex-shrink:0;` Sem caixa. `gap:10px`, `.brand-text` `13px`, `small` `10px` `letter-spacing:.08em`.
- Largura mantém `268px`, transição inalterada.

### Topbar (`sidebar.css:136-153`)

- `background:#fff`, `border-bottom:1px solid #E3E7ED`, `box-shadow:0 1px 3px rgba(19,28,46,.04)`.
- `::before` linha única `#E84910` `3px` em vez de `linear-gradient(90deg, blue-500 0 25%, sesi-green 25% 50%, ...)`.

### Footer (`app.css:276-282`)

- Mantém `background:var(--blue-900)` flat, `border-top:4px solid var(--orange-500)` (sem gradiente).

### Content

- `background:var(--n-50)` (`#content-wrapper` `sidebar.css:132`).

---

## 4. Componentes

### Botões (`app.css:106-176`)

- `.btn-primary`: `background:#E84910; border-color:#E84910; color:#fff;` **flat** — remover `box-shadow:0 2px 0 var(--orange-700)` e hover shadow pesado. Hover: `background:#CF4110` apenas.
- `.btn-secondary` (híbrido A): `background:#164194; border-color:#164194; color:#fff;` sólido (não outline de C). Hover `#123675`. Remover `box-shadow:0 2px 0 var(--blue-900)`.
- `.btn-outline-*`, `.btn-ghost`: mantêm flat com `border 1.5px`, hover `background:var(--blue-50)`.

### Cards (`app.css:79-103`)

- `.card`: `background:#fff; border:1px solid #E3E7ED; border-radius:14px; shadow-sm;` hover `shadow-sm` (não `shadow-md`), sem `transform`.
- `.card-curso .thumb`: remover `linear-gradient(135deg,var(--blue-700),var(--blue-500))` → `background:#E4EFFB` flat ou `#F7F9FB`.
- `.card-dark`: de `linear-gradient(135deg,var(--blue-900),var(--blue-700))` para `background:#fff; border:1px solid #E3E7ED; color:var(--n-900);` ou, quando necessário escuro, `background:#0E2C63` flat sem gradiente.

### Tabelas/Forms (`app.css:195-231`)

- `.table thead th` `background:#F7F9FB` flat, sem gradiente.
- `.form-control:focus` mantém `border-color:var(--blue-500); box-shadow:0 0 0 3px var(--blue-100)` sutil.

---

## 5. Arquivos Afetados

- `frontend/static/css/app.css` — tokens, buttons, cards, tables, forms, footer
- `frontend/static/css/sidebar.css` — sidebar, topbar, brand-logo
- `frontend/static/css/fonts-senai.css` — sem mudança (tokens fonte já ok)
- `frontend/templates/components/sidebar.html` — sem mudança estrutural, apenas classe/estilo reflete novo CSS
- `frontend/templates/base.html` — sem mudança estrutural (topbar já via CSS)
- `design/preview-abordagens.html` — preview mantido para referência

Sem migrações, sem `requirements.txt`, sem Python.

---

## 6. Verificação

1. `python backend/manage.py collectstatic --noinput --clear` dentro do container
2. `docker compose restart web` + limpar `__pycache__`
3. `graphify update .`
4. Teste manual: `/` (landing), `/login`, `/registro`, `home` com sidebar active, `editais/`, `resultados/` — checar cores sóbrias, ausência de gradientes, logo 20-22px sem caixa, contraste AA.
5. `docker compose exec web ls /app/staticfiles/css/` confirma `app.css` com `#E84910` apenas em primary, `fonts-senai.css` coletado.

---

## 7. Fora de Escopo

- Troca de logo PNG (1755×485) por SVG/monograma — fica para futuro se necessário.
- Mudança de paleta completa (ex: trocar laranja por outro) — manter DS oficial.
- Refatoração de `base.html` layout ou lógica Django.
