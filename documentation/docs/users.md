# Usuários do Sistema

> Os usuários devem ser criados via admin Django ou pelo comando `python manage.py createsuperuser`.

---

## Permissões por grupo

| Grupo | Permissões |
|---|---|
| **Superuser** | Acesso total: admin Django, gerenciar usuários, criar/editais, avaliar, aprovar |
| **Manager** | Criar e gerenciar editais, aprovar usuários, avaliar candidatos, visualizar painéis |
| **ExecuteUser** | Acesso operacional (execução de tarefas do sistema) |
| **ViewUser** | Visualizar editais abertos, candidatar-se, acompanhar status |

---

## Recuperação de senha

Caso esqueça a senha, acesse a tela de login e clique em **"Esqueci minha senha"**.  
Em ambiente de desenvolvimento, o link de redefinição aparece nos logs do container:

```powershell
docker compose logs web
```

Em produção, o email é enviado via SMTP.

---

## Comandos dos containers Docker

### Subir todos os containers (dev)

```powershell
# Na raiz do projeto (onde está o docker-compose.yml)
docker compose up -d
```

A aplicação ficará disponível em:
- **http://localhost** (via Traefik, porta 80)
- **http://localhost:8000** (direto no Django, porta 8000)
- RabbitMQ Management: http://localhost:15672 (guest/guest)

### Parar todos os containers

```powershell
docker compose down
```

### Parar sem perder dados (volumes preservados)

```powershell
docker compose stop
```

### Reiniciar um container específico

```powershell
# Ex: após editar .env ou código Python que não é auto-recarregado
docker compose restart web
docker compose restart celery
```

### Ver logs de um container

```powershell
docker compose logs web        # logs do Django
docker compose logs celery     # logs das tarefas assíncronas
docker compose logs db         # logs do PostgreSQL

# Seguir em tempo real
docker compose logs -f web
```

### Executar comandos Django dentro do container

```powershell
# Shell do Django
docker compose exec web python manage.py shell

# Aplicar migrations
docker compose exec web python manage.py migrate

# System check
docker compose exec web python manage.py check
```

### Recriar containers (após mudanças no Dockerfile)

```powershell
docker compose up -d --build
```

### Apagar tudo (containers + volumes + dados)

```powershell
docker compose down -v
```

### Ver status dos containers

```powershell
docker compose ps
```

---

## Serviços

| Container | Descrição | Porta |
|---|---|---|
| `db` | PostgreSQL 16 | (interna) |
| `redis` | Cache e backend Celery | (interna) |
| `rabbitmq` | Message broker Celery | 15672 (management) |
| `web` | Django runserver | 8000 |
| `celery` | Worker de tarefas assíncronas | (interna) |
| `celery-beat` | Agendador de tarefas periódicas | (interna) |
| `traefik` | Proxy reverso | 80 (app), 8080 (dashboard) |
