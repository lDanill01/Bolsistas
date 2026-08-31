# Design: Refinamento Contraste, Radius e Sombras — Minimalista Moderno

**Data:** 2026-08-31 (iteração após híbrido C+A)
**Status:** Aprovado (3/3 seções)
**Base:** `docs/superpowers/specs/2026-08-31-design-ajuste-cores-gradientes-icone-design.md` (sidebar clara flat, logo 22px, topbar linha única, botões flat, cards flat)
**Objetivo:** Reduzir contraste alto (texto/fundo/cards/CTAs chapados), harmonizar arredondamentos desajustados e trocar sombras por versão minimalista moderna, mantendo DS cores/tipografia.

---

## 1. Contraste Suavizado (mantém DS)

Tokens DS preservados, apenas uso ajustado:

| Token | Antes | Depois | Onde |
|-------|-------|--------|------|
| `--bg-body` | `#F7F9FB` (n-50) | `#F2F4F8` | `app.css:18` + `sidebar.css` content-wrapper |
| `--bg-card` | `#FFFFFF` | `#FFFFFF` | cards — mantém, cria separação vs fundo levemente acinzentado |
| `--border-color` | `#E3E7ED` (n-200) | `#E6EAF0` | bordas — suaviza linha |
| `--text-main` | `#131C2E` (n-900) | `#232E45` (n-800) | `app.css:21` + `body` — reduz peso 15% |
| `--text-muted` | `#5A667D` (n-600) | `#5A667D` | mantém |
| CTA laranja/azul | `#E84910` / `#164194` | idem | mas hover transição suave `background .18s ease` sem salto, sem shadow |

Efeito: página menos "estourada", cards flutuam sobre fundo, texto menos pesado, CTAs ainda hierárquicos mas não gritam.

---

## 2. Radius Harmonizado (escala 8/10/12)

Antes desajustado: btn 4px, form 4px, badge 6px, dropdown 8px, card 14px, sidebar link 8px — sem ritmo.

Depois coeso:

| Componente | Antes | Depois | Arquivo |
|------------|-------|--------|---------|
| `.btn` | `4px` | `8px` (radius-md) | `app.css:103` |
| `.form-control/.form-select` | `4px` | `8px` | `app.css:206` |
| `.badge` | `6px` | `8px` | `app.css:227` |
| `.card` / `.card-header` | `14px (--radius-lg)` | `12px` | `app.css:82,88` + `fonts-senai.css:55` se necessário redefinir local |
| `.dropdown-menu` | `8px` | `12px` | `app.css:254` |
| `#sidebar .sidebar-link` | `8px` | `10px` | `sidebar.css:102` |
| `.alert` / `.progress` | `8px/999px` | mantém | já coeso |

Mantém DS (`--radius-sm 4px`, `--radius-md 8px`, `--radius-lg 12px` após ajuste local 14→12).

---

## 3. Sombras Minimalistas Modernas (criativo)

Antes: `shadow-sm` único ou `shadow-md` pesado, ou `box-shadow:none` chapado.

Depois — sombras soft com cor base azul institucional `14,44,99` para harmonizar com marca, blur generoso, opacidade baixa:

```css
/* Cards — profundidade suave */
--shadow-soft: 0 1px 2px rgba(14,44,99,.04), 0 4px 12px rgba(14,44,99,.06);
--shadow-soft-hover: 0 4px 16px rgba(14,44,99,.08), 0 2px 8px rgba(14,44,99,.06);
/* Dropdown/menus — flutuação */
--shadow-menu: 0 8px 24px rgba(14,44,99,.10), 0 2px 8px rgba(14,44,99,.06);
/* Topbar — linha sutil */
--shadow-topbar: 0 1px 3px rgba(14,44,99,.04);
```

Aplicação:

- `.card` → `box-shadow: var(--shadow-soft); transition: box-shadow .18s ease, transform .18s ease;` + hover `box-shadow: var(--shadow-soft-hover); transform: translateY(-1px);` (`app.css:82-87`)
- `.dropdown-menu` → `box-shadow: var(--shadow-menu); border: 1px solid #E6EAF0; backdrop-filter: blur(8px);` (moderno, `app.css:254`)
- `.top-navbar` → `box-shadow: var(--shadow-topbar);` (`sidebar.css:140`)
- `#sidebar` → `box-shadow: none; border-right: 1px solid #E6EAF0;` (limpo)
- `.btn` → sem shadow (flat), hover apenas cor — mantém minimalismo

Efeitos criativos mantendo DS: leve `translateY(-1px)` nos cards, `backdrop-filter` nos menus, transições `ease` suaves.

---

## 4. Arquivos

- `frontend/static/css/app.css` — tokens bg/text/border, radius btn/form/badge/card/dropdown, shadows card/dropdown
- `frontend/static/css/sidebar.css` — radius sidebar-link, shadow topbar/sidebar
- `frontend/static/css/fonts-senai.css` — se precisar ajustar `--radius-lg 14→12` e `--shadow-*` globais, mas pode ficar local em app.css

Sem Python/migrações.

---

## 5. Verificação

- Visual: `localhost:8000` fundo levemente acinzentado vs cards brancos, texto menos pesado, botões 8px, cards com sombra suave e hover lift, dropdown com blur.
- `grep -q "border-radius: 4px" app.css` → deve falhar (trocado para 8px) exceto onde intencional
- `collectstatic --clear` + `docker compose restart web` + `graphify update .`
