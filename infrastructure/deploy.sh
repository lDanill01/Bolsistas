#!/bin/bash
# deploy.sh — Build, push e deploy do stack Bolsas no Docker Swarm
#
# Pré-requisitos:
#   1. Docker Swarm inicializado:  docker swarm init
#   2. Network overlay "public":   docker network create --driver=overlay --attachable public
#   3. Registry acessível (ex: localhost:5000)
#   4. .env.prod configurado com DOMAIN, ACME_EMAIL, REGISTRY
#   5. .secrets/ preenchido com valores reais
#
# Uso:
#   ./deploy.sh              # deploy com tag latest
#   ./deploy.sh v1.2.3       # deploy com tag específica

set -euo pipefail

TAG="${1:-latest}"
REGISTRY="${REGISTRY:-localhost:5000}"
IMAGE="${REGISTRY}/bolsas:${TAG}"
STACK="bolsas"
COMPOSE_FILE="docker-compose.yml"
PROD_FILE="docker-compose.prod.yml"

echo ">>> Buildando imagem ${IMAGE}..."
docker build -t "${IMAGE}" .

echo ">>> Push para registry ${REGISTRY}..."
docker push "${IMAGE}"

echo ">>> Deploy stack ${STACK}..."
docker stack deploy \
  -c "${COMPOSE_FILE}" \
  -c "${PROD_FILE}" \
  --with-registry-auth \
  "${STACK}"

echo ""
echo ">>> Deploy concluido!"
echo ">>> Aguardando servicos iniciarem..."
sleep 5
docker stack services "${STACK}"

echo ""
echo ">>> Logs (Ctrl+C para sair):"
docker service logs -f "${STACK}_web"
