#!/usr/bin/env bash
set -euo pipefail

# Deploy do stack Docker Swarm de producao.
# Requisitos: Docker em modo Swarm, registry configurado e acessivel.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
STACK_NAME="bolsas"

if [ ! -f "$PROJECT_DIR/.env.prod" ]; then
    echo "ERRO: .env.prod nao encontrado em $PROJECT_DIR"
    echo "Copie .env.prod.example para .env.prod e preencha os valores."
    exit 1
fi

# Carrega variaveis nao-secretas
set -a
# shellcheck source=/dev/null
source "$PROJECT_DIR/.env.prod"
set +a

SECRETS_DIR="$PROJECT_DIR/.secrets"
mkdir -p "$SECRETS_DIR"

REQUIRED_SECRETS=(
    "secret_key"
    "db_password"
    "groq_api_key"
    "rabbitmq_password"
    "cf_dns_api_token"
)

# O segredo nao utilizado pelo IA_PROVIDER atual pode conter um placeholder.

MISSING=0
for secret in "${REQUIRED_SECRETS[@]}"; do
    file="$SECRETS_DIR/${secret}.txt"
    if [ ! -f "$file" ] || [ ! -s "$file" ]; then
        echo "ERRO: segredo ausente ou vazio: $file"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "Crie os arquivos de segredo em $SECRETS_DIR/"
    echo "Exemplo:"
    echo "  echo -n 'minha-chave' > $SECRETS_DIR/secret_key.txt"
    exit 1
fi

if ! docker info --format '{{.Swarm.LocalNodeState}}' | grep -q "active"; then
    echo "ERRO: Docker nao esta em modo Swarm. Inicie com: docker swarm init"
    exit 1
fi

# Cria os Docker Secrets (ignora se ja existirem)
for secret in "${REQUIRED_SECRETS[@]}"; do
    file="$SECRETS_DIR/${secret}.txt"
    if docker secret ls --format '{{.Name}}' | grep -qx "${secret}"; then
        echo "Segredo ja existe: $secret (mantido)"
    else
        echo "Criando segredo: $secret"
        docker secret create "$secret" "$file"
    fi
done

# Build e push da imagem
REGISTRY="${REGISTRY:-localhost:5000}"
TAG="${TAG:-latest}"
IMAGE="${REGISTRY}/bolsas:${TAG}"

echo ""
echo "Build da imagem: $IMAGE"
docker build -t "$IMAGE" "$PROJECT_DIR"

echo "Push da imagem: $IMAGE"
docker push "$IMAGE"

# Deploy do stack
echo ""
echo "Deploy do stack: $STACK_NAME"
docker stack deploy -c "$PROJECT_DIR/docker-compose.prod.yml" --env-file "$PROJECT_DIR/.env.prod" "$STACK_NAME"

echo ""
echo "Status dos servicos:"
docker stack ps "$STACK_NAME" --format 'table {{.Name}}\t{{.CurrentState}}\t{{.Error}}' || true

echo ""
echo "Deploy concluido."
