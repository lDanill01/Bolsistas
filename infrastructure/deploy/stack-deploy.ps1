# Deploy do stack Docker Swarm de producao (PowerShell).
# Requisitos: Docker em modo Swarm, registry configurado e acessivel.

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $PSScriptRoot
$StackName = "bolsas"

$EnvFile = Join-Path $ProjectDir ".env.prod"
if (-not (Test-Path $EnvFile)) {
    Write-Error ".env.prod nao encontrado em $ProjectDir"
}

# Carrega variaveis nao-secretas
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#\s=]+)\s*=\s*(.*)\s*$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

$SecretsDir = Join-Path $ProjectDir ".secrets"
New-Item -ItemType Directory -Force -Path $SecretsDir | Out-Null

$RequiredSecrets = @(
    "secret_key",
    "db_password",
    "groq_api_key",
    "rabbitmq_password",
    "cf_dns_api_token"
)

# O segredo nao utilizado pelo IA_PROVIDER atual pode conter um placeholder.

$Missing = $false
foreach ($secret in $RequiredSecrets) {
    $file = Join-Path $SecretsDir "$secret.txt"
    if (-not (Test-Path $file) -or (Get-Item $file).Length -eq 0) {
        Write-Host "ERRO: segredo ausente ou vazio: $file" -ForegroundColor Red
        $Missing = $true
    }
}

if ($Missing) {
    Write-Host ""
    Write-Host "Crie os arquivos de segredo em $SecretsDir"
    exit 1
}

$SwarmState = docker info --format '{{.Swarm.LocalNodeState}}'
if ($SwarmState -notmatch "active") {
    Write-Error "Docker nao esta em modo Swarm. Inicie com: docker swarm init"
}

foreach ($secret in $RequiredSecrets) {
    $file = Join-Path $SecretsDir "$secret.txt"
    $exists = docker secret ls --format '{{.Name}}' | Select-String -Pattern "^$secret$" -Quiet
    if ($exists) {
        Write-Host "Segredo ja existe: $secret (mantido)"
    } else {
        Write-Host "Criando segredo: $secret"
        docker secret create $secret $file
    }
}

$Registry = if ($env:REGISTRY) { $env:REGISTRY } else { "localhost:5000" }
$Tag = if ($env:TAG) { $env:TAG } else { "latest" }
$Image = "$Registry/bolsas:$Tag"

Write-Host ""
Write-Host "Build da imagem: $Image"
docker build -t $Image $ProjectDir

Write-Host "Push da imagem: $Image"
docker push $Image

Write-Host ""
Write-Host "Deploy do stack: $StackName"
docker stack deploy -c "$ProjectDir\docker-compose.prod.yml" --env-file $EnvFile $StackName

Write-Host ""
Write-Host "Status dos servicos:"
docker stack ps $StackName --format 'table {{.Name}}\t{{.CurrentState}}\t{{.Error}}'

Write-Host ""
Write-Host "Deploy concluido."
