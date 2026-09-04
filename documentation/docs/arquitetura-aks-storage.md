# Arquitetura futura AKS e Azure Blob Storage

Status: aprovada para implementacao futura. O ambiente atual em Docker Compose
e o deploy existente em Azure Container Apps (ACA) permanecem inalterados.

## Objetivo

Disponibilizar uma arquitetura de producao opcional para AKS, com arquivos de
media privados no Azure Blob Storage e credenciais sem chaves dentro de codigo,
imagens ou manifests versionados.

## Limites

- O pacote AKS nao altera `infrastructure/azure-pipelines.yml`, que continua
  publicando em ACA.
- PostgreSQL, Redis e RabbitMQ sao dependencias externas. O pacote nao cria
  StatefulSets, PersistentVolumes ou bancos dentro do cluster.
- Media continua privada e e entregue pela rota Django `media/<path>`, nunca
  diretamente por um container Blob publico.
- Nao armazenar connection string, account key, senha ou certificado no Git.

## Componentes

```
Internet -> NGINX Ingress -> Service web -> Deployment web (Django/Gunicorn)
                                      |-> Deployment celery worker
                                      |-> Deployment celery beat (1 replica)
                                      |-> Job de migracao, executado antes do rollout

Todos os workloads -> ServiceAccount AKS -> Workload Identity
                                             |-> Azure Blob Storage (media)
                                             |-> Key Vault CSI (segredos de runtime)

Workloads -> PostgreSQL externo / Redis externo / RabbitMQ externo
```

O NGINX Ingress recebe o trafego HTTPS. O cert-manager emite e renova o
certificado do host configurado. O Service web e interno ao cluster e somente
o Ingress e exposto.

## Organizacao dos manifests

Quando o pacote for implementado, usar Kustomize nesta estrutura:

```
k8s/
  base/
    namespace.yaml
    serviceaccount.yaml
    configmap.yaml
    secret-provider-class.yaml
    web-deployment.yaml
    web-service.yaml
    celery-deployment.yaml
    beat-deployment.yaml
    migration-job.yaml
    hpa-web.yaml
    pdb-web.yaml
    network-policy.yaml
    kustomization.yaml
  overlays/aks-production/
    ingress.yaml
    certificate.yaml
    kustomization.yaml
    patches/
```

O overlay deve conter valores especificos de producao, como host, referencias
de imagem, limites de recursos, identificadores Azure e endpoints externos.
Nunca duplicar secret values no overlay.

## Identidade, segredos e storage

1. O cluster AKS precisa ter OIDC, Workload Identity e o add-on Azure Key Vault
   Secrets Store CSI habilitados.
2. Criar uma user-assigned managed identity para o namespace/workloads.
3. Criar a federated identity credential vinculando essa identidade ao
   `ServiceAccount` do namespace `bolsas-production`.
4. Conceder a essa identidade:
   - `Storage Blob Data Contributor` no escopo do container de media ou da
     storage account;
   - `Key Vault Secrets User` no Key Vault.
5. O `SecretProviderClass` le os segredos do Key Vault e os sincroniza para um
   Secret Kubernetes de runtime, consumido com `envFrom` por web, worker, beat
   e job de migracao.
6. O Blob container de media deve existir antes do deploy. Ele e privado.

Segredos do Key Vault:

- `SECRET_KEY`
- `DB_PASSWORD`
- `RABBITMQ_PASSWORD`
- `GROQ_API_KEY`
- `EMAIL_HOST_PASSWORD`

Configuracoes nao secretas do ConfigMap:

- `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- configuracao de PostgreSQL, Redis e RabbitMQ externos
- `AZURE_ACCOUNT_NAME`, `AZURE_CONTAINER`, `AZURE_URL_EXPIRATION_SECS`
- configuracao de e-mail e IA que nao contenha segredo

O projeto deve adicionar `azure-identity` a `requirements.txt`. Em
`backend/config/settings.py`, quando `AZURE_ACCOUNT_NAME` e
`AZURE_CONTAINER` estiverem definidos e nao houver connection string/account
key, configurar `storages.backends.azure_storage.AzureStorage` com
`DefaultAzureCredential()` em `STORAGES['default']['OPTIONS']['token_credential']`.
O webhook de Workload Identity injeta as variaveis federadas esperadas pelo
`DefaultAzureCredential`; nao criar fallback com chave no AKS.

## Operacao dos workloads

- **web**: Deployment com no minimo 2 replicas, Service interno, readiness e
  liveness em `/health/`, requests/limits declarados, PDB e HPA por CPU/memoria.
- **celery worker**: Deployment independente com 2 replicas iniciais, mesmos
  segredos e configuracoes do web. Escalonamento por fila (KEDA) fica fora do
  primeiro pacote; HPA pode ser adicionado quando houver metrica de fila.
- **celery beat**: uma replica e estrategia `Recreate`, prevenindo agendas
  duplicadas em rollout.
- **migration job**: Job separado, sem execucao automatica por um apply comum.
  O runbook executa, espera completar e so entao atualiza os Deployments.
- **NetworkPolicy**: permitir entrada no web apenas a partir do Ingress. Nao
  aplicar default-deny de egress ate que os IPs/FQDNs de todas as dependencias
  externas estejam definidos e testados.

## Runbook de adocao futura

1. Provisionar AKS, ACR, Key Vault, Blob container e servicos externos.
2. Habilitar Workload Identity, OIDC, Key Vault CSI, NGINX Ingress e cert-manager.
3. Criar identidade, federated credential e role assignments descritos acima.
4. Popular o Key Vault e preencher somente identificadores/enderecos no overlay.
5. Validar com `kustomize build k8s/overlays/aks-production` e
   `kubectl diff -k k8s/overlays/aks-production`.
6. Executar o Job de migracao e aguardar conclusao.
7. Aplicar o overlay, acompanhar rollout de web/worker/beat e verificar
   `/health/` por HTTPS.
8. Testar upload, leitura protegida e exclusao de um arquivo de media. Confirmar
   que o blob foi criado no container privado e que nao ha URL publica.

## Instrucoes obrigatorias para agentes de IA

Ao criar ou alterar a arquitetura AKS, o agente deve:

1. Ler este documento antes de alterar `k8s/`, `backend/config/settings.py`,
   `requirements.txt`, `.env*.example` ou configuracoes de deploy.
2. Preservar Docker Compose, Docker Swarm e Azure Container Apps; nao trocar o
   pipeline ACA por AKS sem pedido explicito.
3. Usar Kustomize com `base` e `overlays/aks-production`; manter nomes,
   namespace e seletores consistentes.
4. Usar Workload Identity para Blob e Key Vault CSI para segredos. Nunca gravar
   segredo, connection string, account key, token SAS ou certificado em YAML,
   `.env.example`, documentacao ou logs.
5. Manter Blob privado e acesso de usuario passando pelo Django/default_storage.
6. Executar `kustomize build`, validacao de schema disponivel e testes Django
   pertinentes antes de declarar a alteracao concluida.
7. Documentar todo novo parametro nao secreto no ConfigMap e todo segredo no
   inventario de Key Vault deste documento.

## Criterios de aceite da implementacao futura

- O overlay gera manifests validos sem segredos embutidos.
- Pods autenticam no Blob por Workload Identity e o upload funciona sem
  `AZURE_CONNECTION_STRING` ou `AZURE_ACCOUNT_KEY`.
- Os segredos sao obtidos pelo Key Vault CSI e indisponibilidade do Key Vault
  impede o pod de iniciar sem vazar valores nos logs.
- O Ingress atende HTTPS com certificado valido; probes, PDB e HPA do web estao
  ativos.
- Migrations ocorrem antes do rollout e Celery beat mantem uma unica instancia.

## Referencias

- https://django-storages.readthedocs.io/en/stable/backends/azure.html
- https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview
- https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver
