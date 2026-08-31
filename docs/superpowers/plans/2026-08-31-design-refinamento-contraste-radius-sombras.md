# Refinamento Contraste Radius Sombras Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Suavizar contraste alto, harmonizar radius (8/10/12) e aplicar sombras minimalistas modernas mantendo DS.

**Architecture:** Edição direta de `app.css` (tokens, radius, shadows) e `sidebar.css` (radius, shadows). Sem Python. Verificação via grep + collectstatic.

**Tech Stack:** CSS, Django static, Docker

## Global Constraints

- Manter DS cores/tipografia: --blue-900 #0E2C63, --orange-500 #E84910, Neo Sans Pro
- --bg-body #F7F9FB → #F2F4F8
- --text-main #131C2E → #232E45
- --border-color #E3E7ED → #E6EAF0
- Radius: btn 8px, form 8px, badge 8px, dropdown 12px, card 12px, sidebar link 10px
- Shadows: --shadow-soft 0 1px 2px rgba(14,44,99,.04), 0 4px 12px rgba(14,44,99,.06); --shadow-soft-hover 0 4px 16px rgba(14,44,99,.08), 0 2px 8px rgba(14,44,99,.06); --shadow-menu 0 8px 24px rgba(14,44,99,.10), 0 2px 8px rgba(14,44,99,.06)

---

### Task 1: Contraste Suavizado

**Files:**
- Modify: `frontend/static/css/app.css:18-23`
- Modify: `frontend/static/css/sidebar.css:132` (content-wrapper bg)

**Interfaces:**
- Consumes: DS tokens
- Produces: fundo/texto suavizados que Tasks 2-3 usam

- [ ] **Step 1: Verificar contraste atual (deve FAIL depois)**

```bash
grep -q "#F7F9FB" frontend/static/css/app.css && echo "F7F9FB existe" || echo "não"
grep -q "#131C2E" frontend/static/css/app.css && echo "131C2E existe" || echo "não"
```

- [ ] **Step 2: Editar app.css tokens**

```css
:root {
    --bg-body: #F2F4F8;
    --bg-card: #FFFFFF;
    --bg-sidebar: #0E2C63;
    --text-main: #232E45;
    --text-muted: #5A667D;
    --border-color: #E6EAF0;
    --radius: 8px;
}
```

E em `sidebar.css:132` trocar `background: var(--n-50)` por `background: #F2F4F8` ou `var(--bg-body)`.

- [ ] **Step 3: Verificar**

```bash
grep -q "#F2F4F8" frontend/static/css/app.css && echo PASS || echo FAIL
grep -q "#232E45" frontend/static/css/app.css && echo PASS || echo FAIL
```

- [ ] **Step 4: Commit**

```bash
git add frontend/static/css/app.css frontend/static/css/sidebar.css
git commit -m "feat: contraste suavizado — bg #F2F4F8, text #232E45, border #E6EAF0"
```

---

### Task 2: Radius Harmonizado 8/10/12

**Files:**
- Modify: `frontend/static/css/app.css:101-227`
- Modify: `frontend/static/css/sidebar.css:102`

**Interfaces:**
- Consumes: Task 1 contraste
- Produces: radius coeso

- [ ] **Step 1: Verificar radius antigo**

```bash
grep -q "border-radius: 4px" frontend/static/css/app.css && echo "4px existe" || echo "não"
```

- [ ] **Step 2: Editar**

Em `app.css`:

```css
.btn { border-radius: 8px; }
.form-control, .form-select { border-radius: 8px; }
.badge { border-radius: 8px; }
.card { border-radius: 12px; }
.card-header { border-radius: 12px 12px 0 0 !important; }
.dropdown-menu { border-radius: 12px; }
.alert { border-radius: 10px; }
```

Em `sidebar.css`:

```css
#sidebar .sidebar-link { border-radius: 10px; }
```

- [ ] **Step 3: Verificar**

```bash
grep -q "border-radius: 8px" frontend/static/css/app.css && echo PASS || echo FAIL
grep -q "border-radius: 10px" frontend/static/css/sidebar.css && echo PASS || echo FAIL
```

- [ ] **Step 4: Commit**

```bash
git add frontend/static/css/app.css frontend/static/css/sidebar.css
git commit -m "feat: radius harmonizado 8/10/12"
```

---

### Task 3: Sombras Minimalistas Modernas

**Files:**
- Modify: `frontend/static/css/app.css:79-87,254`
- Modify: `frontend/static/css/sidebar.css:140`

**Interfaces:**
- Consumes: Tasks 1-2
- Produces: sombras soft

- [ ] **Step 1: Verificar sombra antiga**

```bash
grep -q "shadow-sm" frontend/static/css/app.css && echo "shadow-sm existe" || echo "não"
```

- [ ] **Step 2: Editar**

Em `app.css` adicionar vars e aplicar:

```css
:root {
    --shadow-soft: 0 1px 2px rgba(14,44,99,.04), 0 4px 12px rgba(14,44,99,.06);
    --shadow-soft-hover: 0 4px 16px rgba(14,44,99,.08), 0 2px 8px rgba(14,44,99,.06);
    --shadow-menu: 0 8px 24px rgba(14,44,99,.10), 0 2px 8px rgba(14,44,99,.06);
}
.card {
    box-shadow: var(--shadow-soft);
    transition: box-shadow .18s ease, transform .18s ease;
}
.card:hover { box-shadow: var(--shadow-soft-hover); transform: translateY(-1px); }
.dropdown-menu { box-shadow: var(--shadow-menu); backdrop-filter: blur(8px); border: 1px solid #E6EAF0; }
```

Em `sidebar.css`:

```css
.top-navbar { box-shadow: 0 1px 3px rgba(14,44,99,.04); }
#sidebar { box-shadow: none; }
```

- [ ] **Step 3: Verificar**

```bash
grep -q "shadow-soft" frontend/static/css/app.css && echo PASS || echo FAIL
grep -q "backdrop-filter" frontend/static/css/app.css && echo PASS || echo FAIL
```

- [ ] **Step 4: Commit + collectstatic**

```bash
git add frontend/static/css/app.css frontend/static/css/sidebar.css
git commit -m "feat: sombras minimalistas modernas soft + hover lift"
docker compose exec web python backend/manage.py collectstatic --noinput --clear
docker compose restart web
graphify update .
```

