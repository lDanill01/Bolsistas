# Design Ajuste Cores Gradientes Icone Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar híbrido C+A (minimal neutro + secundário azul) removendo gradientes saturados e corrigindo logo sidebar desproporcional (1755x485 → 20-22px sem caixa).

**Architecture:** Edição direta de 2 CSS principais (`app.css`, `sidebar.css`) para flat sóbrio; sidebar clara #F7F9FB com active #E4EFFB; topbar linha única laranja; botões flat sem shadows. Sem Python/migrações. Verificação via `collectstatic` + `docker compose restart`.

**Tech Stack:** Django 6, Bootstrap 5.3.3, CSS puro, Neo Sans Pro (fonts-senai.css), Docker Compose

## Global Constraints

- Manter `fonts-senai.css` inalterado (tokens já definidos: --blue-900 #0E2C63, --blue-700 #164194, --orange-500 #E84910, --n-50 #F7F9FB, --n-200 #E3E7ED, etc)
- Laranja #E84910 APENAS em .btn-primary e sidebar active indicator (1 CTA/tela) — regra DS
- Zero gradientes pesados — remover linear-gradient de sidebar, card-dark, thumb, topbar 4 cores
- Shadows apenas sm (0 1px 2px rgba(19,28,46,.06))
- Logo sidebar: height 20-22px, object-fit:contain, sem background/padding/box-shadow, gap 10px
- Não quebrar `base.html` estrutura (apenas CSS)
- Após cada edição: `graphify update .` e `collectstatic`

---

### Task 1: Corrigir Sidebar Clara + Logo Proporcional

**Files:**
- Modify: `frontend/static/css/sidebar.css:1-35`
- Modify: `frontend/static/css/sidebar.css:51-58` (brand-logo)
- Modify: `frontend/static/css/sidebar.css:82-115` (section/link active)
- Test: `frontend/static/css/sidebar.css` visual

**Interfaces:**
- Consumes: tokens de `fonts-senai.css` (--blue-900, --orange-500, --n-50, --n-200)
- Produces: sidebar clara flat que Task 2 (topbar) e Task 3 (buttons) consomem como contexto visual

- [ ] **Step 1: Criar teste de regressão visual (grep)**

```bash
# deve PASSAR após fix: sem gradiente, sem caixa branca, logo 22px
grep -q "linear-gradient.*sidebar-bg" frontend/static/css/sidebar.css && echo "FAIL gradiente ainda existe" || echo "PASS sem gradiente"
grep -q "background: #fff;.*border-radius: 6px;.*padding: 4px 8px" frontend/static/css/sidebar.css && echo "FAIL caixa branca ainda existe" || echo "PASS sem caixa"
grep -q "height: 22px" frontend/static/css/sidebar.css && echo "PASS logo 22px" || echo "FAIL logo não corrigido"
```

- [ ] **Step 2: Run teste — deve FAIL antes do fix (confirma problema)**

Run: `bash -c "grep -q linear-gradient frontend/static/css/sidebar.css && echo FAIL || echo PASS"`
Expected: FAIL (gradiente existe em linha 23)

- [ ] **Step 3: Implementar sidebar clara flat**

Em `frontend/static/css/sidebar.css:1-15` substituir `:root` sidebar vars:

```css
:root {
    --sidebar-bg: #F7F9FB; /* C minimal — clara */
    --sidebar-bg-hover: #EFF2F6; /* n-100 */
    --sidebar-bg-active: #E4EFFB; /* blue-100 */
    --sidebar-text: #3B475F; /* n-700 */
    --sidebar-text-active: #0E2C63; /* blue-900 */
    --sidebar-border: #E3E7ED; /* n-200 */
    --sidebar-section: #7C879C; /* n-500 */
    --sidebar-active-indicator: #E84910;
    --topbar-bg: #ffffff;
    --topbar-border: #E3E7ED;
    --topbar-text: #131C2E;
    --topbar-icon: #5A667D;
}
```

Em `sidebar.css:20-34` trocar:

```css
#sidebar {
    width: 268px;
    min-width: 268px;
    background: var(--sidebar-bg);
    color: var(--sidebar-text);
    transition: margin-left 0.3s ease, width 0.3s ease, min-width 0.3s ease;
    z-index: 1040;
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0; left: 0; bottom: 0;
    overflow-y: auto;
    overflow-x: hidden;
    border-right: 1px solid var(--sidebar-border);
}
```

Em `sidebar.css:51-58` corrigir logo:

```css
#sidebar .sidebar-brand .brand-logo {
    height: 22px;
    width: auto;
    flex-shrink: 0;
    object-fit: contain;
    display: block;
    background: none;
    border-radius: 0;
    padding: 0;
    box-shadow: none;
}
```

Em `sidebar.css:37-49` ajustar brand:

```css
#sidebar .sidebar-brand {
    padding: 1rem 1.25rem;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    border-bottom: 1px solid var(--sidebar-border);
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--sidebar-text-active);
    background: transparent;
}
#sidebar .sidebar-brand .brand-text {
    font-family: var(--font-display);
    font-weight: 900;
    font-style: italic;
    letter-spacing: -0.02em;
    line-height: 1;
    font-size: 13px;
}
#sidebar .sidebar-brand .brand-text small {
    display:block;
    font-family: var(--font-body);
    font-style: normal;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: .08em;
    text-transform: uppercase;
    opacity:.75;
    margin-top:2px;
}
```

Em `sidebar.css:82-115` atualizar section/link:

```css
#sidebar .sidebar-section {
    padding: 0.9rem 1.25rem 0.35rem;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    color: var(--sidebar-section);
    font-weight: 700;
}
#sidebar .sidebar-link {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.62rem 1.05rem;
    margin: 0.16rem 0.65rem;
    color: var(--sidebar-text);
    text-decoration: none;
    font-size: 0.88rem;
    font-weight: 500;
    transition: background 0.18s ease, color 0.18s ease;
    border-radius: 8px;
    border-left: 3px solid transparent;
}
#sidebar .sidebar-link:hover {
    background: var(--sidebar-bg-hover);
    color: var(--sidebar-text-active);
}
#sidebar .sidebar-link.active {
    background: var(--sidebar-bg-active);
    color: var(--sidebar-text-active);
    font-weight: 700;
    border-left-color: var(--sidebar-active-indicator);
    box-shadow: none;
}
```

- [ ] **Step 4: Run teste — deve PASS**

Run: `bash -c "grep -q 'background: var(--sidebar-bg);' frontend/static/css/sidebar.css && echo PASS || echo FAIL"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/static/css/sidebar.css
git commit -m "feat: sidebar clara flat + logo 22px sem caixa (C+A)"
```

---

### Task 2: Simplificar Topbar + Footer Flat

**Files:**
- Modify: `frontend/static/css/sidebar.css:136-153` (topbar)
- Modify: `frontend/static/css/app.css:274-282` (footer)
- Test: visual topbar linha única

**Interfaces:**
- Consumes: sidebar clara de Task 1
- Produces: topbar/footer flat que Task 4 usa para contraste

- [ ] **Step 1: Teste topbar 4 cores ainda existe (deve FAIL depois)**

```bash
grep -q "sesi-green" frontend/static/css/sidebar.css && echo "FAIL 4 cores ainda existe" || echo "PASS linha única"
```

- [ ] **Step 2: Run — deve mostrar FAIL antes**

Run: `grep -c "sesi-green" frontend/static/css/sidebar.css`
Expected: 1 (linha 151 ainda tem)

- [ ] **Step 3: Implementar topbar linha única + footer flat**

Em `sidebar.css:136-153`:

```css
.top-navbar {
    background: var(--topbar-bg);
    border-bottom: 1px solid var(--topbar-border);
    padding: 0.55rem 1.25rem;
    box-shadow: 0 1px 3px rgba(19,28,46,.04);
    position: sticky;
    top:0;
    z-index: 1020;
}
.top-navbar::before{
    content:'';
    position:absolute;
    top:0; left:0; right:0;
    height:3px;
    background: var(--orange-500);
}
```

Em `app.css:274-282` remover qualquer gradiente (já é flat, manter):

```css
.footer-senai {
    background: var(--blue-900);
    color: var(--blue-100);
    border-top: 4px solid var(--orange-500);
}
```

- [ ] **Step 4: Verify**

Run: `grep -q "linear-gradient.*sesi-green" frontend/static/css/sidebar.css && echo FAIL || echo PASS`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/static/css/sidebar.css frontend/static/css/app.css
git commit -m "feat: topbar linha única laranja + footer flat"
```

---

### Task 3: Flat Buttons (Primary Laranja Só CTA + Secundário Azul A)

**Files:**
- Modify: `frontend/static/css/app.css:105-176` (buttons)
- Test: grep buttons

**Interfaces:**
- Consumes: tokens globais
- Produces: botões que aparecem em landing/login que Task 4 verifica

- [ ] **Step 1: Teste botão com shadow pesado (deve FAIL depois)**

```bash
grep -q "box-shadow: 0 2px 0 var(--orange-700)" frontend/static/css/app.css && echo "FAIL shadow pesado existe" || echo "PASS flat"
```

- [ ] **Step 2: Run — deve FAIL antes**

Run: `grep -c "box-shadow: 0 2px 0" frontend/static/css/app.css`
Expected: 2 (primary e secondary)

- [ ] **Step 3: Implementar botões flat**

Em `app.css:106-176` substituir:

```css
.btn {
    display: inline-flex; align-items: center; gap: 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 14.5px;
    padding: 11px 22px;
    transition: background .15s, border-color .15s, color .15s;
    border: 2px solid transparent;
    line-height: 1.2;
}
.btn:active { transform: none; }
.btn-sm { padding: 8px 16px; font-size: 13px; }
.btn-lg { padding: 14px 28px; font-size: 15.5px; }

/* Primário = laranja SENAI (única CTA por tela) — flat */
.btn-primary {
    background-color: var(--orange-500) !important;
    border-color: var(--orange-500) !important;
    color: #fff !important;
    box-shadow: none !important;
}
.btn-primary:hover, .btn-primary:focus {
    background-color: var(--orange-600) !important;
    border-color: var(--orange-600) !important;
    color: #fff !important;
    box-shadow: none !important;
}

/* Secundário = azul institucional sólido (híbrido A) — flat */
.btn-secondary {
    background-color: var(--blue-700) !important;
    border-color: var(--blue-700) !important;
    color: #fff !important;
    box-shadow: none !important;
}
.btn-secondary:hover, .btn-secondary:focus {
    background-color: var(--blue-800) !important;
    border-color: var(--blue-800) !important;
}
```

Manter `.btn-outline-primary`, `.btn-outline-secondary`, `.btn-ghost` mas remover shadows se houver; garantir `box-shadow:none`.

- [ ] **Step 4: Verify**

Run: `grep -q "box-shadow: 0 2px 0" frontend/static/css/app.css && echo FAIL || echo PASS`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/static/css/app.css
git commit -m "feat: botoes flat — primary laranja sem shadow, secondary azul sólido A"
```

---

### Task 4: Cards/Tabelas/Forms Flat (remover gradientes)

**Files:**
- Modify: `frontend/static/css/app.css:78-103` (cards)
- Modify: `frontend/static/css/app.css:195-210` (tables)
- Test: grep gradientes

**Interfaces:**
- Consumes: sidebar/topbar/buttons de Tasks 1-3
- Produces: página completa flat

- [ ] **Step 1: Teste gradientes em cards**

```bash
grep -q "linear-gradient.*card-dark\|linear-gradient.*thumb" frontend/static/css/app.css && echo "FAIL gradiente existe" || echo "PASS sem gradiente"
```

- [ ] **Step 2: Run — deve FAIL antes**

Run: `grep -c "linear-gradient" frontend/static/css/app.css`
Expected: 2 (card-dark e thumb)

- [ ] **Step 3: Implementar cards flat**

Em `app.css:78-103`:

```css
.card {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.15s ease;
    overflow: hidden;
}
.card:hover { box-shadow: var(--shadow-sm); }
.card-header {
    background-color: transparent;
    border-bottom: 1px solid var(--border-color);
    border-radius: var(--radius-lg) var(--radius-lg) 0 0 !important;
    padding: 1rem 1.25rem;
}
.card-body { padding: 1.25rem; }
.card-footer { background-color: transparent; border-top: 1px solid var(--border-color); }
.card-dark { background: #0E2C63; color: #fff; border: none; }
.card-dark .text-muted { color: rgba(255,255,255,.75) !important; }

/* Cards DS extras — flat */
.card-curso { width: 100%; background:#fff; border:1px solid var(--n-200); border-radius:var(--radius-lg); overflow:hidden; box-shadow:var(--shadow-sm); }
.card-curso:hover{ box-shadow:var(--shadow-sm); transform:none; }
.card-curso .thumb{ height:140px; background:var(--blue-100); position:relative; }
.card-curso .thumb .tag-pill{ position:absolute; top:12px; left:12px; }
```

Tabelas/forms já flat — apenas garantir sem gradiente, manter `app.css:195-231` existente.

- [ ] **Step 4: Verify**

Run: `grep -q "linear-gradient" frontend/static/css/app.css && echo FAIL || echo PASS`
Expected: PASS (zero ocorrências)

- [ ] **Step 5: Commit**

```bash
git add frontend/static/css/app.css
git commit -m "feat: cards/tabelas flat sem gradientes"
```

---

### Task 5: Collectstatic + Restart + Graphify Verify

**Files:**
- Run: `docker compose exec web python backend/manage.py collectstatic --noinput --clear`
- Run: `docker compose restart web`
- Run: `graphify update .`

**Interfaces:**
- Consumes: todas Tasks 1-4
- Produces: artefatos coletados e graph atualizado

- [ ] **Step 1: Limpar pycache e collectstatic**

```bash
docker compose exec web python -c "import shutil,pathlib; [shutil.rmtree(str(p),ignore_errors=True) for p in pathlib.Path('/app').rglob('__pycache__')]; print('pycache cleared')"
docker compose exec web python backend/manage.py collectstatic --noinput --clear
```

- [ ] **Step 2: Verificar staticfiles**

```bash
docker compose exec web sh -c "ls -la /app/staticfiles/css/app.css /app/staticfiles/css/sidebar.css /app/staticfiles/css/fonts-senai.css 2>&1 | head -n 20"
docker compose exec web sh -c "grep -q 'linear-gradient' /app/staticfiles/css/app.css && echo FAIL || echo PASS; grep -q 'height: 22px' /app/staticfiles/css/sidebar.css && echo PASS || echo FAIL"
```
Expected: PASS + PASS, arquivos com timestamp novo

- [ ] **Step 3: Restart web**

```bash
docker compose restart web
docker compose ps
docker compose logs web --tail 10
```
Expected: web Up, logs `Watching for file changes`, `No migrations to apply`

- [ ] **Step 4: Graphify update**

```bash
graphify update .
```
Expected: `959 nodes, 1825 edges` atualizado, sem erro

- [ ] **Step 5: Commit se houver mudanças em graphify-out (opcional)**

```bash
git add graphify-out/GRAPH_REPORT.md graphify-out/graph.json 2>&1 || echo "no graph changes to commit"
git status --short
```
Se houver diff, commit; senão, apenas log.

